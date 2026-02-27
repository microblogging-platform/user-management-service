from typing import AsyncGenerator

from redis.asyncio import Redis, from_url

from infrastructure.config import settings


async def get_redis_client() -> AsyncGenerator[Redis, None]:
    client = from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
    try:
        yield client
    finally:
        await client.close()
