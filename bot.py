import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
from google import genai
import time
import os
import json
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
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

async def query_ai(prompt):
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        return response.text

    except Exception as e:
        print("Gemini錯誤:", e)
        return "❌ AI 暫時無法回應"
# =========================
# 🔹 Slash Commands
# =========================

@tree.command(
    name="設置日誌頻道",
    description="設定機器人紀錄伺服器事件的頻道"
)
async def set_log(interaction: discord.Interaction, channel: discord.TextChannel):
    await set_setting(interaction.guild.id, "log_channel", channel.id)
    await interaction.response.send_message("✅ 設置完成")

@tree.command(
    name="身份組按鈕",
    description="建立一個讓成員領取身分組的按鈕面板"
)
async def role_panel(interaction: discord.Interaction):
    await interaction.channel.send("領取身分組", view=RoleView())
    await interaction.response.send_message("✅ 已發送", ephemeral=True)

@tree.command(
    name="設置工單功能",
    description="設定工單系統的分類與紀錄頻道"
)
async def ticket_setup(interaction: discord.Interaction, category: discord.CategoryChannel, log: discord.TextChannel):
    await set_setting(interaction.guild.id, "ticket_category", category.id)
    await set_setting(interaction.guild.id, "ticket_log", log.id)
    await interaction.response.send_message("✅ 工單設定完成")

@tree.command(
    name="設置工單頻道",
    description="在此頻道發送工單開啟按鈕"
)
async def ticket_panel(interaction: discord.Interaction):
    await interaction.channel.send("🎫 點擊開啟工單", view=TicketView())
    await interaction.response.send_message("✅ 已發送", ephemeral=True)

@tree.command(
    name="人數頻道創建",
    description="建立顯示伺服器人數的語音頻道"
)
async def count_create(interaction: discord.Interaction):
    channel = await interaction.guild.create_voice_channel("👥人數: 0")
    await set_setting(interaction.guild.id, "count_channel", channel.id)
    await interaction.response.send_message("✅ 已建立")

@tree.command(
    name="移除人數頻道",
    description="刪除目前的人數統計頻道"
)
async def count_remove(interaction: discord.Interaction):
    cid = await get_setting(interaction.guild.id, "count_channel")
    ch = interaction.guild.get_channel(cid)
    if ch:
        await ch.delete()
    await interaction.response.send_message("✅ 已移除")

@tree.command(name="ai問答", description="向 AI 提問")
@app_commands.describe(問題="你想問 AI 的內容")
async def ai(interaction: discord.Interaction, 問題: str):
    await interaction.response.defer()

    reply = await query_ai(f"請用繁體中文回答：{問題}")

    if len(reply) > 2000:
        reply = reply[:1990] + "..."

    await interaction.followup.send(reply)

# /help
@tree.command(name="help", description="顯示所有指令")
async def help_cmd(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📖 指令幫助",
        description="這裡是所有可用指令",
        color=discord.Color.blurple()
    )

    # 🔹 斜線指令
    embed.add_field(
        name="🔹 斜線指令 (/)",
        value=(
            "`/身份組按鈕` - 建立身分組按鈕\n"
            "`/設置日誌頻道` - 設置日誌頻道\n"
            "`/設置工單功能` - 設置工單分類與日誌\n"
            "`/設置工單頻道` - 發送工單按鈕\n"
            "`/人數頻道創建` - 建立人數頻道\n"
            "`/移除人數頻道` - 移除人數頻道\n"
            "`/ai問答` - 問 AI 問題"
        ),
        inline=False
    )

    # 🔸 管理指令
    embed.add_field(
        name="🔸 管理指令 (!)",
        value=(
            "`!ping` - 測試延遲\n"
            "`!ban @用戶 [原因]` - 封鎖用戶\n"
            "`!kick @用戶 [原因]` - 踢出用戶\n"
            "`!unban [ID]` - 解封\n"
            "`!to @用戶 [秒數]` - 禁言\n"
            "`!unto @用戶` - 解除禁言"
        ),
        inline=False
    )

    # 🤖 AI
    embed.add_field(
        name="🤖 AI 功能",
        value=(
            "📌 `@機器人 訊息` → 自動回覆\n"
            "📌 `/ai問答` → 指令提問"
        ),
        inline=False
    )

    embed.set_footer(text="💡 提示：可以直接 @我 來聊天！")
    embed.set_thumbnail(url=interaction.client.user.avatar.url if interaction.client.user.avatar else None)

    await interaction.response.send_message(embed=embed, ephemeral=True)
# =========================
# 🔸 Prefix Commands
# =========================

@bot.command()
async def ping(ctx):
    await ctx.send(f"{round(bot.latency*1000)}ms")

