import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

# Obter o diretório onde este arquivo config.py está localizado
BASE_DIR = Path(__file__).parent

# Carregar variáveis de ambiente do arquivo .env
# Prioridade: 1) .env no mesmo diretório do config.py, 2) buscar em diretórios pais
env_path = BASE_DIR / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
else:
    # Se não encontrar no diretório atual, procurar em diretórios pais
    load_dotenv(find_dotenv(), override=True)

# Configurações de armazenamento local
STORAGE_DIR = Path(os.getenv("STORAGE_DIR", "./storage")).resolve()
PUBLIC_API_BASE = os.getenv("PUBLIC_API_BASE", "http://localhost:8080")

# Garantir que o diretório de storage existe
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
