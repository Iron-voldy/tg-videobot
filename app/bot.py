from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, ContextTypes, filters
)
import logging
from app.database import get_session, User, Video
from app.api import generate_video
from app.helpers import is_safe_prompt, format_welcome_message
from app.config import TELEGRAM_TOKEN, FREE_GENERATIONS, STAR_COST

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command"""
    user = update.effective_user
    session = get_session()
    
    # Check if the user exists
    db_user = session.query(User).filter(User.user_id == user.id).first()
    
    # Extract referral code if present
    referral_code = None
    if context.args and len(context.args) > 0:
        referral_code = context.args[0]
    
    if not db_user:
        # Create new user
        db_user = User(user.id, user.username)
        session.add(db_user)
        
        # Process referral if exists
        if referral_code:
            referrer = session.query(User).filter(User.referral_code == referral_code).first()
            if referrer and referrer.user_id != user.id:  # Prevent self-referral
                db_user.referred_by = referral_code
                referrer.free_generations += 1
                
                # Notify referrer
                try:
                    await context.bot.send_message(
                        chat_id=referrer.user_id,
                        text=f"🎉 Someone used your referral code! You've earned 1 free video generation."
                    )
                except Exception as e:
                    logger.error(f"Failed to notify referrer: {e}")
        
        session.commit()
        welcome_message = format_welcome_message(db_user.referral_code, db_user.free_generations)
        await update.message.reply_text(welcome_message)
    else:
        # Existing user
        welcome_message = format_welcome_message(db_user.referral_code, db_user.free_generations)
        await update.message.reply_text(welcome_message)
    
    session.close()

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /balance command"""
    user = update.effective_user
    session = get_session()
    
    db_user = session.query(User).filter(User.user_id == user.id).first()
    if db_user:
        message = (
            f"🎬 Your Balance:\n\n"
            f"Free generations: {db_user.free_generations}\n"
            f"Stars: {db_user.stars}\n\n"
            f"Your referral code: {db_user.referral_code}\n"
            f"Share it with friends to earn free generations!"
        )
        await update.message.reply_text(message)
    else:
        await update.message.reply_text("Please use /start to register first.")
    
    session.close()

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /buy command"""
    keyboard = [
        [
            InlineKeyboardButton("1 Star = 1 Video", callback_data="buy_1"),
            InlineKeyboardButton("5 Stars = 5 Videos", callback_data="buy_5")
        ],
        [
            InlineKeyboardButton("10 Stars = 10 Videos", callback_data="buy_10")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "💰 Buy more video generations using Telegram stars.\n"
        "Choose an option:",
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /help command"""
    help_text = (
        "🎬 *AI Video Generator Bot Help* 🎬\n\n"
        "*How to use:*\n"
        "1. Simply send me a text prompt like 'sunset over mountains'\n"
        "2. I'll generate a 30-second video based on your prompt\n"
        "3. Each user gets 3 free generations\n\n"
        "*Commands:*\n"
        "/start - Start the bot and get your referral code\n"
        "/balance - Check your free generations and stars\n"
        "/buy - Purchase more generations using Telegram stars\n"
        "/help - Show this help message\n\n"
        "*Referral System:*\n"
        "Share your referral code with friends. When they start the bot using your code, "
        "you'll earn 1 free generation!\n\n"
        "*Content Policy:*\n"
        "Please keep your prompts appropriate. Explicit, violent, or hateful content is not allowed."
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("buy_"):
        amount = int(query.data.split("_")[1])
        # Here you would implement the actual Telegram payment
        # For now, we'll just show a message
        await query.edit_message_text(
            text=f"To purchase {amount} video generations, please send {amount} stars through Telegram.\n\n"
                 f"This would typically integrate with Telegram's payment system."
        )

async def process_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process text prompts and generate videos"""
    user = update.effective_user
    prompt = update.message.text
    
    # Check if prompt is safe
    if not is_safe_prompt(prompt):
        await update.message.reply_text(
            "⚠️ Sorry, your prompt contains inappropriate content. "
            "Please try a different prompt."
        )
        return
    
    session = get_session()
    db_user = session.query(User).filter(User.user_id == user.id).first()
    
    if not db_user:
        await update.message.reply_text("Please use /start to register first.")
        session.close()
        return
    
    # Check if user has free generations or stars
    if db_user.free_generations > 0:
        # Use free generation
        await update.message.reply_text("🎬 Generating your video... This may take a moment.")
        
        # Generate video
        video_url = generate_video(prompt)
        
        if video_url:
            # Save video to database
            video = Video(
                user_id=user.id,
                prompt=prompt,
                video_url=video_url,
                used_free=True
            )
            session.add(video)
            
            # Decrease free generations
            db_user.free_generations -= 1
            session.commit()
            
            # Send video
            await update.message.reply_text(
                f"🎥 Here's your video based on: '{prompt}'\n\n"
                f"You have {db_user.free_generations} free generations left."
            )
            
            # Send video URL (in a real scenario, you'd download and send the actual video)
            await update.message.reply_text(f"Video URL: {video_url}")
        else:
            await update.message.reply_text(
                "😔 Sorry, I couldn't generate a video. Please try a different prompt."
            )
    elif db_user.stars >= STAR_COST:
        # Use stars
        await update.message.reply_text("🎬 Generating your video using 1 star... This may take a moment.")
        
        # Generate video
        video_url = generate_video(prompt)
        
        if video_url:
            # Save video to database
            video = Video(
                user_id=user.id,
                prompt=prompt,
                video_url=video_url,
                used_stars=STAR_COST
            )
            session.add(video)
            
            # Decrease stars
            db_user.stars -= STAR_COST
            session.commit()
            
            # Send video
            await update.message.reply_text(
                f"🎥 Here's your video based on: '{prompt}'\n\n"
                f"You have {db_user.stars} stars left."
            )
            
            # Send video URL (in a real scenario, you'd download and send the actual video)
            await update.message.reply_text(f"Video URL: {video_url}")
        else:
            await update.message.reply_text(
                "😔 Sorry, I couldn't generate a video. Please try a different prompt."
            )
    else:
        # No free generations or stars
        keyboard = [
            [InlineKeyboardButton("Buy Stars", callback_data="buy_1")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🚫 You've used all your free generations and have no stars.\n\n"
            "Buy stars to generate more videos or invite friends using your referral code to earn free generations.",
            reply_markup=reply_markup
        )
    
    session.close()

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors"""
    logger.warning(f'Update "{update}" caused error "{context.error}"')

def setup_bot():
    """Set up and return the Telegram bot application"""
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("balance", balance))
    application.add_handler(CommandHandler("buy", buy))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_prompt))
    
    # Register error handler
    application.add_error_handler(error_handler)
    
    return application