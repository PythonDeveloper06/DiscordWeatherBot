from typing import AsyncGenerator, Generator
import aiohttp
import discord
from aiohttp import ClientResponse
from discord import Member, Message
from discord.ext.commands import Bot, Context
from discord.channel import TextChannel

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


def from_message(info: tuple) -> Generator[list, None, None]:
    count = 0
    if 'list' not in info[0]:
        description = info[0]['weather'][0]['description']
        icon = info[0]['weather'][0]['icon']

        temperature = info[0]['main']['temp']
        feels_like = info[0]['main']['feels_like']
        pressure = info[0]['main']['pressure']
        humidity = info[0]['main']['humidity']

        speed = info[0]['wind']['speed']

        yield [description, icon, temperature, feels_like, pressure, humidity, speed]
    else:
        for index, inf in enumerate(info[0]['list']):
            if count != 3:
                description = info[0]['list'][index + 2]['weather'][0]['description']
                icon = info[0]['list'][index + 2]['weather'][0]['icon']

                temperature = info[0]['list'][index + 2]['main']['temp']
                feels_like = info[0]['list'][index + 2]['main']['feels_like']
                pressure = info[0]['list'][index + 2]['main']['pressure']
                humidity = info[0]['list'][index + 2]['main']['humidity']

                speed = info[0]['list'][index + 2]['wind']['speed']

                date = info[0]['list'][index + 2]['dt_txt']

                count += 1

                yield [description, icon, temperature, feels_like, pressure, humidity, speed, date]
            else:
                break


def add_message(func: Generator[list, None, None], ctx: Context, name: str) -> discord.Embed:
    message = discord.Embed(
        title=f"Погода в {name}",
        color=color,
        timestamp=ctx.message.created_at
    )

    for dt in func:
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
            name="Атмосферное давление", value=f"**{round(int(dt[4]) * HPa_to_mmHg)}мм рт. ст.**",
            inline=False)
        message.add_field(
            name="Скорость ветра", value=f"**{dt[6]}м/с**", inline=False)

        message.set_thumbnail(url=f"https://openweathermap.org/img/wn/{dt[1]}@2x.png")

        message.set_footer(text=f"Запрошено {ctx.author.name}")

    return message


async def material(channel: TextChannel, ctx: Context, info: tuple) -> discord.Embed:
    if info[0]['cod'] != '404':
        async with channel.typing():
            if 'list' not in info[0]:
                name = info[0]['name']
            else:
                name = info[0]['city']['name']
            if 'list' not in info[0]:
                return add_message(from_message(info), ctx, name)
            else:
                return add_message(from_message(info), ctx, name)
    else:
        error_message = discord.Embed(
            title='Ошибка',
            description=f'Произошла ошибка при получении данных о погоде для {ctx.author.name}.\n'
                        f'*Проверьте, верно ли введено название города.*',
            color=color
        )
        return error_message
