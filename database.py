import os
from contextlib import asynccontextmanager
import asyncpg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/shopdb")

_pool = None

async def get_pool():
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
    return _pool

async def close_pool():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None

@asynccontextmanager
async def get_db():
    pool = await get_pool()
    async with pool.acquire() as conn:
        yield conn

async def init_db():
    pool = await get_pool()
    async with pool.acquire() as conn:
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        with open(schema_path, "r", encoding="utf-8") as f:
            sql = f.read()
        await conn.execute(sql)
    print("✅ Database initialized")
