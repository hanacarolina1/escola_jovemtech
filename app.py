from fastapi import FastAPI, Depends
from routers.alunos import alunos_router
from routers.cursos import cursos_router
from routers.matriculas import matriculas_router
from redis_client import is_redis_available
from database import get_db
import os

app = FastAPI(
    title="API de Gestão Escolar", 
    description="""
        Esta API fornece endpoints para gerenciar alunos, cursos e turmas.
        
        Ambientes:
        - Produção: MongoDB Atlas (escola_producao)
        - Homologação: MongoDB Atlas (escola_homologacao)
    """, 
    version="1.0.0",
)

app.include_router(alunos_router, tags=["alunos"])
app.include_router(cursos_router, tags=["cursos"])
app.include_router(matriculas_router, tags=["matriculas"])

@app.get("/")
def root():
    """Endpoint raiz com informações da API"""
    return {
        "api": "Gestão Escolar API",
        "version": "1.0.0",
        "environment": os.getenv("RAILWAY_ENVIRONMENT", "development"),
        "database": os.getenv("DATABASE_NAME", "escola"),
        "endpoints": [
            "/alunos",
            "/cursos", 
            "/matriculas",
            "/status",
            "/cache/stats"
        ]
    }

@app.get("/status")
def status(db=Depends(get_db)):
    """
    Verifica status da API, MongoDB e Redis.
    """
    # Verificar MongoDB
    try:
        db.command("ping")
        mongodb_status = "connected"
        mongodb_info = {
            "database": os.getenv("DATABASE_NAME"),
            "status": "ok"
        }
    except Exception as e:
        mongodb_status = f"disconnected: {str(e)}"
        mongodb_info = {"error": str(e)}
    
    # Verificar Redis
    redis_available = is_redis_available()
    
    return {
        "api": "running",
        "environment": os.getenv("RAILWAY_ENVIRONMENT", "development"),
        "mongodb": mongodb_status,
        "mongodb_info": mongodb_info,
        "redis": "connected" if redis_available else "disconnected or not configured",
        "cache_ttl": 30 if redis_available else 0,
        "timestamp": __import__("datetime").datetime.now().isoformat()
    }

@app.get("/cache/stats")
def cache_stats():
    """
    Retorna estatísticas do cache (se Redis disponível).
    """
    if not is_redis_available():
        return {
            "status": "redis_unavailable",
            "message": "Redis não está disponível neste ambiente",
            "environment": os.getenv("RAILWAY_ENVIRONMENT", "development")
        }
    
    try:
        from redis_client import get_redis
        redis_conn = get_redis()
        exists = redis_conn.exists("cursos:lista")
        ttl = redis_conn.ttl("cursos:lista") if exists else -1
        
        return {
            "cache_key": "cursos:lista",
            "exists": bool(exists),
            "ttl_seconds": ttl if ttl > 0 else 0,
            "status": "redis_available",
            "environment": os.getenv("RAILWAY_ENVIRONMENT", "development")
        }
    except Exception as e:
        return {"error": str(e)}