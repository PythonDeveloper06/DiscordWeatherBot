import asyncio
import datetime
from typing import AsyncGenerator, Union

import aiohttp
from aiohttp import ClientResponse
from discord import Member, Message, Interaction, Embed
from discord.channel import TextChannel
from discord.ext.commands import Bot, Context

from config import API_KEY

color = 0x00FFFF
HPa_to_mmHg = 0.750064


async def on_member(word: str, bot: Bot, member: Member) -> Message:
    for guild in bot.guilds:
        if guild == member.guild:
            for tc in guild.text_channels:
                channel: TextChannel = bot.get_channel(tc.id)
                return await channel.send(f'{word} {member.name}')


async def api_weather(url: str) -> ClientResponse:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as res:
            return await res.json()


async def from_message(info: tuple) -> AsyncGenerator[list, tuple]:
    if 'list' not in info[0]:
        description = info[0]['weather'][0]['description']
        icon = info[0]['weather'][0]['icon']

        temperature = info[0]['main']['temp']
        feels_like = info[0]['main']['feels_like']
        pressure = info[0]['main']['pressure']
        humidity = info[0]['main']['humidity']

        speed = info[0]['wind']['speed']

        yield description, icon, temperature, feels_like, pressure, humidity, speed
    else:
        for index, inf in enumerate(info[0]['list']):
            if index != 3:
                base = info[0]['list'][index + 2]

                description = base['weather'][0]['description']
                icon = base['weather'][0]['icon']

                temperature = base['main']['temp']
                feels_like = base['main']['feels_like']
                pressure = base['main']['pressure']
                humidity = base['main']['humidity']

                speed = base['wind']['speed']
                date = base['dt_txt']

                yield description, icon, temperature, feels_like, pressure, humidity, speed, date
            else:
                break


async def add_message(func: AsyncGenerator[list, tuple], name: str, user: str) -> Embed:
    message = Embed(
        title=f"Погода в {name}",
        color=color,
        timestamp=datetime.datetime.now()
    )

    async for dt in func:
        if len(dt) == 8:
            message.add_field(name='**------------Дата-и-время------------**',
                              value=f'*----------{dt[-1]}----------*',
                              inline=False)
        message.add_field(
            name="Описание", value=f"**{dt[0].capitalize()}**", inline=False)
        message.add_field(
            name="Температура", value=f"**{dt[2]}°C**", inline=False)
        message.add_field(
            name="Ощущается", value=f"**{dt[3]}°C**", inline=False)
        message.add_field(
            name="Влажность", value=f"**{dt[5]}%**", inline=False)
        message.add_field(
            name="Атмосферное давление", value=f"**{round(int(dt[4]) * HPa_to_mmHg)}мм рт. ст.**", inline=False)
        message.add_field(
            name="Скорость ветра", value=f"**{dt[6]}м/с**", inline=False)

        message.set_thumbnail(url=f"https://openweathermap.org/img/wn/{dt[1]}@2x.png")

        message.set_footer(text=f"Запрошено {user}")

    return message


async def material(interaction: Union[Interaction, Context], info: tuple) -> Embed:
    user = interaction.author.name if interaction.__class__ == Context else interaction.user.name
    if info[0]['cod'] != '404':
        name = info[0]['name'] if 'list' not in info[0] else info[0]['city']['name']
        return await add_message(from_message(info), name, user)
    else:
        error_message = Embed(
            title='Ошибка',
            description=f'Произошла ошибка при получении данных о погоде для {user}.\n'
                        f'*Проверьте, верно ли введено название города.*',
            color=color
        )
        return error_message


async def auto_send(ctx: Context, city: str, date: str):
    print('------------------------------------------------')
    h, m, *s = date.split(':')
    while True:
        now = datetime.datetime.now()
        print(f'Time is now: {now}')
        then = now + datetime.timedelta(days=1)
        print(f'Time + 1 day: {then}')
        plan_time = then.replace(hour=int(h), minute=int(m), second=0)
        print(f'Time of completion: {plan_time}')

        wait_time = (plan_time - now).total_seconds()
        print(f'Time of wait: {wait_time} seconds')
        print('------------------------------------------------')

        await asyncio.sleep(wait_time)

        url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&lang=ru&appid={API_KEY}'
        data = await asyncio.gather(asyncio.ensure_future(api_weather(url)))

        message_or_error_message = await asyncio.ensure_future(material(ctx, data))
        yield message_or_error_message


async def auto_send_hour(ctx: Context, city: str, date: str):
    print('------------------------------------------------')
    h, m, *s = date.split(':')
    while True:
        now = datetime.datetime.now()
        print(f'Time is now: {now}')
        usl = datetime.datetime(year=now.year, month=now.month, day=now.day, hour=int(h), minute=int(m))
        print(f'Entered time: {usl}')

        if now < usl:
            then = datetime.datetime.now().replace(hour=int(h), minute=int(m), second=0) + \
                   datetime.timedelta(hours=1)
        else:
            then = datetime.datetime(year=now.year, month=now.month, day=now.day, hour=now.hour,
                                     minute=now.minute, second=0) + datetime.timedelta(hours=1)
        print(f'Time of completion: {then}')
        wait_time = (then - now).total_seconds()
        print(f'Time of wait: {wait_time} seconds')
        print('------------------------------------------------')

        await asyncio.sleep(wait_time)

        url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&lang=ru&appid={API_KEY}'
        data = await asyncio.gather(asyncio.ensure_future(api_weather(url)))

        message_or_error_message = await asyncio.ensure_future(material(ctx, data))
        yield message_or_error_message
