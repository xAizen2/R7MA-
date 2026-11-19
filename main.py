
import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import os

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

queues = {}
players = {}

async def play_next(guild):
    queue = queues.get(guild.id, [])
    if not queue:
        players.pop(guild.id, None)
        return

    url = queue.pop(0)
    voice = guild.voice_client

    if not voice:
        return

    source = discord.FFmpegPCMAudio(
        url,
        before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
        options="-vn"
    )

    loop = asyncio.get_running_loop()

    def after(error):
        if error:
            print(f"Audio error: {error}")
        asyncio.run_coroutine_threadsafe(
            play_next(guild), loop
        )

    players[guild.id] = url
    voice.play(source, after=after)


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"R7MA is online: {bot.user}")


@bot.tree.command(name="play", description="تشغيل رابط صوتي")
@app_commands.describe(url="رابط الصوت المباشر")
async def play(interaction: discord.Interaction, url: str):

    if not interaction.user.voice:
        await interaction.response.send_message(
            "ادخل روم صوتي أولاً 🎧",
            ephemeral=True
        )
        return

    await interaction.response.defer()

    channel = interaction.user.voice.channel
    voice = interaction.guild.voice_client

    if voice is None:
        voice = await channel.connect()
    elif voice.channel != channel:
        await voice.move_to(channel)

    queue = queues.setdefault(interaction.guild.id, [])
    queue.append(url)

    if not voice.is_playing() and not voice.is_paused():
        await play_next(interaction.guild)

    await interaction.followup.send("🎵 تمت إضافة الرابط إلى R7MA!")


@bot.tree.command(name="skip", description="تخطي الصوت")
async def skip(interaction: discord.Interaction):
    voice = interaction.guild.voice_client

    if voice and (voice.is_playing() or voice.is_paused()):
        voice.stop()
        await interaction.response.send_message("⏭️ تم التخطي")
    else:
        await interaction.response.send_message("لا يوجد صوت يعمل")


@bot.tree.command(name="pause", description="إيقاف مؤقت")
async def pause(interaction: discord.Interaction):
    voice = interaction.guild.voice_client

    if voice and voice.is_playing():
        voice.pause()
        await interaction.response.send_message("⏸️ تم الإيقاف المؤقت")
    else:
        await interaction.response.send_message("لا يوجد صوت يعمل")


@bot.tree.command(name="resume", description="استكمال التشغيل")
async def resume(interaction: discord.Interaction):
    voice = interaction.guild.voice_client

    if voice and voice.is_paused():
        voice.resume()
        await interaction.response.send_message("▶️ تم الاستكمال")
    else:
        await interaction.response.send_message("لا يوجد صوت متوقف")


@bot.tree.command(name="queue", description="عرض قائمة الانتظار")
async def show_queue(interaction: discord.Interaction):
    queue = queues.get(interaction.guild.id, [])

    if not queue:
        await interaction.response.send_message("📭 القائمة فارغة")
        return

    text = "\n".join(
        f"{i+1}. {url}" for i, url in enumerate(queue)
    )

    await interaction.response.send_message(
        f"🎵 قائمة R7MA:\n{text[:1800]}"
    )


@bot.tree.command(name="stop", description="إيقاف البوت")
async def stop(interaction: discord.Interaction):
    voice = interaction.guild.voice_client

    queues[interaction.guild.id] = []

    if voice:
        await voice.disconnect()

    players.pop(interaction.guild.id, None)

    await interaction.response.send_message(
        "👋 R7MA غادر الروم الصوتي"
    )


if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing")

bot.run(TOKEN)
  
