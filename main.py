import datetime
import asyncio
import discord
from discord import Member
from discord.ext.commands import Bot, Context
import logging
import aiohttp

from config import TOKEN, API_KEY
from mixins import on_member

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
              '*/support: показывает то, что может погодный бот.*'
    )
    await channel.send(embed=message)


@bot.command(name='weather')
async def text(ctx: Context, city: str) -> None:
    async with aiohttp.ClientSession() as session:
        url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&lang=ru&appid={API_KEY}'
        async with session.get(url) as res:
            data = await res.json()
    channel = ctx.message.channel

    if data['cod'] != '404':
        description = data['weather'][0]['description']
        icon = data['weather'][0]['icon']

        temperature = data['main']['temp']
        feels_like = data['main']['feels_like']
        pressure = data['main']['pressure']
        humidity = data['main']['humidity']

        speed = data['wind']['speed']

        message = discord.Embed(
            title=f"Погода в {city.capitalize()}",
            color=color,
            timestamp=ctx.message.created_at
        )
        message.add_field(
            name="Описание", value=f"**{description.capitalize()}**", inline=False)
        message.add_field(
            name="Температура", value=f"**{temperature}°C**", inline=False)
        message.add_field(
            name="Ощущается", value=f"**{feels_like}°C**", inline=False)
        message.add_field(
            name="Влажность", value=f"**{humidity}%**", inline=False)
        message.add_field(
            name="Атмосферное давление", value=f"**{round(pressure * HPa_to_mmHg)}мм рт. ст.**", inline=False)
        message.add_field(
            name="Скорость ветра", value=f"**{speed}м/с**", inline=False)

        message.set_thumbnail(url=f"https://openweathermap.org/img/wn/{icon}@2x.png")

        message.set_footer(text=f"Запрошено {ctx.author.name}")
        await channel.send(embed=message)

    else:
        error_message = discord.Embed(
            title='Ошибка',
            description=f'Произошла ошибка при получении данных о погоде для {city}.',
            color=color
        )
        await channel.send(embed=error_message)


bot.run(TOKEN)
