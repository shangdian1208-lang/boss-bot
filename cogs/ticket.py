import discord
from discord.ext import commands

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__()

    @discord.ui.select(
        placeholder="選擇工單類型",
        options=[
            discord.SelectOption(label="客服"),
            discord.SelectOption(label="檢舉"),
        ]
    )
    async def select(self, interaction: discord.Interaction, select: discord.ui.Select):
        category = discord.utils.get(interaction.guild.categories, name=select.values[0])

        channel = await interaction.guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            category=category
        )

        await channel.send(f"{interaction.user.mention} 已建立工單")
        await interaction.response.send_message("已開啟工單", ephemeral=True)

class Ticket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="ticketpanel")
    async def ticketpanel(self, interaction: discord.Interaction):
        await interaction.channel.send("選擇工單類型", view=TicketView())
        await interaction.response.send_message("已發送", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Ticket(bot))
