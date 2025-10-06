"""
Discord Voice Bot - Main bot class
Handles voice channel creation and management
"""
import discord
from discord.ext import commands
import asyncio
from typing import Optional
import signal
import sys
import os

from .config import (
    MAIN_CHANNEL_ID, 
    MAIN_CATEGORY_ID, 
    COMMAND_PREFIX, 
    CHANNEL_MONITOR_INTERVAL,
    setup_logging
)
from .utils import (
    send_control_message,
    cleanup_control_message,
    create_channel_name,
    create_channel_overwrites
)

logger = setup_logging()


class VoiceBot(commands.Bot):
    """Main bot class for managing voice channels"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.voice_states = True
        intents.guilds = True
        intents.message_content = True  # Fix for commands to work properly
        
        super().__init__(
            command_prefix=COMMAND_PREFIX,
            intents=intents,
            help_command=None
        )
        
        # Track created channels to prevent memory leaks
        self.created_channels = {}
        
    async def setup_hook(self):
        """Called when the bot is starting up"""
        logger.info("Bot is starting up...")
        
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
                
            # User left a temporary channel - only clean up if the channel is now empty
            if before.channel and before.channel.id in self.created_channels:
                # Check if the user actually left the channel (not just switching between channels)
                user_left_channel = not after.channel or after.channel.id != before.channel.id
                if user_left_channel:
                    # User left the temporary channel, check if it's empty
                    if self._is_channel_empty(before.channel):
                        await self._cleanup_empty_channel(before.channel)
                
        except Exception as e:
            logger.error(f"Error in voice_state_update: {e}", exc_info=True)
            
    def _is_channel_empty(self, channel: discord.VoiceChannel) -> bool:
        """Check if a voice channel is empty"""
        return len(channel.members) == 0
            
    async def _create_temp_channel(self, member: discord.Member, guild: discord.Guild):
        """Create a temporary voice channel for the user"""
        try:
            category = discord.utils.get(guild.categories, id=MAIN_CATEGORY_ID)
            if not category:
                logger.error(f"Category with ID {MAIN_CATEGORY_ID} not found in guild {guild.name}")
                return
                
            # Create channel with better naming and permissions
            channel_name = create_channel_name(member)
            temp_channel = await guild.create_voice_channel(
                name=channel_name,
                category=category,
                user_limit=0,  # 0 = unlimited users
                overwrites=create_channel_overwrites(member)
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
            
            # Send control message to the voice channel
            control_message_id = await send_control_message(temp_channel, member)
            if control_message_id:
                self.created_channels[temp_channel.id]['control_message'] = control_message_id
            
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
                await asyncio.sleep(CHANNEL_MONITOR_INTERVAL)
                
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
                    
                if self._is_channel_empty(channel):
                    await self._cleanup_empty_channel(channel)
                    break
                    
        except Exception as e:
            logger.error(f"Error monitoring channel {channel.name}: {e}", exc_info=True)
            
    async def _cleanup_empty_channel(self, channel: discord.VoiceChannel):
        """Delete empty temporary channel"""
        try:
            if channel.id in self.created_channels:
                # Double-check that the channel is actually empty before deleting
                if not self._is_channel_empty(channel):
                    logger.warning(f"Attempted to delete non-empty channel '{channel.name}', skipping")
                    return
                    
                channel_info = self.created_channels[channel.id]
                
                # Try to delete the control message before deleting the channel
                if 'control_message' in channel_info:
                    await cleanup_control_message(channel, channel_info['control_message'])
                
                await channel.delete()
                self.created_channels.pop(channel.id)
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
                # Get fresh channel object
                channel = self.get_channel(channel_id)
                if channel is None:
                    # Channel already deleted, remove from tracking
                    self.created_channels.pop(channel_id, None)
                    continue
                    
                if self._is_channel_empty(channel):
                    await self._cleanup_empty_channel(channel)
                    cleaned += 1
            except Exception as e:
                logger.warning(f"Error during cleanup of channel {channel_id}: {e}")
                continue
                
        await ctx.send(f"🧹 Cleaned up {cleaned} empty channels")
