from pathlib import Path
import aiosqlite

BASE_DIR = Path(__file__).parent

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "expenses.db"


async def get_connection():

    conn = await aiosqlite.connect(DB_PATH)
    await conn.execute("PRAGMA journal_mode=WAL;")
    await conn.execute("PRAGMA foreign_keys=ON;")
    conn.row_factory = aiosqlite.Row

    return conn