from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List
from schemas import Curso
from database import get_db
from bson import ObjectId
from redis_client import get_redis, is_redis_available
import json
from datetime import datetime

cursos_router = APIRouter()

CACHE_TTL = 30

@cursos_router.get("/cursos", response_model=List[Curso])
def read_cursos(db = Depends(get_db)):
    """
    Retorna lista de cursos com cache Redis (se disponível).
    """
    # Verificar se Redis está disponível
    if is_redis_available():
        redis_conn = get_redis()
        cache_key = "cursos:lista"
        
        # 1. Verificar se está no Redis
        cached_data = redis_conn.get(cache_key)
        
        if cached_data:
            print("✅ Cache HIT - Retornando do Redis")
            cursos_data = json.loads(cached_data)
            return [Curso(**curso) for curso in cursos_data]
    
    # 2. Se não está no cache ou Redis indisponível, buscar do MongoDB
    print("❌ Cache MISS - Buscando no MongoDB")
    cursos = list(db.cursos.find())
    
    # Se Redis estiver disponível, salvar no cache
    if is_redis_available():
        try:
            redis_conn = get_redis()
            cursos_serializable = []
            for curso in cursos:
                curso_dict = {
                    "id": str(curso["_id"]),
                    "nome": curso["nome"],
                    "codigo": curso["codigo"],
                    "descricao": curso.get("descricao", ""),
                    "carga_horaria": curso.get("carga_horaria", 0)
                }
                cursos_serializable.append(curso_dict)
            
            redis_conn.setex(cache_key, CACHE_TTL, json.dumps(cursos_serializable))
            print("💾 Dados salvos no cache Redis")
        except Exception as e:
            print(f"⚠️  Erro ao salvar no Redis: {e}")
    
    return cursos

@cursos_router.post("/cursos", response_model=Curso)
def create_curso(curso: Curso = Body(...), db = Depends(get_db)):
    """
    Cria um novo curso e limpa o cache se Redis estiver disponível.
    """
    curso_dict = curso.dict(exclude={"id"})
    new_curso = db.cursos.insert_one(curso_dict)
    created_curso = db.cursos.find_one({"_id": new_curso.inserted_id})
    
    # Limpar cache se Redis estiver disponível
    if is_redis_available():
        try:
            redis_conn = get_redis()
            redis_conn.delete("cursos:lista")
            print("🗑️  Cache limpo após criação de curso")
        except Exception as e:
            print(f"⚠️  Erro ao limpar cache: {e}")
    
    return created_curso

@cursos_router.put("/cursos/{codigo_curso}", response_model=Curso)
def update_curso(codigo_curso: str, curso: Curso = Body(...), db = Depends(get_db)):
    """
    Atualiza um curso e limpa o cache se Redis estiver disponível.
    """
    db_curso = db.cursos.find_one({"codigo": codigo_curso})
    if db_curso is None:
        raise HTTPException(status_code=404, detail="Curso não encontrado")

    curso_dict = {k: v for k, v in curso.dict(exclude_unset=True).items() if k != "id"}
    
    if len(curso_dict) >= 1:
        db.cursos.update_one({"codigo": codigo_curso}, {"$set": curso_dict})

    updated_curso = db.cursos.find_one({"codigo": codigo_curso})
    
    # Limpar cache se Redis estiver disponível
    if is_redis_available():
        try:
            redis_conn = get_redis()
            redis_conn.delete("cursos:lista")
            print("🗑️  Cache limpo após atualização de curso")
        except Exception as e:
            print(f"⚠️  Erro ao limpar cache: {e}")
    
    return updated_curso

@cursos_router.get("/cursos/{codigo_curso}", response_model=Curso)
def read_curso_por_codigo(codigo_curso: str, db = Depends(get_db)):
    """
    Retorna um curso específico por código.
    """
    # Cache individual apenas se Redis disponível
    if is_redis_available():
        try:
            redis_conn = get_redis()
            cache_key = f"curso:{codigo_curso}"
            cached_curso = redis_conn.get(cache_key)
            
            if cached_curso:
                print(f"✅ Cache HIT - Curso {codigo_curso}")
                curso_data = json.loads(cached_curso)
                return Curso(**curso_data)
        except Exception as e:
            print(f"⚠️  Erro ao ler cache: {e}")
    
    db_curso = db.cursos.find_one({"codigo": codigo_curso})
    if db_curso is None:
        raise HTTPException(status_code=404, detail="Nenhum curso encontrado com esse código")
    
    # Salvar no cache individual se Redis disponível
    if is_redis_available():
        try:
            redis_conn = get_redis()
            curso_dict = {
                "id": str(db_curso["_id"]),
                "nome": db_curso["nome"],
                "codigo": db_curso["codigo"],
                "descricao": db_curso.get("descricao", ""),
                "carga_horaria": db_curso.get("carga_horaria", 0)
            }
            redis_conn.setex(cache_key, CACHE_TTL, json.dumps(curso_dict))
        except Exception as e:
            print(f"⚠️  Erro ao salvar cache: {e}")
    
    return db_curso