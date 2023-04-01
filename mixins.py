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


async def material(channel: TextChannel, ctx: Context, info: tuple) -> discord.Embed:
    count = 0

    if info[0]['cod'] != '404':
        async with channel.typing():
            if 'list' not in info[0]:
                name = info[0]['name']
            else:
                name = info[0]['city']['name']

            if 'list' not in info[0]:
                description = info[0]['weather'][0]['description']
                icon = info[0]['weather'][0]['icon']

                temperature = info[0]['main']['temp']
                feels_like = info[0]['main']['feels_like']
                pressure = info[0]['main']['pressure']
                humidity = info[0]['main']['humidity']

                speed = info[0]['wind']['speed']

                message = discord.Embed(
                    title=f"Погода в {name}",
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
            else:
                message = discord.Embed(
                    title=f"Погода в {name}",
                    color=color,
                    timestamp=ctx.message.created_at
                )

                for index, inf in enumerate(info[0]['list']):
                    if count != 3:
                        description = info[0]['list'][index+2]['weather'][0]['description']
                        icon = info[0]['list'][index+2]['weather'][0]['icon']

                        temperature = info[0]['list'][index+2]['main']['temp']
                        feels_like = info[0]['list'][index+2]['main']['feels_like']
                        pressure = info[0]['list'][index+2]['main']['pressure']
                        humidity = info[0]['list'][index+2]['main']['humidity']

                        speed = info[0]['list'][index+2]['wind']['speed']

                        date = info[0]['list'][index+2]['dt_txt']

                        message.add_field(name='**------------Дата-и-время------------**',
                                          value=f'*----------{date}----------*',
                                          inline=False)

                        message.add_field(
                            name="Описание", value=f"**{description.capitalize()}**", inline=False)
                        message.add_field(
                            name="Температура", value=f"**{temperature}°C**", inline=False)
                        message.add_field(
                            name="Ощущается", value=f"**{feels_like}°C**", inline=False)
                        message.add_field(
                            name="Влажность", value=f"**{humidity}%**", inline=False)
                        message.add_field(
                            name="Атмосферное давление", value=f"**{round(pressure * HPa_to_mmHg)}мм рт. ст.**",
                            inline=False)
                        message.add_field(
                            name="Скорость ветра", value=f"**{speed}м/с**", inline=False)

                        message.set_thumbnail(url=f"https://openweathermap.org/img/wn/{icon}@2x.png")

                        count += 1

            message.set_footer(text=f"Запрошено {ctx.author.name}")

            return message
    else:
        error_message = discord.Embed(
            title='Ошибка',
            description=f'Произошла ошибка при получении данных о погоде для {ctx.author.name}.\n'
                        f'*Проверьте, верно ли введено название города.*',
            color=color
        )

        return error_message
