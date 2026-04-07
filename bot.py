import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import os
from database import *
from views import *

TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = os.getenv("PREFIX", "!")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents)
tree = bot.tree

# ===== 啟動 =====
@bot.event
async def setup_hook():
    await init_db()
    bot.add_view(RoleView())
    bot.add_view(TicketView())
    bot.add_view(CloseTicketView())
    await tree.sync()

@bot.event
async def on_ready():
    print(f"✅ 已登入 {bot.user}")

# AI
HF_API_KEY = os.getenv("HF_API_KEY")

API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"

headers = {
    "Authorization": f"Bearer {HF_API_KEY}"
}

async def query_hf(prompt):
    async with aiohttp.ClientSession() as session:
        async with session.post(API_URL, headers=headers, json={
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 200,
                "temperature": 0.7
            }
        }) as response:
            result = await response.json()

            if isinstance(result, list):
                return result[0]["generated_text"]
            else:
                return "❌ AI 發生錯誤"

# =========================
# 🔹 Slash Commands
# =========================

@tree.command(name="設置日誌頻道")
async def set_log(interaction: discord.Interaction, channel: discord.TextChannel):
    await set_setting(interaction.guild.id, "log_channel", channel.id)
    await interaction.response.send_message("✅ 設置完成")

@tree.command(name="身份組按鈕")
async def role_panel(interaction: discord.Interaction):
    await interaction.channel.send("領取身分組", view=RoleView())
    await interaction.response.send_message("✅ 已發送", ephemeral=True)

@tree.command(name="設置工單功能")
async def ticket_setup(interaction: discord.Interaction, category: discord.CategoryChannel, log: discord.TextChannel):
    await set_setting(interaction.guild.id, "ticket_category", category.id)
    await set_setting(interaction.guild.id, "ticket_log", log.id)
    await interaction.response.send_message("✅ 工單設定完成")

@tree.command(name="設置工單頻道")
async def ticket_panel(interaction: discord.Interaction):
    await interaction.channel.send("🎫 點擊開啟工單", view=TicketView())
    await interaction.response.send_message("✅ 已發送", ephemeral=True)

@tree.command(name="人數頻道創建")
async def count_create(interaction: discord.Interaction):
    channel = await interaction.guild.create_voice_channel("👥人數: 0")
    await set_setting(interaction.guild.id, "count_channel", channel.id)
    await interaction.response.send_message("✅ 已建立")

@tree.command(name="移除人數頻道")
async def count_remove(interaction: discord.Interaction):
    cid = await get_setting(interaction.guild.id, "count_channel")
    ch = interaction.guild.get_channel(cid)
    if ch:
        await ch.delete()
    await interaction.response.send_message("✅ 已移除")

@tree.command(name="ai問答", description="AI聊天")
async def ai(interaction: discord.Interaction, 問題: str):
    await interaction.response.defer()

    reply = await query_hf(f"使用繁體中文回答：{問題}")

    # 避免超過2000字
    if len(reply) > 2000:
        reply = reply[:1990] + "..."

    await interaction.followup.send(reply)
# =========================
# 🔸 Prefix Commands
# =========================

@bot.command()
async def ping(ctx):
    await ctx.send(f"{round(bot.latency*1000)}ms")

@bot.command()
async def kick(ctx, member: discord.Member, *, reason="無"):
    await member.kick(reason=reason)
    await ctx.send("已踢出")

@bot.command()
async def ban(ctx, member: discord.Member, *, reason="無"):
    await member.ban(reason=reason)
    await ctx.send("已封鎖")

@bot.command()
async def unban(ctx, user_id: int):
    user = await bot.fetch_user(user_id)
    await ctx.guild.unban(user)
    await ctx.send("已解封")

@bot.command()
async def to(ctx, member: discord.Member, seconds: int):
    await member.timeout(discord.utils.utcnow() + discord.timedelta(seconds=seconds))
    await ctx.send("已禁言")

@bot.command()
async def unto(ctx, member: discord.Member):
    await member.timeout(None)
    await ctx.send("已解除禁言")

# =========================
# 📊 人數更新
# =========================

@bot.event
async def on_member_join(member):
    await update_count(member.guild)

@bot.event
async def on_member_remove(member):
    await update_count(member.guild)

async def update_count(guild):
    cid = await get_setting(guild.id, "count_channel")
    ch = guild.get_channel(cid)
    if ch:
        await ch.edit(name=f"👥人數: {guild.member_count}")

# AI
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if bot.user in message.mentions:
        try:
            # ✨ 顯示輸入中（很重要，體驗差很多）
            async with message.channel.typing():

                # ✅ 移除 mention
                content = message.content.replace(f"<@{bot.user.id}>", "").strip()

                if not content:
                    await message.reply("你要問什麼？")
                    return

                # 🧠 AI Prompt（強化）
                prompt = f"""
你是一個Discord伺服器的智能助理，請用繁體中文自然回答。
語氣可以輕鬆一點，但不要太隨便。

使用者說：
{content}
"""

                reply = await query_hf(prompt)

                # ✂️ 避免過長
                reply = reply.strip()
                if len(reply) > 2000:
                    reply = reply[:1990] + "..."

                await message.reply(reply)

        except Exception as e:
            await message.reply("⚠️ AI暫時壞掉了，稍後再試")
            print("AI錯誤:", e)

    await bot.process_commands(message)
# =========================

bot.run(TOKEN)
