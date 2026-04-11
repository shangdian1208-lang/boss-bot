import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import datetime

# ================== 記錄 log 設定（每個伺服器獨立） ==================
log_channels = {}

# ================== 🔒 關閉確認 UI ==================
class CloseConfirmView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=30)

    @discord.ui.button(label="✅ 確認關閉", style=discord.ButtonStyle.danger, emoji="🔒")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):

        channel = interaction.channel
        guild = interaction.guild

        await interaction.response.send_message("🔒 工單將在 5 秒後關閉...", ephemeral=True)

        # 🧾 LOG
        log_id = log_channels.get(guild.id)
        log = guild.get_channel(log_id) if log_id else None

        if log:
            embed = discord.Embed(
                title="📕 工單關閉",
                description=f"**{channel.name}** 已被關閉",
                color=0xED4245,
                timestamp=datetime.utcnow()
            )
            embed.set_footer(text=f"操作人：{interaction.user}")

            await log.send(embed=embed)

        await asyncio.sleep(5)
        await channel.delete()

    @discord.ui.button(label="❌ 取消", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("已取消關閉", ephemeral=True)


# ================== 🎫 工單按鈕 ==================
class TicketView(discord.ui.View):
    def __init__(self, category_name=None):
        super().__init__(timeout=None)
        self.category_name = category_name

    @discord.ui.button(label="📩 開啟工單", style=discord.ButtonStyle.green, emoji="🎫")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):

        guild = interaction.guild
        user = interaction.user

        # ❌ 防重複開單
        existing = discord.utils.get(guild.channels, name=f"ticket-{user.name}")
        if existing:
            return await interaction.response.send_message("❌ 你已經有工單了", ephemeral=True)

        # 📂 分類
        category = None
        if self.category_name:
            category = discord.utils.get(guild.categories, name=self.category_name)

        # 🔒 權限鎖
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        channel = await guild.create_text_channel(
            name=f"ticket-{user.name}",
            category=category,
            overwrites=overwrites
        )

        # 🎫 embed
        embed = discord.Embed(
            title="🎫 工單已建立",
            description="請詳細描述你的問題\n管理員會盡快處理",
            color=0x5865F2
        )

        await channel.send(embed=embed, view=TicketCloseView())

        await interaction.response.send_message(
            f"✅ 工單已建立：{channel.mention}",
            ephemeral=True
        )


# ================== 🔒 工單內關閉按鈕 ==================
class TicketCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 關閉工單", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.send_message(
            "⚠️ 確定要關閉工單嗎？",
            view=CloseConfirmView(),
            ephemeral=True
        )


# ================== 🎫 主 Cog ==================
class Ticket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ================== 發送面板 ==================
    @app_commands.command(name="ticket_panel", description="發送工單面板")
    @app_commands.checks.has_permissions(administrator=True)
    async def panel(
        self,
        interaction: discord.Interaction,
        title: str,
        description: str,
        category: str = None
    ):

        embed = discord.Embed(
            title=title,
            description=description,
            color=0x5865F2
        )
        embed.set_footer(text="點擊按鈕開啟工單")

        await interaction.channel.send(embed=embed, view=TicketView(category))

        await interaction.response.send_message("✅ 工單面板已建立", ephemeral=True)


    # ================== 設定 LOG ==================
    @app_commands.command(name="setlog", description="設定工單 log 頻道")
    @app_commands.checks.has_permissions(administrator=True)
    async def setlog(self, interaction: discord.Interaction, channel: discord.TextChannel):

        log_channels[interaction.guild.id] = channel.id

        await interaction.response.send_message(
            f"✅ 已設定 log 頻道：{channel.mention}",
            ephemeral=True
        )


# ================== setup ==================
async def setup(bot):
    await bot.add_cog(Ticket(bot))
