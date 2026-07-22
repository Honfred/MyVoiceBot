"""
UI Components for Discord Voice Bot
Contains Views, Buttons, and Modals for channel management
"""
import discord
import logging
from .config import VIEW_TIMEOUT

logger = logging.getLogger(__name__)


class ChannelControlView(discord.ui.View):
    """UI for controlling voice channel settings"""
    
    def __init__(self, channel: discord.VoiceChannel, bot):
        super().__init__(timeout=VIEW_TIMEOUT)
        self.channel = channel
        self.bot = bot

    def _current_controller_id(self):
        """Id of the user currently allowed to control the channel (changes if the owner leaves)"""
        channel_info = self.bot.created_channels.get(self.channel.id)
        return channel_info.get('creator') if channel_info else None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Only allow the current channel controller or admins to use buttons"""
        if interaction.user.id == self._current_controller_id():
            return True
        if isinstance(interaction.user, discord.Member) and interaction.user.guild_permissions.administrator:
            return True
        await interaction.response.send_message(
            "❌ Только владелец канала или администратор может использовать эти кнопки!",
            ephemeral=True
        )
        return False
    
    @discord.ui.button(label='🔒 Приватный', style=discord.ButtonStyle.secondary)
    async def make_private(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Make channel private"""
        try:
            overwrites = self.channel.overwrites
            overwrites[self.channel.guild.default_role] = discord.PermissionOverwrite(connect=False)
            await self.channel.edit(overwrites=overwrites)
            await interaction.response.send_message("🔒 Канал сделан приватным!", ephemeral=True)
            logger.info(f"Channel {self.channel.name} made private by {interaction.user.display_name}")
        except Exception as e:
            logger.error(f"Error making channel private: {e}")
            await interaction.response.send_message(f"❌ Ошибка: {e}", ephemeral=True)
    
    @discord.ui.button(label='🔓 Открытый', style=discord.ButtonStyle.secondary)
    async def make_public(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Make channel public"""
        try:
            overwrites = self.channel.overwrites
            if self.channel.guild.default_role in overwrites:
                del overwrites[self.channel.guild.default_role]
            await self.channel.edit(overwrites=overwrites)
            await interaction.response.send_message("🔓 Канал сделан открытым!", ephemeral=True)
            logger.info(f"Channel {self.channel.name} made public by {interaction.user.display_name}")
        except Exception as e:
            logger.error(f"Error making channel public: {e}")
            await interaction.response.send_message(f"❌ Ошибка: {e}", ephemeral=True)
    
    @discord.ui.button(label='👥 Лимит пользователей', style=discord.ButtonStyle.primary)
    async def set_user_limit(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Set user limit modal"""
        modal = UserLimitModal(self.channel)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label='📝 Переименовать', style=discord.ButtonStyle.primary)
    async def rename_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Rename channel modal"""
        modal = RenameModal(self.channel)
        await interaction.response.send_modal(modal)


class UserLimitModal(discord.ui.Modal, title='Установить лимит пользователей'):
    """Modal for setting user limit"""
    
    def __init__(self, channel: discord.VoiceChannel):
        super().__init__()
        self.channel = channel
    
    user_limit = discord.ui.TextInput(
        label='Количество пользователей (0 = без ограничений)',
        placeholder='Введите число от 0 до 99',
        default='0',
        max_length=2
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            limit = int(self.user_limit.value)
            if limit < 0 or limit > 99:
                await interaction.response.send_message(
                    "❌ Лимит должен быть от 0 до 99!", 
                    ephemeral=True
                )
                return
            
            await self.channel.edit(user_limit=limit)
            limit_text = "без ограничений" if limit == 0 else f"{limit} пользователей"
            await interaction.response.send_message(
                f"👥 Лимит установлен: {limit_text}", 
                ephemeral=True
            )
            logger.info(f"User limit set to {limit} for channel {self.channel.name} by {interaction.user.display_name}")
        except ValueError:
            await interaction.response.send_message("❌ Введите корректное число!", ephemeral=True)
        except Exception as e:
            logger.error(f"Error setting user limit: {e}")
            await interaction.response.send_message(f"❌ Ошибка: {e}", ephemeral=True)


class RenameModal(discord.ui.Modal, title='Переименовать канал'):
    """Modal for renaming channel"""
    
    def __init__(self, channel: discord.VoiceChannel):
        super().__init__()
        self.channel = channel
    
    channel_name = discord.ui.TextInput(
        label='Новое название канала',
        placeholder='Введите новое название',
        max_length=100
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            old_name = self.channel.name
            await self.channel.edit(name=self.channel_name.value)
            await interaction.response.send_message(
                f"📝 Канал переименован: '{old_name}' → '{self.channel_name.value}'", 
                ephemeral=True
            )
            logger.info(f"Channel renamed from '{old_name}' to '{self.channel_name.value}' by {interaction.user.display_name}")
        except Exception as e:
            logger.error(f"Error renaming channel: {e}")
            await interaction.response.send_message(f"❌ Ошибка: {e}", ephemeral=True)
