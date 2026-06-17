from pathlib import Path
import asyncpg
from dotenv import load_dotenv
import os

load_dotenv()

# Get Neon connection string from environment variable
NEON_CONNECTION_STRING = os.getenv("NEON_CONNECTION_STRING")

if not NEON_CONNECTION_STRING:
    raise ValueError("NEON_CONNECTION_STRING not found in .env file")

# Module-level POOL variable
POOL = None


async def get_connection():
    """Get connection from pool"""
    if POOL is None:
        await init_pool()
    return await POOL.acquire()


async def init_pool():
    """Initialize connection pool for Neon"""
    # CRITICAL FIX: Use global to update module-level POOL
    global POOL
    POOL = await asyncpg.create_pool(
        dsn=NEON_CONNECTION_STRING,
        min_size=2,
        max_size=50,
        command_timeout=60,
    )


async def close_pool():
    """Close connection pool"""
    global POOL
    if POOL:
        await POOL.close()
        POOL = None