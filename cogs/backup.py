import discord
from discord.ext import commands
from discord import app_commands
import json

class Backup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="backup", description="備份伺服器")
    async def backup(self, interaction: discord.Interaction):

        guild = interaction.guild

        data = {
            "roles": [],
            "channels": [],
            "categories": []
        }

        # 📦 身分組
        for role in guild.roles:
            data["roles"].append({
                "name": role.name,
                "permissions": role.permissions.value
            })

        # 📂 類別
        for cat in guild.categories:
            data["categories"].append(cat.name)

        # 📁 頻道
        for ch in guild.channels:
            data["channels"].append({
                "name": ch.name,
                "type": str(ch.type),
                "category": ch.category.name if ch.category else None
            })

        file_name = f"{guild.id}_backup.json"

        with open(file_name, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        await interaction.response.send_message(
            f"💾 備份完成：{file_name}",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(Backup(bot))
