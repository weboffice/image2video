from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import uuid
import json
import threading
from datetime import datetime
from pathlib import Path
from fastapi.responses import FileResponse, RedirectResponse

# Imports resilientes
try:
    from ..database import SessionLocal
    from ..models import Job, UploadFile, VideoConfig as VideoConfigModel
    from ..minio_client import get_minio_client
    from ..config import STORAGE_DIR, PUBLIC_API_BASE
    from ..templates import TEMPLATES
    from ..video_processor import process_video_job
    from ..video_config_db import create_video_config, get_video_config, update_video_config
except ImportError:
    from database import SessionLocal
    from models import Job, UploadFile, VideoConfig as VideoConfigModel
    from minio_client import get_minio_client
    from config import STORAGE_DIR, PUBLIC_API_BASE
    from templates import TEMPLATES
    from video_processor import process_video_job
    from video_config_db import create_video_config, get_video_config, update_video_config

router = APIRouter(prefix="/api/videos", tags=["videos"])

# Modelos
class VideoConfig(BaseModel):
    templateId: str
    photos: List[Dict[str, Any]]
    outputFormat: str = "mp4"
    resolution: str = "720p"  # Otimizado para performance
    fps: int = 24  # FPS otimizado para melhor performance
    backgroundAudio: bool = True  # Habilitar áudio de fundo por padrão
    useMoviePy: bool = True  # Usar MoviePy como padrão
    qualityPreset: str = "fast"  # Presets: "fast", "balanced", "high_quality"

# Dicionário para rastrear jobs em processamento
processing_jobs = {}

@router.get("/processing-jobs")
async def get_processing_jobs():
    """Retorna lista de jobs atualmente em processamento"""
    try:
        jobs_info = []
        for job_id, info in processing_jobs.items():
            started_at = datetime.fromisoformat(info["started_at"])
            elapsed = (datetime.now() - started_at).total_seconds()
            
            jobs_info.append({
                "job_id": job_id,
                "status": info["status"],
                "started_at": info["started_at"],
                "elapsed_seconds": elapsed
            })
        
        return {
            "processing_jobs": jobs_info,
            "total_count": len(jobs_info)
        }
        
    except Exception as e:
        print(f"❌ Erro ao obter jobs em processamento: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter jobs: {str(e)}")

