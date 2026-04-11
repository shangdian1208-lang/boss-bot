import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp

ffmpeg_options = {'options': '-vn'}

ytdl = yt_dlp.YoutubeDL({'format': 'bestaudio', 'noplaylist': True})


# ================== 🎛️ 控制面板 ==================
class MusicControlView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    # ⏸ 暫停
    @discord.ui.button(label="Pause", style=discord.ButtonStyle.secondary, emoji="⏸")
    async def pause(self, interaction: discord.Interaction, button: discord.ui.Button):

        vc = interaction.guild.voice_client
        if vc and vc.is_playing():
            vc.pause()
            await interaction.response.send_message("⏸ 已暫停", ephemeral=True)
        else:
            await interaction.response.send_message("❌ 沒有播放中", ephemeral=True)

    # ▶ 繼續
    @discord.ui.button(label="Resume", style=discord.ButtonStyle.success, emoji="▶")
    async def resume(self, interaction: discord.Interaction, button: discord.ui.Button):

        vc = interaction.guild.voice_client
        if vc and vc.is_paused():
            vc.resume()
            await interaction.response.send_message("▶ 已繼續", ephemeral=True)
        else:
            await interaction.response.send_message("❌ 沒有暫停", ephemeral=True)

    # ⏹ 停止 + 清空
    @discord.ui.button(label="Stop", style=discord.ButtonStyle.danger, emoji="⏹")
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):

        vc = interaction.guild.voice_client
        if vc:
            vc.stop()
            await interaction.response.send_message("⏹ 已停止", ephemeral=True)
        else:
            await interaction.response.send_message("❌ 沒有播放", ephemeral=True)

    # 🚪 離開
    @discord.ui.button(label="Leave", style=discord.ButtonStyle.red, emoji="🚪")
    async def leave(self, interaction: discord.Interaction, button: discord.ui.Button):

        vc = interaction.guild.voice_client
        if vc:
            await vc.disconnect()
            await interaction.response.send_message("🚪 已離開語音", ephemeral=True)
        else:
            await interaction.response.send_message("❌ 我不在語音", ephemeral=True)

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="play", description="播放 YouTube 音樂")
    async def play(self, interaction: discord.Interaction, url: str):

        await interaction.response.defer()

        vc = interaction.guild.voice_client

        # 自動加入語音
        if not vc:
            if interaction.user.voice:
                vc = await interaction.user.voice.channel.connect()
            else:
                return await interaction.followup.send("❌ 你不在語音頻道")

        # 解析音樂
        info = ytdl.extract_info(url, download=False)
        audio_url = info["url"]
        title = info.get("title", "Unknown")

        # 停止舊音樂
        if vc.is_playing():
            vc.stop()

        vc.play(discord.FFmpegPCMAudio(audio_url, **ffmpeg_options))

        # 🎨 Embed UI
        embed = discord.Embed(
            title="🎵 正在播放",
            description=f"**{title}**",
            color=0x5865F2
        )
        embed.add_field(name="🔗 連結", value=url, inline=False)
        embed.set_footer(text=f"請求者：{interaction.user}")

        await interaction.followup.send(
            embed=embed,
            view=MusicControlView(self.bot)  # 🎛️ 控制面板
        )


