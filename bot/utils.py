"""
Utility functions for Discord Voice Bot
"""
import discord
import logging
from .views import ChannelControlView

logger = logging.getLogger(__name__)


async def send_control_message(channel: discord.VoiceChannel, creator: discord.Member, bot):
    """Send control message with buttons to the voice channel's chat (visible to everyone, but only the current controller may use the buttons)"""
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
                "📝 **Переименовать** - изменить название"
            ),
            inline=False
        )
        
        embed.set_footer(text="Кнопками может пользоваться только владелец канала и администраторы")

        # Create view with control buttons; it looks up the current controller from the bot at click time
        view = ChannelControlView(channel, bot)

        # Send the message to the voice channel's chat without pinging anyone
        message = await channel.send(embed=embed, view=view, silent=True)

        logger.info(f"Control message sent to channel {channel.name}")
        return message

    except Exception as e:
        logger.error(f"Error sending control message: {e}", exc_info=True)
        return None


async def cleanup_control_message(message: discord.Message):
    """Delete the control message before deleting the channel"""
    try:
        await message.delete()
        logger.debug("Control message deleted")
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
