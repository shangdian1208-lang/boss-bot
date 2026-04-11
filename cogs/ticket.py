import discord
from discord.ext import commands

# ================== 關閉確認 UI ==================

class ConfirmCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=30)

    @discord.ui.button(label="確認關閉", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.send_message("⏳ 正在關閉工單...", ephemeral=True)

        await interaction.channel.send("🔒 工單將在 5 秒後關閉...")
        await discord.utils.sleep_until(discord.utils.utcnow() + discord.timedelta(seconds=5))

        await interaction.channel.delete()

    @discord.ui.button(label="取消", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("❌ 已取消關閉", ephemeral=True)


# ================== 工單關閉按鈕 ==================

class CloseButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="關閉工單", style=discord.ButtonStyle.danger, emoji="🔒")
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.send_message(
            "⚠️ 確定要關閉這個工單嗎？",
            view=ConfirmCloseView(),
            ephemeral=True
        )


# ================== 工單建立 ==================

class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="客服", emoji="📞"),
            discord.SelectOption(label="檢舉", emoji="🚨"),
        ]
        super().__init__(placeholder="選擇工單類型", options=options)

    async def callback(self, interaction: discord.Interaction):
        category = discord.utils.get(
            interaction.guild.categories,
            name=self.values[0]
        )

        channel = await interaction.guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            category=category
        )

        embed = discord.Embed(
            title="🎫 工單已建立",
            description=f"{interaction.user.mention} 請描述你的問題",
            color=0x5865F2
        )

        await channel.send(embed=embed, view=CloseButton())

        await interaction.response.send_message(
            "✅ 工單已建立",
            ephemeral=True
        )


class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())


class Ticket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="ticket_panel")
    async def panel(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎫 客服中心",
            description="請選擇工單類型",
            color=0x5865F2
        )

        await interaction.channel.send(embed=embed, view=TicketView())
        await interaction.response.send_message("已發送", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Ticket(bot))
