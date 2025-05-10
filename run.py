from app.bot import setup_bot
import logging
import os

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    logger = logging.getLogger(__name__)
    
    # Get port from environment variable (for Heroku)
    PORT = int(os.environ.get('PORT', 5000))
    
    # Set up and start the bot
    updater = setup_bot()
    
    # Start the Bot
    if os.environ.get('ENVIRONMENT') == 'production':
        # Production: use webhook (for Heroku)
        updater.start_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=os.environ.get('TELEGRAM_TOKEN'),
            webhook_url=f"https://{os.environ.get('APP_NAME')}.herokuapp.com/{os.environ.get('TELEGRAM_TOKEN')}"
        )
    else:
        # Development: use polling
        updater.start_polling()
    
    logger.info("Bot started")
    
    # Run the bot until you press Ctrl-C
    updater.idle()