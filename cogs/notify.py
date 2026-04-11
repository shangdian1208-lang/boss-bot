import discord
from discord.ext import commands, tasks
from discord import app_commands
import feedparser
import asyncio

from db import set_notify, get_notify


class Notify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_video = {}
        self.check_rss.start()

    # ================== 設定 ==================
    @app_commands.command(name="notify_set", description="設定發片通知")
    async def set_notify_cmd(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        channel_id: str,
        message: str = "🎬 新影片上傳！"
    ):

        rss = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

        set_notify(interaction.guild.id, channel.id, rss, message)

        await interaction.response.send_message("✅ 已儲存到資料庫")

    # ================== RSS 檢查 ==================
    @tasks.loop(seconds=60)
    async def check_rss(self):

        await self.bot.wait_until_ready()

        for guild_id, channel_id, rss, message in get_notify():

            feed = feedparser.parse(rss)

            if not feed.entries:
                continue

            latest = feed.entries[0]
            video_id = latest.yt_videoid

            if self.last_video.get(guild_id) == video_id:
                continue

            self.last_video[guild_id] = video_id

            channel = self.bot.get_channel(channel_id)
            if not channel:
                continue

            embed = discord.Embed(
                title="📢 新影片通知",
                description=f"**{latest.title}**\n\n{message}",
                url=latest.link,
                color=0xFF0000
            )

            await channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Notify(bot))
