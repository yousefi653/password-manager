import os

import redis
from dotenv import load_dotenv

from logger import get_logger

logger = get_logger(__name__)

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
        logger.debug("redis: set key=%r ttl=%s", key, ttl)
        return cls._client.set(name=key, value=value, ex=ttl)

    @classmethod
    def get(cls, key):
        value = cls._client.get(key)
        logger.debug("redis: get key=%r hit=%s", key, value is not None)
        return value

    @classmethod
    def delete(cls, key):
        logger.debug("redis: delete key=%r", key)
        return cls._client.delete(key)

    @classmethod
    def increase(cls, key, ttl=3600):
        logger.debug("redis: increase key=%r ttl=%s", key, ttl)
        cls._client.incr(name=key, amount=1)
        cls._client.expire(name=key, time=ttl)