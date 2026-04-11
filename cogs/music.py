import discord
from discord import app_commands
from discord.ext import commands
import yt_dlp

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="join")
    async def join(self, interaction: discord.Interaction):
        vc = await interaction.user.voice.channel.connect()
        await interaction.response.send_message("已加入語音")

    @app_commands.command(name="play")
    async def play(self, interaction: discord.Interaction, url: str):
        vc = interaction.guild.voice_client

        ydl_opts = {'format': 'bestaudio'}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            url2 = info['url']

        vc.play(discord.FFmpegPCMAudio(url2))
        await interaction.response.send_message("播放中 🎵")

async def setup(bot):
    await bot.add_cog(Music(bot))
