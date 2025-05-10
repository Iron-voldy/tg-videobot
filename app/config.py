import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot configuration
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
DEEPAI_API_KEY = os.getenv('DEEPAI_API_KEY')

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///bot_database.db')

# Content filter
BLOCKED_WORDS = ["explicit", "nudity", "porn", "violence", "gore", "hate", "racist"]

# Video generation settings
DEFAULT_VIDEO_DURATION = 30  # seconds
FREE_GENERATIONS = 3  # Number of free generations per user
STAR_COST = 1  # Number of stars for one video generation

# DeepAI API endpoints
DEEPAI_VIDEO_API = "https://api.deepai.org/api/text2video"