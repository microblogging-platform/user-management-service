from domain.interfaces.services.blacklist import ITokenBlacklistService
from redis.asyncio import Redis


class RedisTokenBlacklistService(ITokenBlacklistService):
    def __init__(self, redis: Redis):
        self.redis = redis

    async def blacklist_token(self, token: str, expires_at: int) -> None:
        await self.redis.set(token, "blacklisted", exat=expires_at)

    async def is_blacklisted(self, token: str) -> bool:
        exists = await self.redis.exists(token)
        return exists > 0