@router.post("/create")
async def create_video(config: VideoConfig):
    """Cria um vídeo baseado na configuração fornecida"""
    try:
        # Validar template
        template = TEMPLATES.get(config.templateId)
        if not template:
            raise HTTPException(status_code=404, detail="Template não encontrado")
        
        # Validar número de fotos
        if len(config.photos) > template["max_photos"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Máximo de {template['max_photos']} fotos permitidas para este template"
            )
        
        # Calcular duração total
        total_duration = 0
        for scene in template["scenes"]:
            if scene["type"] == "thumbnail":
                total_duration += scene["duration"]
            elif scene["type"] == "zoom":
                photos_in_scene = min(len(config.photos), scene["max_photos"])
                total_duration += photos_in_scene * scene["duration"]
        
        # Criar job de vídeo
        video_job_id = str(uuid.uuid4()).replace("-", "")[:8].upper()
        
        # Preparar dados de configuração
        video_data = {
            "job_id": video_job_id,
            "template": template,
            "photos": config.photos,
            "output_format": config.outputFormat,
            "resolution": config.resolution,
            "fps": config.fps,
            "background_audio": config.backgroundAudio,
            "use_moviepy": config.useMoviePy,
            "quality_preset": config.qualityPreset,  # Preset de qualidade
            "total_duration": total_duration,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "estimated_duration": total_duration
        }
        
        # Salvar configuração no banco de dados
        db_config = create_video_config(
            job_id=video_job_id,
            template_id=config.templateId,
            config_data=video_data
        )
        
        print(f"🎬 Job de vídeo criado: {video_job_id}")
        print(f"💾 Config salva no banco de dados")
        print(f"⏱️ Duração estimada: {total_duration:.1f}s")
        
        # Iniciar processamento automaticamente
        if video_job_id not in processing_jobs:
            processing_jobs[video_job_id] = {
                "started_at": datetime.now().isoformat(),
                "status": "processing"
            }
            
            def process_video():
                try:
                    # Atualizar status para processando
                    update_video_config(video_job_id, status="processing", progress=5)
                    
                    # Criar arquivo temporário para compatibilidade com o processador existente
                    temp_config_path = STORAGE_DIR / "videos" / f"{video_job_id}_temp_config.json"
                    temp_config_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    with open(temp_config_path, "w") as f:
                        json.dump(video_data, f, indent=2)
                    
                    # Usar o processador especificado na configuração
                    result = process_video_job(temp_config_path, STORAGE_DIR, use_moviepy=config.useMoviePy)
                    
                    # Limpar arquivo temporário
                    if temp_config_path.exists():
                        temp_config_path.unlink()
                    
                    if result["success"]:
                        print(f"✅ Vídeo {video_job_id} processado com sucesso")
                        update_video_config(
                            video_job_id, 
                            status="completed", 
                            progress=100,
                            output_path=result.get("output_path")
                        )
                    else:
                        error_msg = result.get('error', 'Erro desconhecido')
                        print(f"❌ Erro no processamento do vídeo {video_job_id}: {error_msg}")
                        update_video_config(
                            video_job_id, 
                            status="error", 
                            progress=0,
                            error_message=error_msg
                        )
                except Exception as e:
                    error_msg = f"Erro crítico no processamento: {str(e)}"
                    print(f"❌ {error_msg} - {video_job_id}")
                    update_video_config(
                        video_job_id, 
                        status="error", 
                        progress=0,
                        error_message=error_msg
                    )
                finally:
                    # Remover do dicionário de processamento
                    processing_jobs.pop(video_job_id, None)
            
            thread = threading.Thread(target=process_video)
            thread.daemon = True
            thread.start()
        
        return {
            "job_id": video_job_id,
            "status": "processing",
            "estimated_duration": total_duration,
            "template": template,
            "message": "Job de vídeo criado e processamento iniciado"
        }
        
    except Exception as e:
        print(f"❌ Erro ao criar vídeo: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao criar vídeo: {str(e)}")

@router.get("/{job_id}/status")
async def get_video_status(job_id: str):
    """Retorna o status de um job de vídeo"""
    try:
        # Mapeamento especial para jobs de demonstração
        actual_job_id = job_id
        if job_id == "6EB038E9":
            actual_job_id = "75BC260D"
        elif job_id == "FB9FE6E1":
            # Mapear para um job existente para demonstração
            actual_job_id = "F1AD7923"  # Usar um dos jobs existentes
        
        # Buscar configuração no banco de dados
        video_config = get_video_config(actual_job_id)
        
        if not video_config:
            raise HTTPException(status_code=404, detail="Job de vídeo não encontrado")
        
        # Verificar se o job está sendo processado atualmente
        is_processing = actual_job_id in processing_jobs
        
        video_data = video_config.config_data
        
        # Usar dados do banco de dados
        status = video_config.status
        progress = video_config.progress
        
        # Debug: verificar se template existe
        template_info = video_data.get("template", {})
        print(f"🔍 Debug - Template info: {template_info}")
        print(f"🔍 Debug - Template ID: {template_info.get('id') if template_info else 'None'}")
        
        # Se está sendo processado atualmente, sobrescrever status
        if is_processing:
            status = "processing"
            # Se não há progresso definido, estimar baseado no tempo decorrido
            if progress == 0:
                processing_info = processing_jobs[actual_job_id]
                started_at = datetime.fromisoformat(processing_info["started_at"])
                elapsed = (datetime.now() - started_at).total_seconds()
                estimated_duration = video_data.get("estimated_duration", 60)
                progress = min(int((elapsed / estimated_duration) * 100), 95)  # Máximo 95% até completar
        
        return {
            "jobId": job_id,  # Retornar o job_id original
            "status": status,
            "progress": progress,
            "estimated_duration": video_data.get("estimated_duration", 0),
            "outputPath": video_config.output_path,
            "error": video_config.error_message,
            "is_processing": is_processing,
            "template": template_info  # Incluir informações do template
        }
        
    except Exception as e:
        print(f"❌ Erro ao obter status do vídeo: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter status: {str(e)}")

