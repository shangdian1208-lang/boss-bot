import discord
from discord.ext import commands, tasks
from discord import app_commands
import feedparser
import asyncio


class Notify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = {}  # guild 設定
        self.last_video = {}
        self.check_rss.start()

    # ================== 設定發送頻道 ==================
    @app_commands.command(name="notify_set_channel", description="設定通知發送頻道")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):

        gid = interaction.guild.id
        self.data.setdefault(gid, {})
        self.data[gid]["channel"] = channel.id

        await interaction.response.send_message(f"✅ 已設定通知頻道：{channel.mention}")

    # ================== 設定 RSS ==================
    @app_commands.command(name="notify_set_rss", description="設定 YouTube RSS")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_rss(self, interaction: discord.Interaction, channel_id: str):

        gid = interaction.guild.id
        self.data.setdefault(gid, {})
        self.data[gid]["rss"] = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

        await interaction.response.send_message("✅ RSS 已設定")

    # ================== 自訂訊息 ==================
    @app_commands.command(name="notify_set_message", description="自訂發片訊息")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_message(self, interaction: discord.Interaction, message: str):

        gid = interaction.guild.id
        self.data.setdefault(gid, {})
        self.data[gid]["message"] = message

        await interaction.response.send_message("✅ 訊息已設定")

    # ================== RSS 偵測 ==================
    @tasks.loop(seconds=60)
    async def check_rss(self):

        await self.bot.wait_until_ready()

        for guild_id, cfg in self.data.items():

            if "rss" not in cfg or "channel" not in cfg:
                continue

            feed = feedparser.parse(cfg["rss"])

            if not feed.entries:
                continue

            latest = feed.entries[0]
            video_id = latest.yt_videoid

            # 避免重複通知
            if self.last_video.get(guild_id) == video_id:
                continue

            self.last_video[guild_id] = video_id

            channel = self.bot.get_channel(cfg["channel"])
            if not channel:
                continue

            title = latest.title
            url = latest.link

            msg = cfg.get("message", "🎬 新影片上傳！")

            embed = discord.Embed(
                title="📢 新影片通知",
                description=f"**{title}**\n\n{msg}",
                url=url,
                color=0xFF0000
            )

            await channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Notify(bot))
