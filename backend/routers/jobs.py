from fastapi import APIRouter, HTTPException, Request, Header
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime
from pathlib import Path
import json

# Imports resilientes
try:
    from ..database import SessionLocal
    from ..models import Job, UploadFile
    from ..minio_client import minio_client
    from ..config import STORAGE_DIR, PUBLIC_API_BASE
except ImportError:
    from database import SessionLocal
    from models import Job, UploadFile
    from minio_client import minio_client
    from config import STORAGE_DIR, PUBLIC_API_BASE

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

# Modelos
class JobCreateRequest(BaseModel):
    template_id: Optional[str] = None

class JobResponse(BaseModel):
    code: str
    status: str
    created_at: str

class UploadURLRequest(BaseModel):
    filename: str
    content_type: str
    job_code: Optional[str] = None

class UploadURLResponse(BaseModel):
    upload_url: str
    object_key: str
    public_url: str

class DeletePhotoResponse(BaseModel):
    message: str
    deleted_file_id: int
    deleted_object_key: str

@router.post("", response_model=JobResponse)
async def create_job(request: JobCreateRequest):
    """Criar um novo job."""
    db = SessionLocal()
    try:
        job_code = str(uuid.uuid4())[:8].upper()
        job = Job(code=job_code, status="created")
        db.add(job)
        db.commit()
        db.refresh(job)
        return JobResponse(code=job.code, status=job.status, created_at=job.created_at.isoformat())
    finally:
        db.close()

@router.post("/upload-url", response_model=UploadURLResponse)
async def get_upload_url(request: UploadURLRequest):
    """Gerar URL local para upload (PUT) e registrar arquivo pendente."""
    allowed = ["image/jpeg", "image/jpg", "image/png"]
    if request.content_type not in allowed:
        raise HTTPException(status_code=400, detail="Tipo de arquivo não suportado. Use JPEG ou PNG.")

    if not request.job_code:
        raise HTTPException(status_code=400, detail="job_code é obrigatório")

    # Certificar job
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.code == request.job_code).first()
        if job is None:
            raise HTTPException(status_code=404, detail="Job não encontrado")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        uuid_part = uuid.uuid4().hex[:6]
        object_key = f"uploads/{request.job_code}/{timestamp}_{uuid_part}_{request.filename}"
        upload_url = f"{PUBLIC_API_BASE}/api/upload/{object_key}"

        # Registrar arquivo pendente
        upload_rec = UploadFile(
            job_id=job.id,
            filename=request.filename,
            content_type=request.content_type,
            object_key=object_key,
            status="pending",
        )
        db.add(upload_rec)
        db.commit()

        public_url = f"/files/{object_key}"
        return UploadURLResponse(upload_url=upload_url, object_key=object_key, public_url=public_url)
    finally:
        db.close()

@router.get("/{job_code}")
async def get_job_status(job_code: str):
    """Obter status e informações de um job"""
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.code == job_code).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job não encontrado")
        
        # Buscar arquivos do job ordenados por order_index
        files = db.query(UploadFile).filter(UploadFile.job_id == job.id).order_by(UploadFile.order_index, UploadFile.created_at).all()
        
        return {
            "code": job.code,
            "status": job.status,
            "created_at": job.created_at.isoformat(),
            "updated_at": job.updated_at.isoformat(),
            "files": [
                {
                    "id": file.id,
                    "filename": file.filename,
                    "content_type": file.content_type,
                    "size_bytes": file.size_bytes,
                    "object_key": file.object_key,
                    "status": file.status,
                    "order_index": file.order_index,
                    "created_at": file.created_at.isoformat()
                }
                for file in files
            ]
        }
    finally:
        db.close()

@router.get("/{job_code}/files")
async def get_job_files(job_code: str):
    """Obter lista de arquivos de um job"""
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.code == job_code).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job não encontrado")
        
        files = db.query(UploadFile).filter(UploadFile.job_id == job.id).all()
        return {
            "job_code": job_code,
            "files": [
                {
                    "id": file.id,
                    "filename": file.filename,
                    "content_type": file.content_type,
                    "size_bytes": file.size_bytes,
                    "object_key": file.object_key,
                    "status": file.status,
                    "created_at": file.created_at.isoformat()
                }
                for file in files
            ]
        }
    finally:
        db.close()

