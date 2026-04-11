import discord
from discord.ext import commands
from discord import app_commands
import json
import io

class Backup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ================== 💾 備份 ==================
    @app_commands.command(name="backup", description="下載伺服器備份")
    @app_commands.checks.has_permissions(administrator=True)
    async def backup(self, interaction: discord.Interaction):

        guild = interaction.guild

        data = {
            "roles": [],
            "categories": [],
            "channels": []
        }

        # roles
        for role in guild.roles:
            if role.name != "@everyone":
                data["roles"].append({
                    "name": role.name,
                    "permissions": role.permissions.value
                })

        # categories
        for cat in guild.categories:
            data["categories"].append(cat.name)

        # channels
        for ch in guild.channels:
            data["channels"].append({
                "name": ch.name,
                "type": str(ch.type),
                "category": ch.category.name if ch.category else None
            })

        json_data = json.dumps(data, indent=4, ensure_ascii=False)

        file = discord.File(
            io.BytesIO(json_data.encode()),
            filename=f"{guild.id}_backup.json"
        )

        await interaction.response.send_message(
            "💾 備份完成（點擊下載）",
            file=file,
            ephemeral=True
        )

    # ================== 🔄 還原 ==================
    @app_commands.command(name="restore", description="上傳備份還原伺服器")
    @app_commands.checks.has_permissions(administrator=True)
    async def restore(self, interaction: discord.Interaction, file: discord.Attachment):

        await interaction.response.send_message("⚠️ 正在還原...", ephemeral=True)

        content = await file.read()
        data = json.loads(content)

        guild = interaction.guild

        # 建立分類
        category_map = {}
        for cat_name in data["categories"]:
            cat = await guild.create_category(cat_name)
            category_map[cat_name] = cat

        # 建立角色
        for role_data in data["roles"]:
            await guild.create_role(
                name=role_data["name"],
                permissions=discord.Permissions(role_data["permissions"])
            )

        # 建立頻道
        for ch in data["channels"]:
            category = category_map.get(ch["category"])

            if "text" in ch["type"]:
                await guild.create_text_channel(ch["name"], category=category)
            elif "voice" in ch["type"]:
                await guild.create_voice_channel(ch["name"], category=category)

        await interaction.followup.send("✅ 還原完成")

async def setup(bot):
    await bot.add_cog(Backup(bot))
