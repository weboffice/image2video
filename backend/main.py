from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import uvicorn

# Imports resilientes
try:
    from .database import engine, Base
    from .config import STORAGE_DIR
    from .routers import jobs, upload, files, templates, videos
except ImportError:  # execução direta
    from database import engine, Base
    from config import STORAGE_DIR
    from routers import jobs, upload, files, templates, videos

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerenciar ciclo de vida da aplicação"""
    # Startup
    Base.metadata.create_all(bind=engine)
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    yield
    # Shutdown (se necessário)

app = FastAPI(
    title="Photo-to-Video API",
    description="API para conversão de fotos em vídeo",
    version="1.0.0",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # React dev server
        "http://127.0.0.1:5173",  # Vite dev server (alternativo)
        "http://127.0.0.1:3000",  # React dev server (alternativo)
        "http://172.24.203.99:5173",
        "https://imv.engaja.me" # Frontend dev server (alternativo)
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Servir arquivos estáticos
app.mount("/files", StaticFiles(directory=str(STORAGE_DIR)), name="files")

@app.get("/")
async def root():
    """Endpoint raiz"""
    return {"message": "Photo-to-Video API está funcionando!"}

@app.get("/health")
async def health_check():
    """Verificação de saúde da API"""
    return {"status": "healthy"}

# Incluir routers
app.include_router(jobs.router)
app.include_router(upload.router)
app.include_router(files.router)
app.include_router(templates.router)
app.include_router(videos.router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
