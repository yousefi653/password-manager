import os

import redis
from dotenv import load_dotenv

load_dotenv()


class RedisService:
    _client = redis.Redis(
        host=os.getenv("REDIS_HOST", "127.0.0.1"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        db=int(os.getenv("REDIS_DB", "0")),
        decode_responses=True,
    )

    @classmethod
    def set(cls, key, value, ttl=None):
        cls._client.set(name=key, value=value, ex=ttl)

    @classmethod
    def get(cls, key):
        return cls._client.get(key)

    @classmethod
    def delete(cls, key):
        return cls._client.delete(key)

    @classmethod
    def increase(cls, key, ttl=3600):
        cls._client.incr(name=key, amount=1)
        cls._client.expire(name=key, time=ttl)