@bot.command()
async def kick(ctx, member: discord.Member, *, reason="無"):
    await log_kick(ctx.guild, ctx.author, member, reason)
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
            content = message.content.replace(f"<@{bot.user.id}>", "").strip()

            if not content:
                await message.reply("你要問什麼？")
                return

            reply = await query_ai(f"請用繁體中文自然回答：{content}")

            await message.reply(reply[:2000])

        except Exception as e:
            print(e)
            await message.reply("❌ AI 出錯了")

    await bot.process_commands(message)

# 🔍 取得 log 頻道
log_channels = {}  # guild_id: channel_id

def get_log_channel(guild):
    channel_id = log_channels.get(guild.id)
    if channel_id:
        return guild.get_channel(channel_id)
    return None


# =========================
# 🗑️ 訊息刪除
# =========================
@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return

    log_channel = get_log_channel(message.guild)
    if not log_channel:
        return

    embed = discord.Embed(title="🗑️ 訊息被刪除", color=discord.Color.red())
    embed.add_field(name="使用者", value=message.author.mention)
    embed.add_field(name="頻道", value=message.channel.mention)
    embed.add_field(name="內容", value=message.content or "無內容", inline=False)

    await log_channel.send(embed=embed)


# =========================
# ✏️ 訊息編輯
# =========================
@bot.event
async def on_message_edit(before, after):
    if before.author.bot:
        return
    if before.content == after.content:
        return

    log_channel = get_log_channel(before.guild)
    if not log_channel:
        return

    embed = discord.Embed(title="✏️ 訊息被編輯", color=discord.Color.orange())
    embed.add_field(name="使用者", value=before.author.mention)
    embed.add_field(name="修改前", value=before.content or "無", inline=False)
    embed.add_field(name="修改後", value=after.content or "無", inline=False)

    await log_channel.send(embed=embed)


# =========================
# 👤 成員加入
# =========================
@bot.event
async def on_member_join(member):
    log_channel = get_log_channel(member.guild)
    if not log_channel:
        return

    embed = discord.Embed(title="👤 成員加入", color=discord.Color.green())
    embed.add_field(name="使用者", value=member.mention)
    embed.add_field(name="ID", value=member.id)

    await log_channel.send(embed=embed)


# =========================
# 🚪 成員離開
# =========================
@bot.event
async def on_member_remove(member):
    log_channel = get_log_channel(member.guild)
    if not log_channel:
        return

    embed = discord.Embed(title="🚪 成員離開", color=discord.Color.dark_gray())
    embed.add_field(name="使用者", value=member.mention)

    await log_channel.send(embed=embed)


# =========================
# 🔨 Ban
# =========================
@bot.event
async def on_member_ban(guild, user):
    log_channel = get_log_channel(guild)
    if not log_channel:
        return

    embed = discord.Embed(title="🔨 成員被封鎖", color=discord.Color.red())
    embed.add_field(name="用戶", value=f"{user} ({user.id})")

    await log_channel.send(embed=embed)


# =========================
# 👢 Kick（需要在你的 !kick 指令內加）
# =========================
async def log_kick(guild, moderator, target, reason):
    log_channel = get_log_channel(guild)
    if not log_channel:
        return

    embed = discord.Embed(title="👢 成員被踢出", color=discord.Color.orange())
    embed.add_field(name="管理員", value=moderator.mention)
    embed.add_field(name="目標", value=target.mention)
    embed.add_field(name="原因", value=reason or "無")

    await log_channel.send(embed=embed)


# =========================
# 🏷️ 身分組變動
# =========================
@bot.event
async def on_member_update(before, after):
    log_channel = get_log_channel(before.guild)
    if not log_channel:
        return

    before_roles = set(before.roles)
    after_roles = set(after.roles)

    added = after_roles - before_roles
    removed = before_roles - after_roles

    if not added and not removed:
        return

    embed = discord.Embed(title="🏷️ 身分組變動", color=discord.Color.blue())
    embed.add_field(name="使用者", value=after.mention)

    if added:
        embed.add_field(name="新增", value=", ".join(r.name for r in added), inline=False)
    if removed:
        embed.add_field(name="移除", value=", ".join(r.name for r in removed), inline=False)

    await log_channel.send(embed=embed)


# =========================
# 🎤 語音狀態
# =========================
@bot.event
async def on_voice_state_update(member, before, after):
    log_channel = get_log_channel(member.guild)
    if not log_channel:
        return

    if before.channel == after.channel:
        return

    embed = discord.Embed(color=discord.Color.purple())
    embed.add_field(name="使用者", value=member.mention)

    if before.channel is None:
        embed.title = "🎤 加入語音"
        embed.add_field(name="頻道", value=after.channel.name)

    elif after.channel is None:
        embed.title = "🔇 離開語音"
        embed.add_field(name="頻道", value=before.channel.name)

    else:
        embed.title = "🔁 切換語音"
        embed.add_field(name="從", value=before.channel.name)
        embed.add_field(name="到", value=after.channel.name)

    await log_channel.send(embed=embed)
# =========================

bot.run(TOKEN)
