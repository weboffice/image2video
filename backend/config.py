import os
from pathlib import Path

# Configurações de armazenamento local
STORAGE_DIR = Path(os.getenv("STORAGE_DIR", "./storage")).resolve()
PUBLIC_API_BASE = os.getenv("PUBLIC_API_BASE", "http://localhost:8080")

# Garantir que o diretório de storage existe
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
