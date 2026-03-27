import os
from pymongo import MongoClient
from dotenv import load_dotenv
import logging

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")
DATABASE_NAME = os.getenv("DATABASE_NAME", "escola")

# Log para debug no Railway
print(f"🔍 Conectando ao banco: {DATABASE_NAME}")
print(f"🔍 MONGODB_URL configurada: {'Sim' if MONGODB_URL else 'Não'}")

if not MONGODB_URL:
    raise ValueError("❌ MONGODB_URL não configurada! Verifique as variáveis de ambiente no Railway.")

try:
    client = MongoClient(MONGODB_URL)
    # Testar conexão
    client.admin.command('ping')
    print("✅ Conexão com MongoDB Atlas estabelecida com sucesso!")
except Exception as e:
    print(f"❌ Erro ao conectar ao MongoDB: {e}")
    raise

db = client[DATABASE_NAME]

def get_db():
    return db