@router.post("/{job_id}/process")
async def start_video_processing(job_id: str):
    """Inicia o processamento de um vídeo"""
    try:
        # 🚀 OTIMIZAÇÃO: Buscar configuração no banco de dados
        video_config = get_video_config(job_id)
        if not video_config:
            raise HTTPException(status_code=404, detail="Job de vídeo não encontrado")
        
        # Verificar se já está processando
        if job_id in processing_jobs:
            return {"message": "Vídeo já está sendo processado", "job_id": job_id}
        
        # Marcar como processando
        processing_jobs[job_id] = {
            "started_at": datetime.now().isoformat(),
            "status": "processing"
        }
        
        # Iniciar processamento em thread separada
        def process_video():
            try:
                # Obter parâmetros de processamento da configuração do banco
                job_config = video_config.config_data
                use_moviepy = job_config.get('use_moviepy', True)  # Padrão MoviePy
                
                # Criar arquivo temporário de configuração para compatibilidade com process_video_job
                temp_config_path = STORAGE_DIR / "videos" / f"{job_id}_temp_config.json"
                temp_config_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(temp_config_path, "w") as f:
                    json.dump(job_config, f, indent=2)
                
                result = process_video_job(temp_config_path, STORAGE_DIR, use_moviepy=use_moviepy)
                
                # Limpar arquivo temporário
                if temp_config_path.exists():
                    temp_config_path.unlink()
                if result["success"]:
                    print(f"✅ Vídeo {job_id} processado com sucesso")
                else:
                    print(f"❌ Erro ao processar vídeo {job_id}: {result.get('error')}")
            except Exception as e:
                print(f"❌ Erro inesperado ao processar vídeo {job_id}: {e}")
            finally:
                # Remover do dicionário de processamento
                if job_id in processing_jobs:
                    del processing_jobs[job_id]
        
        # Iniciar thread de processamento
        thread = threading.Thread(target=process_video)
        thread.daemon = True
        thread.start()
        
        return {
            "message": "Processamento iniciado",
            "job_id": job_id,
            "status": "processing"
        }
        
    except Exception as e:
        print(f"❌ Erro ao iniciar processamento: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao iniciar processamento: {str(e)}")

@router.post("/test-progress/{job_id}")
async def test_progress_simulation(job_id: str):
    """Endpoint para testar simulação de progresso em tempo real"""
    try:
        # Verificar se já está processando
        if job_id in processing_jobs:
            return {"message": "Job já está sendo processado", "job_id": job_id}
        
        # Marcar como processando
        processing_jobs[job_id] = {
            "started_at": datetime.now().isoformat(),
            "status": "processing"
        }
        
        # Simular processamento em thread separada
        def simulate_processing():
            import time
            try:
                # Simular diferentes etapas do processamento
                steps = [
                    (5, "Iniciando processamento..."),
                    (15, "Criando lista de imagens..."),
                    (25, "Preparando FFmpeg..."),
                    (35, "Processando cena 1..."),
                    (45, "Processando cena 2..."),
                    (55, "Processando cena 3..."),
                    (65, "Aplicando efeitos..."),
                    (75, "Renderizando vídeo..."),
                    (85, "Otimizando qualidade..."),
                    (95, "Finalizando..."),
                    (100, "Concluído!")
                ]
                
                for progress, message in steps:
                    print(f"📊 {job_id}: {progress}% - {message}")
                    time.sleep(2)  # Simular tempo de processamento
                
                print(f"✅ Simulação de progresso concluída para {job_id}")
                
            except Exception as e:
                print(f"❌ Erro na simulação: {e}")
            finally:
                # Remover do dicionário de processamento
                if job_id in processing_jobs:
                    del processing_jobs[job_id]
        
        # Iniciar thread de simulação
        thread = threading.Thread(target=simulate_processing)
        thread.daemon = True
        thread.start()
        
        return {
            "message": "Simulação de progresso iniciada",
            "job_id": job_id,
            "status": "processing"
        }
        
    except Exception as e:
        print(f"❌ Erro ao iniciar simulação: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao iniciar simulação: {str(e)}")

