import discord
from discord.ext import commands
from discord import app_commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="查看指令")
    async def help(self, interaction: discord.Interaction):

        embed = discord.Embed(
            title="🤖 Bot 指令總覽",
            description="選擇你需要的功能",
            color=0x5865F2
        )

        embed.add_field(
            name="🔧 管理",
            value="`/kick` `/ban` `/timeout`",
            inline=False
        )

        embed.add_field(
            name="🎵 音樂",
            value="`/join` `/play` `/leave`",
            inline=False
        )

        embed.add_field(
            name="🎫 工單",
            value="`/ticket_panel`",
            inline=False
        )

        embed.add_field(
            name="✅ 驗證",
            value="`/verify_panel`",
            inline=False
        )

        embed.add_field(
            name="💾 系統",
            value="`/backup` `/help`",
            inline=False
        )

        embed.set_footer(text="Xuan Bot 系統")

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Help(bot))
