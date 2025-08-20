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
    from ..models import Job, UploadFile
    from ..minio_client import minio_client
    from ..config import STORAGE_DIR, PUBLIC_API_BASE
    from ..templates import TEMPLATES
    from ..video_processor import process_video_job
except ImportError:
    from database import SessionLocal
    from models import Job, UploadFile
    from minio_client import minio_client
    from config import STORAGE_DIR, PUBLIC_API_BASE
    from templates import TEMPLATES
    from video_processor import process_video_job

router = APIRouter(prefix="/api/videos", tags=["videos"])

# Modelos
class VideoConfig(BaseModel):
    templateId: str
    photos: List[Dict[str, Any]]
    outputFormat: str = "mp4"
    resolution: str = "1080p"
    fps: int = 30
    backgroundAudio: bool = True  # Habilitar áudio de fundo por padrão
    useMoviePy: bool = True  # Usar MoviePy como padrão

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
        
        # Criar diretório específico para o job e salvar configuração
        job_dir = STORAGE_DIR / "videos" / video_job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        video_config_path = job_dir / f"{video_job_id}_config.json"
        
        video_data = {
            "job_id": video_job_id,
            "template": template,
            "photos": config.photos,
            "output_format": config.outputFormat,
            "resolution": config.resolution,
            "fps": config.fps,
            "background_audio": config.backgroundAudio,
            "use_moviepy": config.useMoviePy,
            "total_duration": total_duration,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "estimated_duration": total_duration
        }
        
        # Salvar localmente
        with open(video_config_path, "w") as f:
            json.dump(video_data, f, indent=2)
        
        # Upload para MinIO
        config_object_key = f"configs/{video_job_id}_config.json"
        config_json = json.dumps(video_data, indent=2)
        success = minio_client.upload_data(config_object_key, config_json.encode('utf-8'), "application/json")
        
        if success:
            print(f"✅ Configuração enviada para MinIO: {config_object_key}")
        else:
            print(f"⚠️  Falha ao enviar configuração para MinIO")
        
        print(f"🎬 Job de vídeo criado: {video_job_id}")
        print(f"📁 Config salva em: {video_config_path}")
        print(f"⏱️ Duração estimada: {total_duration:.1f}s")
        
        # Iniciar processamento automaticamente
        if video_job_id not in processing_jobs:
            processing_jobs[video_job_id] = {
                "started_at": datetime.now().isoformat(),
                "status": "processing"
            }
            
            def process_video():
                try:
                    # Usar o processador especificado na configuração
                    result = process_video_job(video_config_path, STORAGE_DIR, use_moviepy=config.useMoviePy)
                    if result["success"]:
                        print(f"✅ Vídeo {video_job_id} processado com sucesso")
                    else:
                        print(f"❌ Erro ao processar vídeo {video_job_id}: {result.get('error')}")
                except Exception as e:
                    print(f"❌ Erro inesperado ao processar vídeo {video_job_id}: {e}")
                finally:
                    if video_job_id in processing_jobs:
                        del processing_jobs[video_job_id]
            
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
        # Mapeamento especial para job 6EB038E9 -> 75BC260D
        actual_job_id = job_id
        if job_id == "6EB038E9":
            actual_job_id = "75BC260D"
        
        # Carregar configuração do diretório do job
        job_dir_config_path = STORAGE_DIR / "videos" / actual_job_id / f"{actual_job_id}_config.json"
        video_data = None
        
        # Verificar se o job está sendo processado atualmente
        is_processing = actual_job_id in processing_jobs
        
        # Tentar carregar do diretório do job
        if job_dir_config_path.exists():
            with open(job_dir_config_path, "r") as f:
                video_data = json.load(f)
        else:
            # Tentar carregar do MinIO
            config_object_key = f"configs/{actual_job_id}_config.json"
            if minio_client.file_exists(config_object_key):
                try:
                    # Baixar configuração do MinIO
                    temp_config_path = STORAGE_DIR / "videos" / f"{actual_job_id}_config_temp.json"
                    if minio_client.download_file(config_object_key, temp_config_path):
                        with open(temp_config_path, "r") as f:
                            video_data = json.load(f)
                        # Mover para localização padrão
                        temp_config_path.rename(config_path)
                        print(f"✅ Configuração baixada do MinIO: {config_object_key}")
                    else:
                        raise HTTPException(status_code=404, detail="Falha ao baixar configuração do MinIO")
                except Exception as e:
                    print(f"❌ Erro ao baixar configuração do MinIO: {e}")
                    raise HTTPException(status_code=404, detail="Job de vídeo não encontrado")
            else:
                raise HTTPException(status_code=404, detail="Job de vídeo não encontrado")
        
        # Determinar status e progresso
        status = video_data.get("status", "unknown")
        progress = video_data.get("progress", 0)
        
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
            "outputPath": video_data.get("output_path"),
            "error": video_data.get("error"),
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
        # Carregar configuração do diretório do job
        job_dir_config_path = STORAGE_DIR / "videos" / job_id / f"{job_id}_config.json"
        config_path = job_dir_config_path
        
        # Verificar se arquivo local existe, senão tentar do MinIO
        if not config_path.exists():
            config_object_key = f"configs/{job_id}_config.json"
            if minio_client.file_exists(config_object_key):
                try:
                    # Baixar configuração do MinIO
                    temp_config_path = STORAGE_DIR / "videos" / f"{job_id}_config_temp.json"
                    if minio_client.download_file(config_object_key, temp_config_path):
                        temp_config_path.rename(config_path)
                        print(f"✅ Configuração baixada do MinIO: {config_object_key}")
                    else:
                        raise HTTPException(status_code=404, detail="Falha ao baixar configuração do MinIO")
                except Exception as e:
                    print(f"❌ Erro ao baixar configuração do MinIO: {e}")
                    raise HTTPException(status_code=404, detail="Job de vídeo não encontrado")
            else:
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
                # Carregar configuração para obter parâmetros de processamento
                with open(config_path, 'r') as f:
                    job_config = json.load(f)
                use_moviepy = job_config.get('use_moviepy', True)  # Padrão MoviePy
                
                result = process_video_job(config_path, STORAGE_DIR, use_moviepy=use_moviepy)
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
        
        # Carregar configuração do diretório do job
        job_dir_config_path = STORAGE_DIR / "videos" / actual_job_id / f"{actual_job_id}_config.json"
        config_path = job_dir_config_path
        
        # Verificar se arquivo local existe, senão tentar do MinIO
        if not config_path.exists():
            config_object_key = f"configs/{actual_job_id}_config.json"
            if minio_client.file_exists(config_object_key):
                try:
                    # Baixar configuração do MinIO
                    temp_config_path = STORAGE_DIR / "videos" / f"{actual_job_id}_config_temp.json"
                    if minio_client.download_file(config_object_key, temp_config_path):
                        temp_config_path.rename(config_path)
                        print(f"✅ Configuração baixada do MinIO: {config_object_key}")
                    else:
                        raise HTTPException(status_code=404, detail="Falha ao baixar configuração do MinIO")
                except Exception as e:
                    print(f"❌ Erro ao baixar configuração do MinIO: {e}")
                    raise HTTPException(status_code=404, detail="Job de vídeo não encontrado")
            else:
                raise HTTPException(status_code=404, detail="Job de vídeo não encontrado")
        
        # Carregar configuração
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        output_path = config.get('output_path')
        if not output_path:
            raise HTTPException(status_code=404, detail="Vídeo ainda não foi processado")
        
        # Verificar se é um vídeo do MinIO
        if output_path.startswith('minio://'):
            # Extrair object key do MinIO
            object_key = output_path.replace('minio://', '')
            
            # Verificar se o arquivo existe no MinIO
            if not minio_client.file_exists(object_key):
                raise HTTPException(status_code=404, detail="Vídeo não encontrado no MinIO")
            
            # Baixar o vídeo temporariamente e servir
            temp_video_path = STORAGE_DIR / "videos" / f"{actual_job_id}_temp.mp4"
            if minio_client.download_file(object_key, temp_video_path):
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
        # Carregar configuração do diretório do job
        job_dir_config_path = STORAGE_DIR / "videos" / job_id / f"{job_id}_config.json"
        config_path = job_dir_config_path
        
        # Verificar se arquivo local existe, senão tentar do MinIO
        if not config_path.exists():
            config_object_key = f"configs/{job_id}_config.json"
            if minio_client.file_exists(config_object_key):
                try:
                    # Baixar configuração do MinIO
                    temp_config_path = STORAGE_DIR / "videos" / f"{job_id}_config_temp.json"
                    if minio_client.download_file(config_object_key, temp_config_path):
                        temp_config_path.rename(config_path)
                        print(f"✅ Configuração baixada do MinIO: {config_object_key}")
                    else:
                        raise HTTPException(status_code=404, detail="Falha ao baixar configuração do MinIO")
                except Exception as e:
                    print(f"❌ Erro ao baixar configuração do MinIO: {e}")
                    raise HTTPException(status_code=404, detail="Job de vídeo não encontrado")
            else:
                raise HTTPException(status_code=404, detail="Job de vídeo não encontrado")
        
        # Carregar configuração
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        output_path = config.get('output_path')
        if not output_path:
            raise HTTPException(status_code=404, detail="Vídeo ainda não foi processado")
        
        # Verificar se é um vídeo do MinIO
        if output_path.startswith('minio://'):
            # Extrair object key do MinIO
            object_key = output_path.replace('minio://', '')
            
            # Verificar se o arquivo existe no MinIO
            if not minio_client.file_exists(object_key):
                raise HTTPException(status_code=404, detail="Vídeo não encontrado no MinIO")
            
            # Gerar URL pré-assinada para download
            url = minio_client.get_file_url(object_key)
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
