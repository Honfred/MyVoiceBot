import discord
from discord.ext import commands
import logging
import os
import asyncio
from typing import Optional
import signal
import sys

# Configuration
MAIN_CHANNEL_ID = int(os.environ.get('MAIN_CHANNEL_ID', '901007391477350440'))
MAIN_CATEGORY_ID = int(os.environ.get('MAIN_CATEGORY_ID', '901007309533245490'))
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

# Enhanced logging setup
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
logger = logging.getLogger(__name__)


class VoiceBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.voice_states = True
        intents.guilds = True
        intents.message_content = True  # Fix for commands to work properly
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None
        )
        
        # Track created channels to prevent memory leaks
        self.created_channels = {}
        
    async def setup_hook(self):
        """Called when the bot is starting up"""
        logger.info(f"Bot is starting up...")
        
    async def on_ready(self):
        """Called when the bot has connected to Discord"""
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Bot is in {len(self.guilds)} guilds')
        
        # Set bot status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name="голосовые каналы"
            )
        )
        
    async def on_error(self, event, *args, **kwargs):
        """Handle errors"""
        logger.error(f'Error in {event}', exc_info=True)
        
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """Handle voice state updates"""
        try:
            # User joined the main channel
            if after.channel and after.channel.id == MAIN_CHANNEL_ID:
                await self._create_temp_channel(member, after.channel.guild)
                
            # User left a temporary channel
            if before.channel and before.channel.id in self.created_channels:
                await self._cleanup_empty_channel(before.channel)
                
        except Exception as e:
            logger.error(f"Error in voice_state_update: {e}", exc_info=True)
            
    async def _create_temp_channel(self, member: discord.Member, guild: discord.Guild):
        """Create a temporary voice channel for the user"""
        try:
            category = discord.utils.get(guild.categories, id=MAIN_CATEGORY_ID)
            if not category:
                logger.error(f"Category with ID {MAIN_CATEGORY_ID} not found in guild {guild.name}")
                return
                
            # Create channel with better naming and permissions
            channel_name = f"🔊 {member.display_name}"
            temp_channel = await guild.create_voice_channel(
                name=channel_name,
                category=category,
                overwrites={
                    member: discord.PermissionOverwrite(
                        manage_channels=True,
                        manage_permissions=True,
                        move_members=True
                    )
                }
            )
            
            # Track the channel
            self.created_channels[temp_channel.id] = {
                'channel': temp_channel,
                'creator': member.id,
                'created_at': discord.utils.utcnow()
            }
            
            # Move user to the new channel
            await member.move_to(temp_channel)
            logger.info(f"Created temporary channel '{channel_name}' for {member.display_name}")
            
            # Start monitoring the channel
            asyncio.create_task(self._monitor_channel(temp_channel))
            
        except discord.Forbidden:
            logger.error(f"Missing permissions to create voice channel in {guild.name}")
        except Exception as e:
            logger.error(f"Error creating temp channel: {e}", exc_info=True)
            
    async def _monitor_channel(self, channel: discord.VoiceChannel):
        """Monitor a temporary channel and delete when empty"""
        try:
            while channel.id in self.created_channels:
                await asyncio.sleep(5)  # Check every 5 seconds
                
                # Refresh channel state
                try:
                    # Get fresh channel object from guild
                    fresh_channel = self.get_channel(channel.id)
                    if fresh_channel is None:
                        # Channel was already deleted
                        self.created_channels.pop(channel.id, None)
                        break
                    channel = fresh_channel
                except discord.NotFound:
                    # Channel was already deleted
                    self.created_channels.pop(channel.id, None)
                    break
                    
                if len(channel.members) == 0:
                    await self._cleanup_empty_channel(channel)
                    break
                    
        except Exception as e:
            logger.error(f"Error monitoring channel {channel.name}: {e}", exc_info=True)
            
    async def _cleanup_empty_channel(self, channel: discord.VoiceChannel):
        """Delete empty temporary channel"""
        try:
            if channel.id in self.created_channels:
                await channel.delete()
                channel_info = self.created_channels.pop(channel.id)
                logger.info(f"Deleted empty temporary channel '{channel.name}'")
                
        except discord.NotFound:
            # Channel already deleted
            self.created_channels.pop(channel.id, None)
        except discord.Forbidden:
            logger.error(f"Missing permissions to delete channel {channel.name}")
        except Exception as e:
            logger.error(f"Error deleting channel {channel.name}: {e}", exc_info=True)
            
    @commands.command(name='stats')
    @commands.has_permissions(administrator=True)
    async def stats(self, ctx):
        """Show bot statistics"""
        embed = discord.Embed(
            title="📊 Bot Statistics",
            color=0x00ff00,
            timestamp=discord.utils.utcnow()
        )
        
        embed.add_field(
            name="Active Temporary Channels",
            value=len(self.created_channels),
            inline=True
        )
        
        embed.add_field(
            name="Guilds",
            value=len(self.guilds),
            inline=True
        )
        
        embed.add_field(
            name="Latency",
            value=f"{round(self.latency * 1000)}ms",
            inline=True
        )
        
        await ctx.send(embed=embed)
        
    @commands.command(name='cleanup')
    @commands.has_permissions(administrator=True)
    async def cleanup_channels(self, ctx):
        """Manually cleanup empty temporary channels"""
        cleaned = 0
        for channel_id, channel_info in list(self.created_channels.items()):
            try:
                channel = channel_info['channel']
                channel = await channel.fetch()
                if len(channel.members) == 0:
                    await self._cleanup_empty_channel(channel)
                    cleaned += 1
            except:
                continue
                
        await ctx.send(f"🧹 Cleaned up {cleaned} empty channels")


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
        return
        
    bot = VoiceBot()
    setup_signal_handlers(bot)
    
    try:
        async with bot:
            await bot.start(token)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}", exc_info=True)
    finally:
        logger.info("Bot shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
