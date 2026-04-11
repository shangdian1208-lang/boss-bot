import sqlite3

conn = sqlite3.connect("bot.db")
c = conn.cursor()

# ================== 建表 ==================
c.execute("""
CREATE TABLE IF NOT EXISTS notify (
    guild_id INTEGER,
    channel_id INTEGER,
    rss TEXT,
    message TEXT
)
""")

conn.commit()


# ================== SET ==================
def set_notify(guild_id, channel_id, rss, message):
    c.execute("DELETE FROM notify WHERE guild_id=?", (guild_id,))
    c.execute(
        "INSERT INTO notify VALUES (?, ?, ?, ?)",
        (guild_id, channel_id, rss, message)
    )
    conn.commit()


# ================== GET ==================
def get_notify():
    c.execute("SELECT * FROM notify")
    return c.fetchall()
