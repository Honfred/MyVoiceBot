"""
Configuration module for Discord Voice Bot
"""
import os
import logging
import sys

# Bot configuration
MAIN_CHANNEL_ID = int(os.environ.get('MAIN_CHANNEL_ID', '901007391477350440'))
MAIN_CATEGORY_ID = int(os.environ.get('MAIN_CATEGORY_ID', '901007309533245490'))
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

# Bot settings
COMMAND_PREFIX = '!'
CHANNEL_MONITOR_INTERVAL = 5  # seconds
VIEW_TIMEOUT = 300  # 5 minutes
CHANNEL_DELETE_DELAY = 3  # seconds


def setup_logging():
    """Setup logging configuration"""
    handlers = [logging.StreamHandler(sys.stdout)]
    
    # Try to add file handler if possible
    try:
        os.makedirs('logs', exist_ok=True)
        handlers.append(logging.FileHandler('logs/bot.log', encoding='utf-8'))
    except (PermissionError, OSError):
        # If can't write to file, just use console logging
        pass
    
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )
    
    return logging.getLogger(__name__)
