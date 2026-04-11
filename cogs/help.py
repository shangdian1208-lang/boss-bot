import discord
from discord.ext import commands
from discord import app_commands


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="顯示完整 Bot 指令總覽")
    async def help(self, interaction: discord.Interaction):

        embed = discord.Embed(
            title="🤖 Bot 指令總覽",
            description="以下是本機器人完整功能分類與使用方式",
            color=0x5865F2
        )

        # 🔧 管理系統
        embed.add_field(
            name="🔧 管理系統",
            value=(
                "📌 `/kick <user> [reason]`\n"
                "踢出伺服器成員\n\n"
                "📌 `/ban <user> [reason]`\n"
                "封鎖伺服器成員\n\n"
                "📌 `/timeout <user> [time]`\n"
                "暫時禁言成員（Timeout）"
            ),
            inline=False
        )

        # 📢 YouTube 通知（如果你有）
        embed.add_field(
            name="📢 YouTube 通知",
            value=(
                "📌 RSS 自動通知系統\n\n"
                "📌 `/notify_set`\n"
                "設定 YouTube 頻道發片通知\n"
                "👉 新影片會自動推播到指定頻道"
            ),
            inline=False
        )

        # 🎫 工單系統
        embed.add_field(
            name="🎫 工單系統",
            value=(
                "📌 `/ticket_panel`\n"
                "開啟工單面板（按鈕式）\n\n"
                "👉 功能：\n"
                "• 點擊建立私人工單頻道\n"
                "• 支援分類（Tickets Category）\n"
                "• 管理員可關閉工單"
            ),
            inline=False
        )

        # ✅ 驗證系統
        embed.add_field(
            name="✅ 驗證系統",
            value=(
                "📌 `/verify_panel`\n"
                "開啟驗證面板\n\n"
                "👉 功能：\n"
                "• 點擊按鈕驗證身份\n"
                "• 自動發放身分組\n"
                "• 防機器人/防未驗證用戶"
            ),
            inline=False
        )

        # 💾 系統工具
        embed.add_field(
            name="💾 系統工具",
            value=(
                "📌 `/backup`\n"
                "備份伺服器資料（角色 / 頻道 / 基本結構）\n\n"
                "📌 `/restore`\n"
                "還原伺服器備份資料（重建結構）\n\n"
                "📌 `/setlog`\n"
                "設定系統 Log 頻道（記錄管理行為）\n\n"
                "📌 `/help`\n"
                "顯示此指令列表"
            ),
            inline=False
        )

        # 📌 補充資訊
        embed.add_field(
            name="📌 系統說明",
            value=(
                "✔ Slash Commands 架構\n"
                "✔ SQLite / 本地資料儲存（若已啟用）\n"
                "✔ 按鈕 UI（Ticket / Verify）\n"
                "✔ 可擴充 Cog 模組化設計"
            ),
            inline=False
        )

        embed.set_footer(text="Xuan Bot System • Full Feature Edition")

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Help(bot))
