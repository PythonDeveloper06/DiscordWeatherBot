import discord
from discord.ext import commands
import logging

from conf import TOKEN

logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='/', intents=intents)


@bot.event
async def on_ready():
    logger.info(f'{bot.user} has connected to Discord!')
    for guild in bot.guilds:
        logger.info(
            f'{bot.user} подключился к чату:\n'
            f'{guild.name}(ID: {guild.id})'
        )


@bot.event
async def on_member_join(member):
    guild = member.guild
    if guild.system_channel is not None:
        to_send = f'Welcome {member.mention} to {guild.name}!'
        await guild.system_channel.send(to_send)


@bot.command(name='weather')
async def text(ctx, city: str):
    await ctx.send(city.capitalize())


bot.run(TOKEN)

