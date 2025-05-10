from app.bot import setup_bot
import logging
import os
from telegram import Update

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Set up and start the bot
    application = setup_bot()
    
    # Start the Bot
    if os.environ.get('ENVIRONMENT') == 'production':
        # Production: use webhook (for Heroku)
        webhook_url = f"https://{os.environ.get('APP_NAME')}.herokuapp.com/{os.environ.get('TELEGRAM_TOKEN')}"
        application.bot.set_webhook(webhook_url)
        
        # Get port from environment variable (for Heroku)
        PORT = int(os.environ.get('PORT', 5000))
        
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=os.environ.get('TELEGRAM_TOKEN'),
            webhook_url=webhook_url
        )
    else:
        # Development: use polling
        logger.info("Starting bot with polling...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    
    logger.info("Bot started")