import discord, os, json, random, asyncio, yt_dlp
from discord.ext import commands, tasks
from discord import app_commands

# -----------------------------
# 環境變數
# -----------------------------
TOKEN = os.getenv("DISCORD_TOKEN")
HF_API = os.getenv("HF_API_KEY")
OWNER_ID = int(os.getenv("OWNER_ID", "1442017307332182168"))

# -----------------------------
# Bot 初始化
# -----------------------------
intents = discord.Intents.all()
client = commands.Bot(command_prefix="/", intents=intents)
client.remove_command("help")

# -----------------------------
# 資料庫
# -----------------------------
if not os.path.exists("db.json"):
    with open("db.json","w") as f:
        json.dump({
            "settings":{}, "exp":{}, "money":{}, "ai_history":{}
        }, f, indent=4)

def load_db():
    with open("db.json","r") as f:
        return json.load(f)

def save_db(data):
    with open("db.json","w") as f:
        json.dump(data, f, indent=4)

db = load_db()

# -----------------------------
# AI 回覆
# -----------------------------
HF_MODEL = "gpt-neo-2.7B"

async def ai_reply(message):
    try:
        db = load_db()
        history = db.get("ai_history", {})
        context = history.get(str(message.channel.id), [])
        context.append(f"User: {message.content}")
        prompt = "\n".join(context[-3:]) + "\nAI:"
        import requests
        headers = {"Authorization": f"Bearer {HF_API}"}
        payload = {"inputs": prompt, "options":{"use_cache":False,"wait_for_model":True}}
        res = requests.post(f"https://api-inference.huggingface.co/models/{HF_MODEL}", headers=headers, json=payload, timeout=30)
        data = res.json()
        reply = data[0].get("generated_text","🤖 AI 無法回覆") if isinstance(data,list) else data.get("generated_text","🤖 AI 無法回覆")
        context.append(f"AI: {reply}")
        db["ai_history"][str(message.channel.id)] = context[-6:]
        save_db(db)
        await message.reply(reply)
    except Exception as e:
        print("HF AI Error:", e)
        await message.reply("⚠️ AI 暫時不可用")

# -----------------------------
# 歡迎/離開訊息
# -----------------------------
@client.event
async def on_member_join(member):
    db = load_db()
    chan_id = db.get("settings", {}).get(str(member.guild.id), {}).get("welcome")
    if chan_id:
        ch = member.guild.get_channel(chan_id)
        if ch:
            await ch.send(f"🎉 歡迎 {member.mention} 加入 {member.guild.name}!")

@client.event
async def on_member_remove(member):
    db = load_db()
    chan_id = db.get("settings", {}).get(str(member.guild.id), {}).get("leave")
    if chan_id:
        ch = member.guild.get_channel(chan_id)
        if ch:
            await ch.send(f"👋 {member.name} 離開了 {member.guild.name}.")

# -----------------------------
# 等級系統
# -----------------------------
@client.event
async def on_message(msg):
    if msg.author.bot:
        return
    db = load_db()
    uid = str(msg.author.id)
    db["exp"][uid] = db.get("exp", {}).get(uid, 0) + random.randint(1,5)
    db["money"][uid] = db.get("money", {}).get(uid, 100)  # 初始金幣 100
    save_db(db)
    # AI 回覆
    if db.get("settings", {}).get(str(msg.guild.id), {}).get("ai") == msg.channel.id:
        await ai_reply(msg)
    await client.process_commands(msg)

@client.tree.command(name="profile", description="查看個人經驗值和金幣")
async def profile(interaction: discord.Interaction):
    uid = str(interaction.user.id)
    db = load_db()
    exp = db.get("exp", {}).get(uid, 0)
    money = db.get("money", {}).get(uid, 100)
    await interaction.response.send_message(f"📊 {interaction.user.mention}\n經驗值: {exp}\n金幣: {money}", ephemeral=True)
    # -----------------------------
