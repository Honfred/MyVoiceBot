"""
Utility functions for Discord Voice Bot
"""
import discord
import logging
from .views import ChannelControlView

logger = logging.getLogger(__name__)


async def send_control_message(channel: discord.VoiceChannel, creator: discord.Member):
    """Send control message with buttons to the voice channel's text channel"""
    try:
        # Create embed with channel info
        embed = discord.Embed(
            title="🎤 Управление голосовым каналом",
            description=f"Канал: **{channel.name}**\nСоздатель: {creator.mention}",
            color=0x00ff00,
            timestamp=discord.utils.utcnow()
        )
        
        embed.add_field(
            name="📋 Доступные действия:",
            value=(
                "🔒 **Приватный** - сделать канал приватным\n"
                "🔓 **Открытый** - сделать канал открытым\n"
                "👥 **Лимит** - установить лимит пользователей\n"
                "📝 **Переименовать** - изменить название\n"
                "🚫 **Удалить** - удалить канал"
            ),
            inline=False
        )
        
        embed.set_footer(text="Кнопки доступны только создателю канала и администраторам")
        
        # Create view with control buttons
        view = ChannelControlView(channel, creator.id)
        
        # Send the message without pinging anyone
        message = await channel.send(
            embed=embed,
            view=view,
            silent=True  # This prevents notifications
        )
        
        logger.info(f"Control message sent to channel {channel.name}")
        return message.id
        
    except Exception as e:
        logger.error(f"Error sending control message: {e}", exc_info=True)
        return None


async def cleanup_control_message(channel: discord.VoiceChannel, message_id: int):
    """Delete the control message before deleting the channel"""
    try:
        control_message = await channel.fetch_message(message_id)
        await control_message.delete()
        logger.debug(f"Control message deleted for channel {channel.name}")
    except (discord.NotFound, discord.Forbidden):
        pass  # Message already deleted or no permissions
    except Exception as e:
        logger.warning(f"Could not delete control message: {e}")


def create_channel_name(member: discord.Member) -> str:
    """Generate a name for the temporary channel"""
    return f"🔊 {member.display_name}"


def create_channel_overwrites(member: discord.Member) -> dict:
    """Create permission overwrites for the temporary channel"""
    return {
        member: discord.PermissionOverwrite(
            manage_channels=True,
            manage_permissions=True,
            move_members=True
        )
    }
