from fastapi import APIRouter, HTTPException, Request, Header
from typing import Optional

# Imports resilientes
try:
    from ..database import SessionLocal
    from ..models import UploadFile
    from ..minio_client import minio_client
except ImportError:
    from database import SessionLocal
    from models import UploadFile
    from minio_client import minio_client

router = APIRouter(prefix="/api/upload", tags=["upload"])

@router.put("/{object_key:path}")
async def put_upload(object_key: str, request: Request, content_type: Optional[str] = Header(None)):
    """Receber PUT com o corpo do arquivo e salvar no MinIO."""
    body = await request.body()
    print(f"📁 Tamanho do arquivo: {len(body)} bytes")
    
    try:
        # Upload para MinIO
        success = minio_client.upload_data(object_key, body, content_type)
        if not success:
            raise HTTPException(status_code=500, detail="Falha ao fazer upload para MinIO")
        
        print(f"✅ Arquivo enviado para MinIO com sucesso: {object_key}")
        
        # Atualizar banco
        db = SessionLocal()
        try:
            rec = db.query(UploadFile).filter(UploadFile.object_key == object_key).first()
            if rec:
                rec.status = "uploaded"
                rec.size_bytes = len(body)
                if content_type:
                    rec.content_type = content_type
                db.commit()
            return {"message": "Upload concluído", "bytes": len(body)}
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Erro ao fazer upload: {e}")
        raise HTTPException(status_code=500, detail=f"Falha ao fazer upload: {e}")