# 身分組領取按鈕
# -----------------------------
class RoleButton(discord.ui.View):
    def __init__(self, role: discord.Role):
        super().__init__(timeout=None)
        self.role = role

    @discord.ui.button(label="領取身分組", style=discord.ButtonStyle.primary)
    async def assign_role(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.user
        if self.role in member.roles:
            await member.remove_roles(self.role)
            await interaction.response.send_message(f"✅ 已移除 {self.role.name}", ephemeral=True)
        else:
            await member.add_roles(self.role)
            await interaction.response.send_message(f"✅ 已獲得 {self.role.name}", ephemeral=True)

@client.tree.command(name="rolemsg", description="發送身分組按鈕訊息")
@app_commands.describe(role="要領取的身分組")
async def rolemsg(interaction: discord.Interaction, role: discord.Role):
    if interaction.user.guild_permissions.manage_roles:
        view = RoleButton(role)
        await interaction.response.send_message(f"按下按鈕領取 {role.name}", view=view)
    else:
        await interaction.response.send_message("❌ 需要管理員權限", ephemeral=True)

# -----------------------------
# 設置全域公告頻道（管理員可用）
# -----------------------------
@client.tree.command(name="set_announce", description="設置全域公告頻道")
@app_commands.describe(channel="要發送公告的頻道")
async def set_announce(interaction: discord.Interaction, channel: discord.TextChannel):
    if not interaction.user.guild_permissions.administrator:  # 管理員可用
        await interaction.response.send_message("❌ 需要管理員權限", ephemeral=True)
        return
    db = load_db()
    if "settings" not in db:
        db["settings"] = {}
    if str(interaction.guild.id) not in db["settings"]:
        db["settings"][str(interaction.guild.id)] = {}
    db["settings"][str(interaction.guild.id)]["announce"] = channel.id
    save_db(db)
    await interaction.response.send_message(f"✅ 公告頻道已設置為 {channel.mention}")

# -----------------------------
# 發送全域公告（僅擁有者可用）
# -----------------------------
@client.tree.command(name="broadcast", description="全域公告 (Embed)")
@app_commands.describe(msg="公告內容")
async def broadcast(interaction: discord.Interaction, msg: str):
    OWNER_ID = 1442017307332182168  # <- 你的 Discord ID，只有你能用
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message("❌ 只有擁有者才能發送公告", ephemeral=True)
        return
    await interaction.response.send_message("🚀 發送中...", ephemeral=True)
    db = load_db()
    success, failed, fail_list = 0, 0, []
    for guild in client.guilds:
        try:
            ch_id = db["settings"].get(str(guild.id), {}).get("announce")
            if ch_id:
                ch = client.get_channel(ch_id)
            else:
                ch = next((c for c in guild.text_channels if c.permissions_for(guild.me).send_messages), None)
            if not ch:
                failed += 1
                fail_list.append(guild.name)
                continue
            embed = discord.Embed(title="📢 全域公告", description=msg, color=discord.Color.blue())
            embed.set_footer(text=f"來自 {interaction.user}")
            await ch.send(embed=embed)
            success += 1
        except Exception as e:
            print(f"公告失敗: {guild.name}", e)
            failed += 1
            fail_list.append(guild.name)
    result_embed = discord.Embed(title="📊 公告發送結果", color=discord.Color.green())
    result_embed.add_field(name="✅ 成功", value=str(success), inline=True)
    result_embed.add_field(name="❌ 失敗", value=str(failed), inline=True)
    if fail_list:
        result_embed.add_field(name="⚠️ 失敗伺服器", value="\n".join(fail_list[:10]), inline=False)
    await interaction.followup.send(embed=result_embed)
# -----------------------------
# 小遊戲
# -----------------------------
@client.tree.command(name="rps", description="剪刀石頭布，一次30金幣")
@app_commands.describe(choice="剪刀 / 石頭 / 布")
async def rps(interaction: discord.Interaction, choice: str):
    choice = choice.strip()
    uid = str(interaction.user.id)
    db = load_db()
    user_money = db.get("money", {}).get(uid, 100)
    if user_money < 30:
        await interaction.response.send_message("💸 金幣不足", ephemeral=True)
        return
    options = ["剪刀","石頭","布"]
    bot_choice = random.choice(options)
    outcome = ""
    if choice == bot_choice:
        outcome = "平手，你贏得 20 金幣"
        db["money"][uid] += 20 - 30
    elif (choice=="剪刀" and bot_choice=="布") or (choice=="石頭" and bot_choice=="剪刀") or (choice=="布" and bot_choice=="石頭"):
        outcome = f"🎉 你贏了！獲得 50 金幣 (扣 30 投注)"
        db["money"][uid] += 50 - 30
    else:
        outcome = f"😢 你輸了，損失 20 金幣 (扣 30 投注)"
        db["money"][uid] -= 30 + 20
    save_db(db)
    await interaction.response.send_message(f"🤖 我出 {bot_choice}\n{outcome}")

@client.tree.command(name="gacha", description="扭蛋，一次30金幣，隨機 ±100")
async def gacha(interaction: discord.Interaction):
    uid = str(interaction.user.id)
    db = load_db()
    user_money = db.get("money", {}).get(uid, 100)
    if user_money < 30:
        await interaction.response.send_message("💸 金幣不足", ephemeral=True)
        return
    reward = random.randint(-100,100)
    db["money"][uid] += reward - 30
    save_db(db)
    await interaction.response.send_message(f"🎰 你抽到 {reward} 金幣 (扣 30 投注)")

# -----------------------------
# 商店購買指令
# -----------------------------
SHOP_ITEMS = {
    "pro_pass": 10000,
    "double_gold": 5000
}

@client.tree.command(name="buy", description="購買商店物品")
@app_commands.describe(item="購買的物品名稱")
async def buy(interaction: discord.Interaction, item: str):
    item = item.lower()
    if item not in SHOP_ITEMS:
        await interaction.response.send_message("❌ 商店沒有這個物品", ephemeral=True)
        return
    uid = str(interaction.user.id)
    db = load_db()
    money = db.get("money", {}).get(uid, 100)
    price = SHOP_ITEMS[item]
    if money < price:
        await interaction.response.send_message(f"💸 金幣不足，需要 {price}", ephemeral=True)
        return
    db["money"][uid] -= price
    save_db(db)
    await interaction.response.send_message(f"✅ 成功購買 {item}，扣除 {price} 金幣")
    
# -----------------------------
# 音樂播放
# -----------------------------
music_queues = {}

@client.tree.command(name="join", description="讓 Bot 加入語音頻道")
async def join(interaction: discord.Interaction):
    if not interaction.user.voice or not interaction.user.voice.channel:
        await interaction.response.send_message("❌ 你不在語音頻道", ephemeral=True)
        return
    channel = interaction.user.voice.channel
    try:
        await channel.connect()
        await interaction.response.send_message(f"🎵 已加入 {channel.name}")
    except Exception as e:
        await interaction.response.send_message(f"❌ 加入語音頻道失敗: {e}")

@client.tree.command(name="leave", description="讓 Bot 離開語音頻道")
async def leave(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("👋 已離開語音頻道")
    else:
        await interaction.response.send_message("❌ 我不在語音頻道", ephemeral=True)

@client.tree.command(name="play", description="播放 YouTube 音樂")
@app_commands.describe(url="YouTube 影片網址")
async def play(interaction: discord.Interaction, url: str):
    vc = interaction.guild.voice_client
    if not vc:
        await interaction.response.send_message("❌ 我不在語音頻道，先使用 /join", ephemeral=True)
        return
    YDL_OPTIONS = {'format': 'bestaudio','noplaylist':'True'}
    FFMPEG_OPTIONS = {'before_options':'-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options':'-vn'}
    try:
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)
            url2 = info['url']
        vc.stop()
        vc.play(discord.FFmpegPCMAudio(executable="ffmpeg", source=url2, **FFMPEG_OPTIONS))
        await interaction.response.send_message(f"🎶 開始播放: {info['title']}")
    except Exception as e:
        await interaction.response.send_message(f"❌ 播放失敗: {e}")

# -----------------------------
# 日誌系統
# -----------------------------
@client.event
async def on_command_completion(ctx):
    db = load_db()
    log_channel_id = db.get("settings", {}).get(str(ctx.guild.id), {}).get("log")
    if log_channel_id:
        ch = ctx.guild.get_channel(log_channel_id)
        if ch:
            await ch.send(f"📝 {ctx.author} 使用了指令 {ctx.command}")

@client.tree.command(name="set_log", description="設置日誌頻道")
@app_commands.describe(channel="日誌頻道")
async def set_log(interaction: discord.Interaction, channel: discord.TextChannel):
    if interaction.user.guild_permissions.manage_guild:
        db = load_db()
        if "settings" not in db:
            db["settings"] = {}
        if str(interaction.guild.id) not in db["settings"]:
            db["settings"][str(interaction.guild.id)] = {}
        db["settings"][str(interaction.guild.id)]["log"] = channel.id
        save_db(db)
        await interaction.response.send_message(f"✅ 日誌頻道已設置為 {channel.mention}")
    else:
        await interaction.response.send_message("❌ 需要管理員權限", ephemeral=True)

# -----------------------------
# 基本防炸功能
# -----------------------------
@client.event
async def on_message_delete(message):
    if message.author.bot: return
    # 可以擴展到日誌
    db = load_db()
    log_channel_id = db.get("settings", {}).get(str(message.guild.id), {}).get("log")
    if log_channel_id:
        ch = message.guild.get_channel(log_channel_id)
        if ch:
            await ch.send(f"🗑️ 刪除訊息: {message.author} - {message.content[:100]}")

@client.event
async def on_message_edit(before, after):
    if before.author.bot: return
    db = load_db()
    log_channel_id = db.get("settings", {}).get(str(before.guild.id), {}).get("log")
    if log_channel_id:
        ch = before.guild.get_channel(log_channel_id)
        if ch:
            await ch.send(f"✏️ 編輯訊息: {before.author}\n從: {before.content[:100]}\n改為: {after.content[:100]}")

# -----------------------------
# /daily 每日固定金幣
# -----------------------------
@client.tree.command(name="daily", description="每日領取固定金幣")
async def daily(interaction: discord.Interaction):
    uid = str(interaction.user.id)
    db = load_db()
    from datetime import datetime
    last_daily = db.get("settings", {}).get("daily_times", {}).get(uid)
    now = datetime.utcnow()
    if last_daily:
        last_time = datetime.fromisoformat(last_daily)
        if (now - last_time).total_seconds() < 86400:
            await interaction.response.send_message("⏳ 每日只能領取一次金幣", ephemeral=True)
            return
    db["money"][uid] = db.get("money", {}).get(uid, 100) + 100  # 每日 +100 金幣
    if "settings" not in db:
        db["settings"] = {}
    if "daily_times" not in db["settings"]:
        db["settings"]["daily_times"] = {}
    db["settings"]["daily_times"][uid] = now.isoformat()
    save_db(db)
    await interaction.response.send_message("💰 你已領取每日 100 金幣!")

# -----------------------------
# 排行榜系統
# -----------------------------
@client.tree.command(name="leaderboard", description="查看排行榜")
@app_commands.describe(type="排行榜類型: exp / money")
async def leaderboard(interaction: discord.Interaction, type: str):
    type = type.lower()
    db = load_db()
    if type not in ["exp", "money"]:
        await interaction.response.send_message("❌ 類型只能是 exp 或 money", ephemeral=True)
        return
    data = db.get(type, {})
    top = sorted(data.items(), key=lambda x: x[1], reverse=True)[:10]
    desc = ""
    for i, (uid, value) in enumerate(top, start=1):
        member = interaction.guild.get_member(int(uid))
        name = member.name if member else f"ID:{uid}"
        desc += f"#{i} {name} - {value}\n"
    embed = discord.Embed(title=f"🏆 {type.upper()} 排行榜", description=desc or "無資料", color=discord.Color.gold())
    await interaction.response.send_message(embed=embed)

# -----------------------------
# /ping 指令
# -----------------------------
@client.tree.command(name="ping", description="測試延遲（管理員權限）")
async def ping(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ 需要管理員權限", ephemeral=True)
        return
    latency = round(client.latency * 1000)
    await interaction.response.send_message(f"🏓 延遲: {latency}ms")

# -----------------------------
# /help 指令
# -----------------------------
@client.tree.command(name="help", description="列出所有指令說明")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(title="📖 指令清單", color=discord.Color.blue())
    embed.add_field(name="/profile", value="查看個人經驗值和金幣", inline=False)
    embed.add_field(name="/daily", value="每日領取固定金幣", inline=False)
    embed.add_field(name="/leaderboard type: exp/money", value="查看排行榜", inline=False)
    embed.add_field(name="/rps choice", value="剪刀石頭布遊戲", inline=False)
    embed.add_field(name="/gacha", value="扭蛋隨機金幣", inline=False)
    embed.add_field(name="/buy item", value="購買商店物品", inline=False)
    embed.add_field(name="/rolemsg role", value="發送身分組按鈕訊息", inline=False)
    embed.add_field(name="/set_announce channel", value="設置全域公告頻道", inline=False)
    embed.add_field(name="/broadcast msg", value="發送全域公告", inline=False)
    embed.add_field(name="/join", value="加入語音頻道", inline=False)
    embed.add_field(name="/leave", value="離開語音頻道", inline=False)
    embed.add_field(name="/play url", value="播放 YouTube 音樂", inline=False)
    embed.add_field(name="/set_log channel", value="設置日誌頻道", inline=False)
    embed.add_field(name="/ping", value="測試延遲（管理員）", inline=False)
    await interaction.response.send_message(embed=embed)
    
# -----------------------------
# 啟動 Bot
# -----------------------------
client.run(TOKEN)
