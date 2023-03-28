import discord
from discord import Member
from discord.ext.commands import Bot, Context
import logging
import asyncio
import requests
import json


from conf import TOKEN
from mixins import on_member

logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

api_key = ''
color = 0x00FFFF

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


@bot.command(name='weather')
async def weather(ctx: Context,  city: str) -> None:
    location = city
    url = f'http://api.openweathermap.org/data/2.5/weather?q={location}&units=metric&lang=ru&appid={api_key}'
    data = json.loads(requests.get(url).content)
    channel = ctx.message.channel

    if data['cod'] != "404":
        async with channel.typing():
            weather = data['weather']
            description = weather[0]['description']
            icon = weather[0]['icon']

            main = data['main']
            temperature = main['temp']
            feels_like = main['feels_like']
            pressure = main['pressure']
            humidity = main['humidity']

            wind = data['wind']
            speed = wind['speed']

            message = discord.Embed(
                title=f"Погода в {location}",
                color=color,
                timestamp=ctx.message.created_at
            )
            message.add_field(
                name="Описание", value=f"**{description}**", inline=False)
            message.add_field(
                name="Температура", value=f"**{temperature}°C**", inline=False)
            message.add_field(
                name="Ощущается", value=f"**{feels_like}°C**", inline=False)
            message.add_field(
                name="Влажность", value=f"**{humidity}%**", inline=False)
            message.add_field(
                name="Атмосферное давление", value=f"**{pressure}hPa**", inline=False)
            message.add_field(
                name="Скорость ветра", value=f"**{speed}м/с**", inline=False)

            message.set_thumbnail(url=f"https://openweathermap.org/img/wn/{icon}@2x.png")

            message.set_footer(text=f"Запрошено {ctx.author.name}")
        await channel.send(embed=message)
    else:
        error_message = discord.Embed(
            title='Ошибка',
            description=f'Произошла ошибка при получении данных о погоде для {location}.',
            color=color
        )
        await channel.send(embed=error_message)


bot.run(TOKEN)
