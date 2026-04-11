import discord
from discord.ext import commands
from utils.embed import success

class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="客服", emoji="📞"),
            discord.SelectOption(label="檢舉", emoji="🚨"),
            discord.SelectOption(label="合作", emoji="🤝"),
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

        await channel.send(embed=embed)

        await interaction.response.send_message(
            embed=success("成功", "你的工單已開啟"),
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
            description="請選擇你需要的服務類型",
            color=0x5865F2
        )

        await interaction.channel.send(embed=embed, view=TicketView())
        await interaction.response.send_message("已發送", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Ticket(bot))
