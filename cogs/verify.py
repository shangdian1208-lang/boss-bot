import discord
from discord.ext import commands
from discord import app_commands
from utils.embed import success

class VerifyView(discord.ui.View):
    def __init__(self, role):
        super().__init__(timeout=None)
        self.role = role

    @discord.ui.button(label="點擊驗證", emoji="✅", style=discord.ButtonStyle.green)
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.user.add_roles(self.role)

        await interaction.response.send_message(
            embed=success("驗證成功", f"你已獲得 {self.role.mention}"),
            ephemeral=True
        )

class Verify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="verify_panel", description="發送驗證面板")
    async def verify_panel(self, interaction: discord.Interaction, role: discord.Role):
        embed = discord.Embed(
            title="🔒 伺服器驗證",
            description="點擊下方按鈕完成驗證\n\n> 保護伺服器免受機器人攻擊",
            color=0x5865F2
        )
        embed.set_footer(text="Verification System")

        await interaction.channel.send(embed=embed, view=VerifyView(role))
        await interaction.response.send_message("已發送驗證面板", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Verify(bot))
