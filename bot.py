# bot.py
import discord, asyncio, os, random, json, youtube_dl, openai
from discord.ext import commands, tasks
from discord import app_commands
from discord.utils import get
from discord import FFmpegPCMAudio

# ===== 讀取環境變數 =====
TOKEN = os.getenv("TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
OPENAI_KEY = os.getenv("OPENAI_KEY")
openai.api_key = OPENAI_KEY

# ===== 資料庫 =====
DB_FILE = "db.json"
def read_db():
    if not os.path.exists(DB_FILE):
        return {"users": {}, "settings": {}, "logs": {}}
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
def write_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

db = read_db()

# ===== Bot 初始化 =====
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)

# ===== 同步 Slash 指令 =====
class MyBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

client = MyBot()

# ===== Bot 上線 =====
@client.event
async def on_ready():
    print(f"🤖 Bot 已上線: {client.user}")
    await client.tree.sync()

# ===== 進出訊息 =====
@client.event
async def on_member_join(member):
    ch_id = db["settings"].get("welcome")
    if ch_id:
        ch = client.get_channel(ch_id)
        if ch: await ch.send(f"👋 歡迎 {member.mention}！")

@client.event
async def on_member_remove(member):
    ch_id = db["settings"].get("leave")
    if ch_id:
        ch = client.get_channel(ch_id)
        if ch: await ch.send(f"😢 {member} 離開了伺服器！")

# ===== 指令 =====
@client.tree.command(name="ping", description="測試指令")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong!")

@client.tree.command(name="help", description="指令列表")
async def help_cmd(interaction: discord.Interaction):
    await interaction.response.send_message(
        "📜 指令: /daily /profile /rps /gacha /broadcast /play /stop /join /leave /set-ai-channel"
    )

# ===== 設定指令 (需管理員) =====
async def admin_set(interaction, key, ch: discord.TextChannel):
    db["settings"][key] = ch.id
    write_db(db)
    await interaction.response.send_message(f"✅ 設定 {key} 頻道完成: {ch.mention}")

@client.tree.command(name="set-welcome-channel", description="設定歡迎頻道")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(ch="頻道")
async def set_welcome(interaction: discord.Interaction, ch: discord.TextChannel):
    await admin_set(interaction, "welcome", ch)

@client.tree.command(name="set-leave-channel", description="設定離開頻道")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(ch="頻道")
async def set_leave(interaction: discord.Interaction, ch: discord.TextChannel):
    await admin_set(interaction, "leave", ch)

@client.tree.command(name="set-ai-channel", description="設定AI聊天頻道")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(ch="頻道")
async def set_ai(interaction: discord.Interaction, ch: discord.TextChannel):
    await admin_set(interaction, "ai", ch)

@client.tree.command(name="set-logs-channel", description="設定日誌頻道")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(ch="頻道")
async def set_logs(interaction: discord.Interaction, ch: discord.TextChannel):
    await admin_set(interaction, "logs", ch)

@client.tree.command(name="broadcast", description="全域公告")
@app_commands.describe(msg="訊息內容")
async def broadcast(interaction: discord.Interaction, msg: str):
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message("❌ 只有擁有者可用", ephemeral=True)
        return
    count = 0
    for guild in client.guilds:
        ch_id = db["settings"].get("announce")
        ch = client.get_channel(ch_id) if ch_id else get(guild.text_channels, permissions_synced=True)
        if ch:
            try:
                await ch.send(f"📢 全域公告\n{msg}")
                count += 1
            except:
                continue
    await interaction.response.send_message(f"✅ 發送成功 {count} 個伺服器")

# ===== 經濟系統 =====
@client.tree.command(name="daily", description="每日金幣")
async def daily(interaction: discord.Interaction):
    uid = str(interaction.user.id)
    if uid not in db["users"]:
        db["users"][uid] = {"money":100, "last":0}
    import time
    now = int(time.time())
    if now - db["users"][uid]["last"] < 86400:
        await interaction.response.send_message("今天已經領過了")
        return
    db["users"][uid]["money"] += 100
    db["users"][uid]["last"] = now
    write_db(db)
    await interaction.response.send_message("💰 領取 +100 金幣")

@client.tree.command(name="profile", description="查看個人資料")
async def profile(interaction: discord.Interaction):
    uid = str(interaction.user.id)
    user = db["users"].get(uid, {"money":100})
    await interaction.response.send_message(f"💰 {interaction.user.mention} 目前金幣: {user['money']}")

