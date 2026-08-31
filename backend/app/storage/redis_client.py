import os
import redis

REDIS_HOST = os.getenv("REDIS_HOST", "image-rag-redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True,
)

def redis_ping() -> bool:
    return bool(redis_client.ping())