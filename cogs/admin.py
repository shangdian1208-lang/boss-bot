import discord
from discord.ext import commands
from discord import app_commands
import datetime

WHITELIST = [1442017307332182168]  # 填入你的ID避免被誤判

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ================== 🔧 權限檢查 ==================
    def is_admin(interaction: discord.Interaction):
        return interaction.user.guild_permissions.administrator

    # ================== 👢 Kick ==================
    @app_commands.command(name="kick", description="踢出成員")
    @app_commands.check(is_admin)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "無原因"):
        await member.kick(reason=reason)
        await interaction.response.send_message(f"👢 已踢出 {member} | 原因：{reason}")

    # ================== 🔨 Ban ==================
    @app_commands.command(name="ban", description="封鎖成員")
    @app_commands.check(is_admin)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "無原因"):
        await member.ban(reason=reason)
        await interaction.response.send_message(f"🔨 已封鎖 {member} | 原因：{reason}")

    # ================== ⏱️ Timeout（禁言） ==================
    @app_commands.command(name="timeout", description="禁言成員")
    @app_commands.check(is_admin)
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str = "無原因"):
        duration = datetime.timedelta(minutes=minutes)
        await member.timeout(duration, reason=reason)

        await interaction.response.send_message(
            f"⏱️ {member} 已被禁言 {minutes} 分鐘 | 原因：{reason}"
        )

    # ================== 🧾 LOG ==================
    async def log(self, guild, message):
        channel = discord.utils.get(guild.text_channels, name="log")
        if channel:
            await channel.send(message)

    # ================== 🔥 防炸系統 ==================
    async def punish(self, guild, user, action):
        if user.id in WHITELIST:
            return

        try:
            await user.ban(reason=f"防炸系統：{action}")
            await self.log(guild, f"🚨 {user} 因 {action} 被封鎖")
        except:
            pass

    # 📛 刪頻道
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        async for entry in channel.guild.audit_logs(limit=1):
            await self.punish(channel.guild, entry.user, "刪除頻道")

    # 📛 刪角色
    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        async for entry in role.guild.audit_logs(limit=1):
            await self.punish(role.guild, entry.user, "刪除角色")

    # 📛 改權限
    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        if before.permissions != after.permissions:
            async for entry in after.guild.audit_logs(limit=1):
                await self.punish(after.guild, entry.user, "亂改權限")

async def setup(bot):
    await bot.add_cog(Admin(bot))
