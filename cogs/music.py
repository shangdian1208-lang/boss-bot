import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import asyncio


ffmpeg_options = {'options': '-vn'}

ytdl = yt_dlp.YoutubeDL({
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'extractor_args': {
        'youtube': {
            'skip': ['dash', 'hls']
        }
    }
})


# ================== 🎛️ 控制面板 ==================
class MusicControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Pause", style=discord.ButtonStyle.secondary, emoji="⏸")
    async def pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if vc and vc.is_playing():
            vc.pause()
            await interaction.response.send_message("⏸ 已暫停", ephemeral=True)
        else:
            await interaction.response.send_message("❌ 沒有播放", ephemeral=True)

    @discord.ui.button(label="Resume", style=discord.ButtonStyle.success, emoji="▶")
    async def resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if vc and vc.is_paused():
            vc.resume()
            await interaction.response.send_message("▶ 已繼續", ephemeral=True)
        else:
            await interaction.response.send_message("❌ 沒有暫停", ephemeral=True)

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.danger, emoji="⏹")
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if vc:
            vc.stop()
            await interaction.response.send_message("⏹ 已停止", ephemeral=True)
        else:
            await interaction.response.send_message("❌ 沒有播放", ephemeral=True)

    @discord.ui.button(label="Leave", style=discord.ButtonStyle.red, emoji="🚪")
    async def leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if vc:
            await vc.disconnect()
            await interaction.response.send_message("🚪 已離開語音", ephemeral=True)
        else:
            await interaction.response.send_message("❌ 不在語音", ephemeral=True)


# ================== 🎵 Music Cog ==================
class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="play", description="播放音樂（支援搜尋）")
    async def play(self, interaction: discord.Interaction, query: str):
        
        info = await asyncio.wait_for(
        asyncio.to_thread(ytdl.extract_info, query, False),
        timeout=10
    )

        await interaction.response.defer()

        vc = interaction.guild.voice_client

        # 🔊 自動加入語音
        if not vc:
            if interaction.user.voice:
                vc = await interaction.user.voice.channel.connect()
            else:
                return await interaction.followup.send("❌ 你不在語音頻道")

        # 🔍 搜尋模式
        if not query.startswith("http"):
            query = f"ytsearch1:{query}"

        info = ytdl.extract_info(query, download=False)

        if "entries" in info:
            info = info["entries"][0]

        audio_url = info["url"]
        title = info.get("title", "Unknown")
        webpage_url = info.get("webpage_url")

        if vc.is_playing():
            vc.stop()

        vc.play(discord.FFmpegPCMAudio(audio_url, **ffmpeg_options))

        embed = discord.Embed(
            title="🎵 正在播放",
            description=title,
            color=0x5865F2
        )

        if webpage_url:
            embed.add_field(name="🔗 YouTube", value=webpage_url, inline=False)

        await interaction.followup.send(
            embed=embed,
            view=MusicControlView()
        )



# ================== setup ==================
async def setup(bot):
    await bot.add_cog(Music(bot))