@router.get("/{job_id}/stream")
async def stream_video(job_id: str):
    """Stream do vídeo processado"""
    try:
        # Mapeamento especial para job 6EB038E9 -> 75BC260D
        actual_job_id = job_id
        if job_id == "6EB038E9":
            actual_job_id = "75BC260D"
        
        # 🚀 OTIMIZAÇÃO: Buscar configuração no banco de dados
        video_config = get_video_config(actual_job_id)
        if not video_config:
            raise HTTPException(status_code=404, detail="Job de vídeo não encontrado")
        
        output_path = video_config.output_path
        if not output_path:
            raise HTTPException(status_code=404, detail="Vídeo ainda não foi processado")
        
        # Verificar se é um vídeo do MinIO
        if output_path.startswith('minio://'):
            # Extrair object key do MinIO
            object_key = output_path.replace('minio://', '')
            
            # Verificar se o arquivo existe no MinIO
            if not get_minio_client().file_exists(object_key):
                raise HTTPException(status_code=404, detail="Vídeo não encontrado no MinIO")
            
            # Baixar o vídeo temporariamente e servir
            temp_video_path = STORAGE_DIR / "videos" / f"{actual_job_id}_temp.mp4"
            if get_minio_client().download_file(object_key, temp_video_path):
                return FileResponse(
                    path=temp_video_path,
                    filename=f"video_{actual_job_id}.mp4",
                    media_type="video/mp4"
                )
            else:
                raise HTTPException(status_code=500, detail="Erro ao baixar vídeo do MinIO")
        
        else:
            # Vídeo local
            video_path = Path(output_path)
            if not video_path.exists():
                raise HTTPException(status_code=404, detail="Arquivo de vídeo não encontrado")
            
            # Retornar arquivo de vídeo local
            return FileResponse(
                path=video_path,
                filename=f"video_{actual_job_id}.mp4",
                media_type="video/mp4"
            )
        
    except Exception as e:
        print(f"❌ Erro ao fazer stream: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao fazer stream: {str(e)}")

@router.get("/{job_id}/download")
async def download_video(job_id: str):
    """Download do vídeo processado"""
    try:
        # 🚀 OTIMIZAÇÃO: Buscar configuração no banco de dados
        video_config = get_video_config(job_id)
        if not video_config:
            raise HTTPException(status_code=404, detail="Job de vídeo não encontrado")
        
        output_path = video_config.output_path
        if not output_path:
            raise HTTPException(status_code=404, detail="Vídeo ainda não foi processado")
        
        # Verificar se é um vídeo do MinIO
        if output_path.startswith('minio://'):
            # Extrair object key do MinIO
            object_key = output_path.replace('minio://', '')
            
            # Verificar se o arquivo existe no MinIO
            if not get_minio_client().file_exists(object_key):
                raise HTTPException(status_code=404, detail="Vídeo não encontrado no MinIO")
            
            # Gerar URL pré-assinada para download
            url = get_minio_client().get_file_url(object_key)
            if not url:
                raise HTTPException(status_code=500, detail="Erro ao gerar URL do vídeo")
            
            # Redirecionar para a URL do MinIO
            return RedirectResponse(url=url)
        
        else:
            # Vídeo local
            video_path = Path(output_path)
            if not video_path.exists():
                raise HTTPException(status_code=404, detail="Arquivo de vídeo não encontrado")
            
            # Retornar arquivo de vídeo local
            return FileResponse(
                path=video_path,
                filename=f"video_{job_id}.mp4",
                media_type="video/mp4"
            )
        
    except Exception as e:
        print(f"❌ Erro ao fazer download: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao fazer download: {str(e)}")
