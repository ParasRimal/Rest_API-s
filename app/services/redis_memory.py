import json
from typing import List, Dict, Any
import redis
from app.config import settings

class RedisMemoryService:
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        # Allow reading host/port from environment config if available
        redis_host = getattr(settings, "REDIS_HOST", host)
        redis_port = getattr(settings, "REDIS_PORT", port)
        self.client = redis.Redis(
            host=redis_host, 
            port=redis_port, 
            db=db, 
            decode_responses=True,
            socket_connect_timeout=2
        )

    def _get_key(self, session_id: str) -> str:
        return f"chat_history:{session_id}"

    def get_history(self, session_id: str, limit: int = 6) -> List[Dict[str, str]]:
        key = self._get_key(session_id)
        try:
            raw_items = self.client.lrange(key, -limit, -1)
            history = []
            for item in raw_items:
                try:
                    history.append(json.loads(item))
                except Exception:
                    continue
            return history
        except (redis.ConnectionError, redis.TimeoutError) as e:
            print(f"[Redis Warning]: Unable to retrieve chat history ({e})")
            return []

    def add_message(self, session_id: str, role: str, content: str):
        key = self._get_key(session_id)
        message = json.dumps({"role": role, "content": content})
        try:
            self.client.rpush(key, message)
            # Retain last 20 messages per session
            self.client.ltrim(key, -20, -1)
        except (redis.ConnectionError, redis.TimeoutError) as e:
            print(f"[Redis Warning]: Unable to save message to memory ({e})")

    def clear_history(self, session_id: str):
        key = self._get_key(session_id)
        try:
            self.client.delete(key)
        except (redis.ConnectionError, redis.TimeoutError) as e:
            print(f"[Redis Warning]: Unable to clear session history ({e})")

redis_memory_service = RedisMemoryService()