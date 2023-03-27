import discord
from discord import Message
from discord.ext import commands
import logging
import asyncio

from conf import TOKEN
from mixins import on_member

logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='/', intents=intents)


@bot.event
async def on_ready() -> None:
    logger.info(f'{bot.user} has connected to Discord!')
    for guild in bot.guilds:
        logger.info(
            f'{bot.user} подключился к чату:\n'
            f'{guild.name} (ID: {guild.id})'
        )


@bot.event
async def on_member_join(member: discord.Member) -> None:
    asyncio.create_task(on_member('Привет', bot, member))


@bot.event
async def on_member_remove(member: discord.Member) -> None:
    asyncio.create_task(on_member('Пока', bot, member))


@bot.command(name='weather', description="Get weather")
async def text(ctx: Message, city: str) -> None:
    await ctx.send(embed=discord.Embed(title=f'Your city {city.capitalize()}', description='Wait a one minute...'))


bot.run(TOKEN)