# ===== 遊戲系統 =====
@client.tree.command(name="rps", description="剪刀石頭布")
@app_commands.describe(choice="你的選擇")
@app_commands.choices(choice=[
    app_commands.Choice(name="石頭", value="rock"),
    app_commands.Choice(name="剪刀", value="scissors"),
    app_commands.Choice(name="布", value="paper")
])
async def rps(interaction: discord.Interaction, choice: str):
    uid = str(interaction.user.id)
    if uid not in db["users"]: db["users"][uid] = {"money":100,"last":0}
    cost = 30
    if db["users"][uid]["money"] < cost:
        await interaction.response.send_message("💸 金幣不足")
        return
    db["users"][uid]["money"] -= cost
    bot_choice = random.choice(["rock","paper","scissors"])
    result = "平手"
    if (choice=="rock" and bot_choice=="scissors") or (choice=="paper" and bot_choice=="rock") or (choice=="scissors" and bot_choice=="paper"):
        db["users"][uid]["money"] += 50
        result = "你贏了 +50"
    elif choice != bot_choice:
        db["users"][uid]["money"] -= 20
        result = "你輸了 -20"
    write_db(db)
    await interaction.response.send_message(f"你: {choice} Bot: {bot_choice}\n{result}")

@client.tree.command(name="gacha", description="扭蛋")
async def gacha(interaction: discord.Interaction):
    uid = str(interaction.user.id)
    if uid not in db["users"]: db["users"][uid] = {"money":100,"last":0}
    cost = 30
    if db["users"][uid]["money"] < cost:
        await interaction.response.send_message("💸 金幣不足")
        return
    db["users"][uid]["money"] -= cost
    n = random.randint(-100,100)
    db["users"][uid]["money"] += n
    write_db(db)
    await interaction.response.send_message(f"🎰 你扭出了 {n} 金幣")

# ===== AI聊天 =====
@client.event
async def on_message(message):
    if message.author.bot: return
    await client.process_commands(message)
    ai_ch = db["settings"].get("ai")
    if ai_ch and message.channel.id == ai_ch:
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role":"user","content":message.content}]
            )
            reply = response.choices[0].message.content
            await message.reply(reply)
        except Exception as e:
            print("AI Error:", e)

# ===== 音樂系統 =====
ytdl_opts = {'format':'bestaudio'}
ffmpeg_opts = {'before_options':'-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options':'-vn'}
voice_clients = {}

@client.tree.command(name="join", description="加入語音頻道")
async def join(interaction: discord.Interaction):
    if interaction.user.voice and interaction.user.voice.channel:
        channel = interaction.user.voice.channel
        vc = await channel.connect()
        voice_clients[interaction.guild_id] = vc
        await interaction.response.send_message(f"✅ 已加入 {channel.name}")
    else:
        await interaction.response.send_message("❌ 你不在語音頻道")

@client.tree.command(name="leave", description="離開語音頻道")
async def leave(interaction: discord.Interaction):
    vc = voice_clients.get(interaction.guild_id)
    if vc:
        await vc.disconnect()
        voice_clients.pop(interaction.guild_id)
        await interaction.response.send_message("✅ 已離開語音頻道")
    else:
        await interaction.response.send_message("❌ Bot 不在語音頻道")

@client.tree.command(name="play", description="播放 YouTube 音樂")
@app_commands.describe(url="YouTube 影片連結")
async def play(interaction: discord.Interaction, url: str):
    vc = voice_clients.get(interaction.guild_id)
    if not vc:
        await interaction.response.send_message("❌ Bot 不在語音頻道")
        return
    with youtube_dl.YoutubeDL(ytdl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        url2 = info['url']
    vc.play(FFmpegPCMAudio(url2, **ffmpeg_opts))
    await interaction.response.send_message(f"🎵 播放 {info['title']}")

@client.tree.command(name="stop", description="停止播放")
async def stop(interaction: discord.Interaction):
    vc = voice_clients.get(interaction.guild_id)
    if vc and vc.is_playing():
        vc.stop()
        await interaction.response.send_message("⏹ 停止播放")
    else:
        await interaction.response.send_message("❌ 沒有播放中")

# ===== 防炸 / 防刷 =====
@client.event
async def on_message_edit(before, after):
    if after.author.bot: return
    if "@everyone" in after.content:
        await after.delete()

# ===== 啟動 Bot =====
client.run(TOKEN)
