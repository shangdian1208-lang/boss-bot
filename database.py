import aiosqlite

DB = "data.db"

async def init_db():
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            guild_id INTEGER PRIMARY KEY,
            log_channel INTEGER,
            ticket_category INTEGER,
            ticket_log INTEGER,
            count_channel INTEGER
        )
        """)
        await db.commit()

async def set_setting(guild_id, key, value):
    async with aiosqlite.connect(DB) as db:
        await db.execute(f"""
        INSERT INTO settings (guild_id, {key})
        VALUES (?, ?)
        ON CONFLICT(guild_id) DO UPDATE SET {key}=excluded.{key}
        """, (guild_id, value))
        await db.commit()

async def get_setting(guild_id, key):
    async with aiosqlite.connect(DB) as db:
        cursor = await db.execute(f"SELECT {key} FROM settings WHERE guild_id=?", (guild_id,))
        row = await cursor.fetchone()
        return row[0] if row else None
