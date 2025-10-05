"""
Entry point for running the Discord Voice Bot
"""
import asyncio
import os
import signal
import sys
from .bot import VoiceBot
from .config import setup_logging

logger = setup_logging()


def setup_signal_handlers(bot):
    """Setup signal handlers for graceful shutdown"""
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        asyncio.create_task(bot.close())
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


async def main():
    """Main bot function"""
    token = os.environ.get('TOKEN')
    if not token:
        logger.error("TOKEN environment variable is required")
        sys.exit(1)
        
    bot = VoiceBot()
    setup_signal_handlers(bot)
    
    try:
        async with bot:
            await bot.start(token)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Bot shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
