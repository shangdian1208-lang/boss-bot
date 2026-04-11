import discord
from discord.ext import commands
import os
import asyncio

intents = discord.Intents.all()

bot = commands.Bot(command_prefix="!", intents=intents)


# ================== 🧠 載入 Cogs ==================
async def load_cogs():
    for file in os.listdir("./cogs"):
        if file.endswith(".py"):
            await bot.load_extension(f"cogs.{file[:-3]}")


# ================== 🚀 啟動流程 ==================
async def main():
    async with bot:
        await load_cogs()
        await bot.start(os.getenv("DISCORD_TOKEN"))


# ================== 🔥 sync slash ==================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"已上線：{bot.user}")


asyncio.run(main())
