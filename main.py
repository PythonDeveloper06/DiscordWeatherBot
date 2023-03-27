import discord
from discord import Member
from discord.ext.commands import Bot, Context
import logging
import asyncio


from conf import TOKEN
from mixins import on_member

logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = Bot(command_prefix='/', intents=intents)


@bot.event
async def on_ready() -> None:
    logger.info(f'{bot.user} has connected to Discord!')
    for guild in bot.guilds:
        logger.info(
            f'{bot.user} подключился к чату:\n'
            f'{guild.name} (ID: {guild.id})'
        )


@bot.event
async def on_member_join(member: Member) -> None:
    await member.create_dm()
    await member.dm_channel.send(
        f'Привет, {member.name}!'
    )
    asyncio.create_task(on_member('Добро пожаловать,', bot, member))


@bot.event
async def on_member_remove(member: Member) -> None:
    asyncio.create_task(on_member('Наш канал покидает', bot, member))


@bot.command(name='weather', description="Get weather")
async def weather(ctx: Context,  city: str) -> None:
    await ctx.send(embed=discord.Embed(title=f'Your city {city.capitalize()}', description='Wait a one minute...'))


bot.run(TOKEN)
