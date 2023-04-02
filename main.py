import datetime
import asyncio

import discord
from discord import Member
from discord.ext.commands import Bot, Context
import logging

from config import TOKEN, API_KEY
from mixins import on_member, api_weather, material

logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

color = 0x00FFFF
HPa_to_mmHg = 0.750064

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
    message = discord.Embed(
        title=f'Привет, {member.name}!',
        color=color,
        timestamp=datetime.datetime.now()
    )
    message.add_field(
        name='Я погодный бот',
        value='*Чтобы узнать больше обо мне, напиши в чат сервера команду:*\n'
              '*/support*',
    )
    await member.dm_channel.send(embed=message)
    asyncio.create_task(on_member('Добро пожаловать,', bot, member))


@bot.event
async def on_member_remove(member: Member) -> None:
    asyncio.create_task(on_member('Наш сервер покидает', bot, member))


@bot.command(name='support')
async def support(ctx):
    channel = ctx.message.channel
    message = discord.Embed(
        title='Описание',
        color=color,
        timestamp=ctx.message.created_at
    )
    message.add_field(
        name='Погодный бот',
        value='*Я буду полезнен, когда вам потребуется узнать погоду, не выходя из дискорда.*\n'
              '*Это чень удобно и просто в использовании.*\n'
              'Основные команды:\n'
              '*/weather {city}: показывает погоду на данный момент заданного города;*\n'
              '*/forecast {city}: показывает погоду на ближайшее время, 3 и на 6 часов вперёд*'
              '*/support: показывает то, что может погодный бот.*'
    )
    await channel.send(embed=message)


@bot.command(name='weather')
async def api(ctx: Context, city: str) -> None:
    url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&lang=ru&appid={API_KEY}'
    data = await asyncio.gather(asyncio.ensure_future(api_weather(url)))
    channel = ctx.message.channel

    message_or_error_message = await material(channel, ctx, data)
    await channel.send(embed=message_or_error_message)


@bot.command(name='forecast')
async def _forecast(ctx: Context, city: str) -> None:
    url = f'http://api.openweathermap.org/data/2.5/forecast?q={city}&units=metric&lang=ru&appid={API_KEY}'
    data = await asyncio.gather(api_weather(url))
    channel = ctx.message.channel

    message_or_error_message = await material(channel, ctx, data)
    await channel.send(embed=message_or_error_message)


bot.run(TOKEN)