@router.delete("/{job_code}/files/{file_id}", response_model=DeletePhotoResponse)
async def delete_job_file(job_code: str, file_id: int):
    """Deletar um arquivo específico de um job"""
    db = SessionLocal()
    try:
        # Verificar se o job existe
        job = db.query(Job).filter(Job.code == job_code).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job não encontrado")
        
        # Verificar se o arquivo existe e pertence ao job
        file = db.query(UploadFile).filter(
            UploadFile.id == file_id,
            UploadFile.job_id == job.id
        ).first()
        
        if not file:
            raise HTTPException(status_code=404, detail="Arquivo não encontrado")
        
        # Deletar do MinIO
        object_key = file.object_key
        minio_deleted = minio_client.delete_file(object_key)
        
        if not minio_deleted:
            # Se falhar ao deletar do MinIO, logar mas continuar
            print(f"⚠️ Aviso: Falha ao deletar arquivo do MinIO: {object_key}")
        
        # Deletar do banco de dados
        db.delete(file)
        db.commit()
        
        return DeletePhotoResponse(
            message="Arquivo deletado com sucesso",
            deleted_file_id=file_id,
            deleted_object_key=object_key
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao deletar arquivo: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao deletar arquivo")
    finally:
        db.close()

@router.post("/{job_code}/start")
async def start_processing(job_code: str):
    """Iniciar processamento de um job"""
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.code == job_code).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job não encontrado")
        job.status = "processing"
        db.commit()
        return {"message": f"Job {job_code} iniciado"}
    finally:
        db.close()

@router.get("/{job_code}/stream")
async def stream_job_status(job_code: str):
    """Stream de status do job"""
    from fastapi.responses import StreamingResponse
    from asyncio import sleep as asleep

    async def event_stream():
        while True:
            yield f"data: {json.dumps({'status': 'processing'})}\n\n"
            await asleep(2)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )

@router.put("/{job_code}/files/{file_id}/reorder")
async def reorder_file(job_code: str, file_id: int, direction: str):
    """Reordenar um arquivo (mover para cima ou para baixo)"""
    if direction not in ['up', 'down']:
        raise HTTPException(status_code=400, detail="Direction deve ser 'up' ou 'down'")
    
    db = SessionLocal()
    try:
        # Buscar o job
        job = db.query(Job).filter(Job.code == job_code).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job não encontrado")
        
        # Buscar o arquivo a ser movido
        file_to_move = db.query(UploadFile).filter(
            UploadFile.id == file_id,
            UploadFile.job_id == job.id
        ).first()
        if not file_to_move:
            raise HTTPException(status_code=404, detail="Arquivo não encontrado")
        
        # Buscar todos os arquivos do job ordenados
        all_files = db.query(UploadFile).filter(
            UploadFile.job_id == job.id
        ).order_by(UploadFile.order_index, UploadFile.created_at).all()
        
        # Encontrar a posição atual do arquivo
        current_index = None
        for i, file in enumerate(all_files):
            if file.id == file_id:
                current_index = i
                break
        
        if current_index is None:
            raise HTTPException(status_code=404, detail="Arquivo não encontrado na lista")
        
        # Determinar nova posição
        if direction == 'up' and current_index > 0:
            new_index = current_index - 1
        elif direction == 'down' and current_index < len(all_files) - 1:
            new_index = current_index + 1
        else:
            # Não há movimento possível
            return {"message": "Arquivo já está na posição limite", "moved": False}
        
        # Trocar as posições
        file_to_swap = all_files[new_index]
        
        # Atualizar os order_index
        temp_order = file_to_move.order_index
        file_to_move.order_index = file_to_swap.order_index
        file_to_swap.order_index = temp_order
        
        db.commit()
        
        return {
            "message": f"Arquivo movido para {direction}",
            "moved": True,
            "file_id": file_id,
            "new_order": file_to_move.order_index
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao reordenar arquivo: {str(e)}")
    finally:
        db.close()
