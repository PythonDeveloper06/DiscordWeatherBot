import datetime
import asyncio

import discord
from discord import Member, Interaction, app_commands
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
    await bot.tree.sync()
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


@bot.tree.command(name='support', description='Support')
async def support(interaction: Interaction):
    message = discord.Embed(
        title='Описание',
        color=color,
        timestamp=datetime.datetime.now()
    )
    with open("support.txt", encoding='utf-8') as file:
        text = file.read()
    message.add_field(name='Погодный бот', value=text)

    await interaction.response.send_message(embed=message, ephemeral=True)


@bot.tree.command(name='weather', description='Get weather now or for the near future')
@app_commands.choices(weather_output=[app_commands.Choice(name='Now', value='weather'),
                                      app_commands.Choice(name='Forecast', value='forecast')])
async def weather_and_forecast(interaction: Interaction, city: str, weather_output: app_commands.Choice[str]) -> None:
    url = f'http://api.openweathermap.org/data/2.5/{weather_output.value}?q={city}&units=metric&lang=ru&appid={API_KEY}'
    data = await asyncio.gather(asyncio.ensure_future(api_weather(url)))

    message_or_error_message = await material(interaction, data)
    await interaction.response.send_message(embed=message_or_error_message, ephemeral=True)


@bot.command(name='set_time')
async def set_time(ctx: Context, city: str, dt: str) -> None:
    h, m = dt.split(':')
    # while True для продакшнеа. В ТЕСТИРОВАНИИ НЕ ИСПОЛЬЗОВАТЬ! ЗАЦИКЛИТСЯ!
    # Для тестирования while true закомментировать
    # while True:
    now = datetime.datetime.now()
    # then = now + datetime.timedelta(days=1)
    then = now.replace(hour=int(h), minute=int(m))
    wait_time = (then - now).total_seconds()

    await asyncio.sleep(wait_time)

    url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&lang=ru&appid={API_KEY}'
    data = await asyncio.gather(asyncio.ensure_future(api_weather(url)))

    message_or_error_message = await material(ctx, data)

    await ctx.author.send(embed=message_or_error_message)


bot.run(TOKEN)
