import discord
from discord.ext import commands
import os

intents = discord.Intents.all()

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"已上線：{bot.user}")

async def load():
    for file in os.listdir("./cogs"):
        if file.endswith(".py"):
            await bot.load_extension(f"cogs.{file[:-3]}")
            
import asyncio
asyncio.run(load())

bot.run(os.getenv("DISCORD_TOKEN"))
