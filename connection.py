from pathlib import Path
import asyncpg
from dotenv import load_dotenv
import os

load_dotenv()

# Get Neon connection string from environment variable
NEON_CONNECTION_STRING = os.getenv("NEON_CONNECTION_STRING")

if not NEON_CONNECTION_STRING:
    raise ValueError("NEON_CONNECTION_STRING not found in .env file")

POOL = None


async def get_connection():
    """Get connection from pool"""
    if POOL is None:
        await init_pool()
    return await POOL.acquire()


async def init_pool():
    """Initialize connection pool for Neon"""
    POOL = await asyncpg.create_pool(
        dsn=NEON_CONNECTION_STRING,
        min_size=2,           # Minimum connections
        max_size=50,          # Handle concurrent requests from multiple users
        command_timeout=60,   # 60s timeout
    )


async def close_pool():
    """Close connection pool"""
    if POOL:
        await POOL.close()