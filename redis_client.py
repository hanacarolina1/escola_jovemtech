import redis
import os
from dotenv import load_dotenv
import logging

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
REDIS_ENABLED = os.getenv("REDIS_ENABLED", "true").lower() == "true"

redis_client = None

def get_redis():
    global redis_client
    
    if not REDIS_ENABLED:
        logging.warning("Redis está desabilitado")
        return None
    
    if redis_client is None:
        try:
            redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
            # Testar conexão
            redis_client.ping()
            print("✅ Redis conectado com sucesso!")
        except Exception as e:
            print(f"⚠️  Redis não disponível: {e}")
            redis_client = None
    
    return redis_client

def is_redis_available():
    """Verifica se Redis está disponível"""
    try:
        client = get_redis()
        if client:
            client.ping()
            return True
    except:
        pass
    return False