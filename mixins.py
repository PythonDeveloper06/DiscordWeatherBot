from discord import Member, Message
from discord.ext.commands import Bot
from discord.channel import TextChannel


async def on_member(word: str, bot: Bot, member: Member) -> Message:
    for guild in bot.guilds:
        if guild == member.guild:
            for tc in guild.text_channels:
                channel: TextChannel = bot.get_channel(tc.id)
                return await channel.send(f'{word} {member.name}')
