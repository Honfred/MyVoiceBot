import discord
import logging
import os

MAIN_CHANNEL_ID = 901007391477350440
MAIN_CATEGORY_ID = 901007309533245490

# log
logging.basicConfig(level=logging.INFO)


class MyClient(discord.Client):
    async def on_voice_state_update(self, member, before, after):
        ch = after.channel # канал в который перешел пользователь
        if ch != None: 
            if after.channel.id == MAIN_CHANNEL_ID:
                for guild in self.guilds:
                    maincategory = discord.utils.get(
                        guild.categories, id=MAIN_CATEGORY_ID)
                    channel2 = await guild.create_voice_channel(name=f' || { member.display_name }', category=maincategory)
                    channel3 = await guild.create_text_channel(name=f' || { member.display_name }', category=maincategory)

                    await member.move_to(channel2)

                    def check(x, y, z):
                        return len(channel2.members) == 0
                    await self.wait_for('voice_state_update', check=check)
                    await channel2.delete()
                    await channel3.delete()


async def main():
    client = MyClient()
    client.run(os.environ.get('TOKEN'))
    return 'ok'
