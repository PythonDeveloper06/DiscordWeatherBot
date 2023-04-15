import datetime
import asyncio

from sqlalchemy import select, update
import discord
from discord import Member, Interaction, app_commands, Embed
from discord.ext.commands import Bot, Context
import logging

from config import TOKEN, API_KEY
from mixins import on_member, api_weather, material, auto_send, auto_send_hour

from data import db_session
from data.users import User

logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)

intents = discord.Intents.all()
intents.members = True
intents.message_content = True

color = 0x00FFFF

bot = Bot(command_prefix='/', intents=intents)


@bot.event
async def on_ready() -> None:
    await db_session.global_init('bot.db')
    logger.info(f"Подключение к базе данных: sqlite+aiosqlite:///bot.db?check_same_thread=False")
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
              'в установленное время бот выведет вам в личное сообщение актуальную погоду:*\n'
              '1.) {hours}: устанавливает нужный час (по умолчанию - 1 час). Для установки, '
              'вводится нужный час и буква H на конце, например, 3H;\n'
              '2.) {minutes}: устанавливет нужную минуту (по умолчанию - 0 минут). Для установки, '
              'вводится нужная минута и буква М на конце, например, 3М;\n'
    )
    message.add_field(
        name='---------------------------\n',
        value='*/set_time {value} {city} {time}: в установленное время бот будет выводить вам каждый час '
              'в личное сообщение актуальную погоду;*\n'
              '1.) {value} = on: запускает автоматическую отправку погоды указанного города;\n'
              '2.) {weather output} = off: останавливает отправку сообщений;\n'
              '**!!!Предупреждение!!!**\n'
              '**Из - за особенности работы работы команды /set_time, вам для остановки рассылки сообщений '
              'нужно будет ввести команду /set_time off ЗА 1 ЧАС до назначенного часа, когда вы захотите '
              'прекратить рассылку сообщений. В назначенный час бот пришлёт вам'
              'в нужное время cообщение и рассылка прекратится**',
        inline=False
    )
    message.add_field(
        name='---------------------------',
        value='*/registration: вводится город и время, '
             'которые сохраняются и затем используются для вывода погоды '
              'в нужное время и каждый день;*\n'
              '---------------------------\n'
              '*/start {value (по умолчанию = on)}: при вызове команды, '
              'автоматически каждый день во время, введённое при вызове команды /registration '
              'будет выводиться погода для города, введённого при вызове команды /registration. '
              'Команда остановки: /start off.*\n'
              '**!!!Предупреждение!!!**\n'
              '**Из - за особенности работы работы команды /start, вам для остановки рассылки сообщений '
              'нужно будет ввести команду /start off ЗА 1 ДЕНЬ до назначенного дня, когда вы захотите '
              'прекратить рассылку сообщений. В назначенный день бот пришлёт вам'
              'в нужное время cообщение и рассылка прекратится**\n',
        inline=False
    )
    message.add_field(
        name='---------------------------',
        value='*Это музыкальная составляющая погодного бота, вы можете прослушать на выбор 3 звука природы:*\n'
              '*1-Гроза;*\n'
              '*2-Сверчки;*\n'
              '*3-Шум реки.*\n'
              '*/join - присоединение бота к голосовому каналу*\n'
              '*/disconnect - отключение бота из голосового канала*\n'
              '*/play - проигрывание музыки*\n'
              '*/pause - остановка проигрывания музыки*\n'
              '*/resume - воспроизведение проигрывания музыки*\n',
        inline=False
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
    logger.info('---------------------------------------')
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
async def set_time(ctx: Context, value: str = 'on', city: str = '', dt: str = '') -> None:
    # result = auto_send(ctx, res[0], res[1])
    # task = await asyncio.create_task(auto_send(result.__anext__())
    task = asyncio.create_task(auto_send_hour(ctx, city, dt).__anext__())
    if value == 'off':
        task.cancel()
        # await result.aclose()
        await ctx.author.send('Отправка сообщений остановлена')
    else:
        # async for data in result:
        await ctx.author.send(embed=(await task))


@bot.tree.command(name='registration', description='Set the city and time for the default weather display')
async def regis(interaction: Interaction, city: str, install_time: str):
    try:
        user = User(username=interaction.user.name, city=city, installed_time=install_time)
        db_sess = await db_session.create_session()
        db_sess.add(user)
        await db_sess.commit()
        await db_sess.close()

        await interaction.response.send_message(embed=Embed(title=f'Город **{city}** и время **{install_time}** '
                                                                  f'были успешно сохранены',
                                                            color=color, timestamp=datetime.datetime.now()),
                                                ephemeral=True)
    except Exception:
        await interaction.response.send_message(embed=Embed(title=f'Вы уже зарегистрировались', color=color,
                                                            timestamp=datetime.datetime.now()),
                                                ephemeral=True)


@bot.command(name='start', description='Starts automatic weather sending')
async def start(ctx: Context, value: str = 'on') -> None:
    try:
        db_sess = await db_session.create_session()
        query = select(User).where(User.username == ctx.message.author.name)
        user = await db_sess.execute(query)
        result = user.scalars().one()
        await db_sess.close()

        # result = auto_send(ctx, res[0], res[1])
        # task = await asyncio.create_task(auto_send(result.__anext__())

        task = asyncio.create_task(auto_send(ctx, result.city, result.installed_time).__anext__())
        if value == 'off':
            task.cancel()
            # await result.aclose()
            await ctx.author.send('Отправка сообщений остановлена')
        else:
            # async for data in result:
            await ctx.author.send(embed=(await task))
    except Exception:
        await ctx.author.send(embed=Embed(title='Сначала нужно зарегистрироваться.\nКоманда регистрации: /registration',
                                          color=color, timestamp=ctx.message.created_at))


@bot.tree.command(name='update', description='Updates stored data')
async def update(interaction: Interaction, city: str = '-', dt: str = '-'):
    try:
        db_sess = await db_session.create_session()
        query = select(User).where(User.username == interaction.user.name)
        user = await db_sess.execute(query)
        result = user.scalars().one()

        if city == '-':
            result.installed_time = dt
            await db_sess.commit()
            await interaction.response.send_message(embed=Embed(title=f'Ваше время успешно обновлено', color=color,
                                                                timestamp=datetime.datetime.now()),
                                                    ephemeral=True)
        elif dt == '-':
            result.city = city
            await db_sess.commit()
            await interaction.response.send_message(embed=Embed(title=f'Ваш город успешно обновлён', color=color,
                                                                timestamp=datetime.datetime.now()),
                                                    ephemeral=True)
        elif dt == '-' and city == '-':
            result.city = city
            result.installed_time = dt
            await db_sess.commit()
            await interaction.response.send_message(embed=Embed(title=f'Ваши данные успешно обновлены', color=color,
                                                                timestamp=datetime.datetime.now()),
                                                    ephemeral=True)
    except Exception:
        await interaction.response.send_message(embed=Embed(title='Сначала нужно зарегистрироваться.\n'
                                                                  'Команда регистрации: /registration',
                                                            color=color, timestamp=datetime.datetime.now()),
                                                ephemeral=True)


@bot.command(name='join', description='Tells the bot to join the voice channel')
async def join(ctx: Context) -> None:
    if ctx.message.author.voice:
        if not ctx.voice_client:
            await ctx.message.author.voice.channel.connect(reconnect=True)
        else:
            await ctx.voice_client.move_to(ctx.message.author.voice.channel)
    else:
        await ctx.message.reply('❗ Вы должны находиться в голосовом канале ❗')


@bot.command(name='disconnect', description='To make the bot leave the voice channel')
async def disconnect(ctx: Context) -> None:
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
    else:
        await ctx.message.reply('❗ Бот не подключен к голосовому каналу ❗')


@bot.command(name='play', description='To play song')
async def play(ctx: Context, *, file_name: str) -> None:
    try:
        server = ctx.message.guild
        voice_channel = server.voice_client
        async with ctx.typing():
            audio_file = f'audio_files/{file_name}.mp3'
            voice_channel.play(discord.FFmpegPCMAudio(executable="ffmpeg/ffmpeg.exe", source=audio_file))
    except:
        await ctx.message.reply("❗ Бот не подключен к голосовому каналу ❗")


@bot.command(name='pause', description='Stops the song')
async def pause(ctx: Context) -> None:
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice:
        voice.pause()
        await ctx.message.reply('Музыка приостановлена.')


@bot.command(name='resume', description='Resumes the song')
async def resume(ctx: Context) -> None:
    voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice:
        if voice.is_paused():
            voice.resume()
            await ctx.message.reply('Музыка продолжается.')


@bot.event
async def on_voice_state_update(member: Member, before, after) -> None:
    voice = discord.utils.get(bot.voice_clients, guild=member.guild)
    if voice and voice.is_connected():
        if len(voice.channel.members) == 1:
            await voice.disconnect()

bot.run(TOKEN)
