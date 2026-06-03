import os
import discord

from dotenv import load_dotenv
from discord.ext import commands

from database import init_db

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.members = True
intents.voice_states = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


@bot.event
async def setup_hook():

    init_db()

    await bot.load_extension("cogs.game")

    await bot.tree.sync()


bot.run(TOKEN)
