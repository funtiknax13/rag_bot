import os

import aiosqlite

DB_PATH = os.getenv("SQLITE_PATH", "/app/data/history.db")
HISTORY_LENGTH = int(os.getenv("HISTORY_LENGTH", "10"))


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


async def get_history(user_id: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """SELECT role, content FROM history
               WHERE user_id = ?
               ORDER BY created_at DESC
               LIMIT ?""",
            (user_id, HISTORY_LENGTH),
        ) as cursor:
            rows = await cursor.fetchall()
    return [{"role": row[0], "content": row[1]} for row in reversed(rows)]


async def add_message(user_id: int, role: str, content: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO history (user_id, role, content) VALUES (?, ?, ?)",
            (user_id, role, content),
        )
        await db.execute(
            """DELETE FROM history WHERE user_id = ? AND id NOT IN (
               SELECT id FROM history WHERE user_id = ?
               ORDER BY created_at DESC LIMIT ?)""",
            (user_id, user_id, HISTORY_LENGTH),
        )
        await db.commit()
