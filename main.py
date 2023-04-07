import datetime
import asyncio

import aiosqlite
import discord
from discord import Member, Interaction, app_commands
from discord.ext.commands import Bot, Context
import logging

from config import TOKEN, API_KEY
from mixins import on_member, api_weather, material, auto_send

logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

color = 0x00FFFF

bot = Bot(command_prefix='/', intents=intents)


@bot.event
async def on_ready() -> None:
    synced = await bot.tree.sync()
    logger.info(f'Amount of connected Slash commands: {len(synced)}')
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
    message.add_field(
        name='Погодный бот',
        value='*Я буду полезнен, когда вам потребуется узнать погоду, не выходя из дискорда.*\n'
              '*Это очень удобно и просто в использовании.*\n'
              '**Основные команды:**\n'
              '*/weather {city} {weather output}:*\n'
              '1.) {weather output} = Now: показывает погоду на данный момент заданного города;\n'
              '2.) {weather output} = Forecast: показывает погоду на ближайшее время, на 3 и на 6 часов вперёд;\n'
              '---------------------------\n'
              '*/support: показывает то, что может погодный бот;*\n'
              '---------------------------\n'
              '*/set_exact_time {city} {time (формат HH:MM)} {hours} {minutes}: '
              'в установленное время бот будет выводить вам в личное сообщение актуальную погоду:*\n'
              '1.) {hours}: устанавливает нужный час (по умолчанию - 1 час). Для установки, '
              'вводится нужный час и буква H на конце, например, 3H;\n'
              '2.) {minutes}: устанавливет нужную минуту (по умолчанию - 0 минут). Для установки, '
              'вводится нужная минута и буква М на конце, например, 3М;\n'
              '---------------------------\n'
              '*/set_time: в установленное время бот будет выводить вам каждый день в личное сообщение '
              'актуальную погоду.*'
    )
    await interaction.response.send_message(embed=message, ephemeral=True)


@bot.tree.command(name='weather', description='Get weather now or for the near future')
@app_commands.choices(weather_output=[app_commands.Choice(name='Now', value='weather'),
                                      app_commands.Choice(name='Forecast', value='forecast')])
async def weather_and_forecast(interaction: Interaction, city: str, weather_output: app_commands.Choice[str]) -> None:
    url = f'http://api.openweathermap.org/data/2.5/{weather_output.value}?q={city}&units=metric&lang=ru&appid={API_KEY}'
    data = await asyncio.gather(asyncio.ensure_future(api_weather(url)))

    message_or_error_message = await material(interaction, data)
    await interaction.response.send_message(embed=message_or_error_message, ephemeral=True)


@bot.command(name='set_exact_time')
async def set_exact_time(ctx: Context, city: str, dt: str, hours: str = '1H', minutes: str = '0M') -> None:
    h, m, *s = dt.split(':')
    now = datetime.datetime.now()
    logger.info(f'Time is now: {now}')

    then = now.replace(hour=int(h), minute=int(m), second=0) + datetime.timedelta(hours=int(hours[0]),
                                                                                  minutes=int(minutes[0]))
    logger.info(f'Time of completion: {then}')

    wait_time = (then - now).total_seconds()
    logger.info(f'Time of wait: {wait_time} seconds')

    await asyncio.sleep(wait_time)

    url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&lang=ru&appid={API_KEY}'
    data = await asyncio.gather(asyncio.ensure_future(api_weather(url)))

    message_or_error_message = await asyncio.ensure_future(material(ctx, data))

    await ctx.author.send(embed=message_or_error_message)

    logger.info('---------------------------------------')


@bot.command(name='set_time')
async def set_time(ctx: Context, city: str, dt: str) -> None:
    async for message_or_error_message in auto_send(ctx, city, dt, True):
        await ctx.author.send(embed=message_or_error_message)


@bot.tree.command(name='registration', description='Set the city and time for the default weather display')
async def regis(interaction: Interaction, city: str, install_time: str):
    try:
        db = await aiosqlite.connect('bot.db')
        await db.execute("INSERT INTO users VALUES(?, ?, ?)", (interaction.user.name, city, install_time))
        await db.commit()
        await interaction.response.send_message(
            f'Ваш город **{city}** и время **{install_time}** было успешно сохранено',
            ephemeral=True)
    except Exception as e:
        await interaction.response.send_message('Вы уже зарегистрировались', ephemeral=True)


@bot.command(name='start', description='Starts automatic weather sending')
async def start(ctx: Context) -> None:
    try:
        db = await aiosqlite.connect('bot.db')
        data = await db.execute("SELECT city, installed_time FROM users WHERE username = ?", (ctx.author.name,))
        res = await data.fetchone()
        async for message_or_error_message in auto_send(ctx, res[0], res[1]):
            await ctx.author.send(embed=message_or_error_message)
    except Exception as e:
        await ctx.author.send('Вы должны зарегистрироваться, чтобы использовать команду /start.\n'
                              'Команда регистрации: /registration')


bot.run(TOKEN)
