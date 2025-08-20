from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

# Imports resilientes
try:
    from ..minio_client import get_minio_client
except ImportError:
    from minio_client import get_minio_client

router = APIRouter(prefix="/api/files", tags=["files"])

@router.get("/{object_key:path}")
async def get_file(object_key: str):
    """Servir arquivo do MinIO"""
    try:
        # Verificar se o arquivo existe no MinIO
        if not get_minio_client().file_exists(object_key):
            raise HTTPException(status_code=404, detail="Arquivo não encontrado")
        
        # Gerar URL pré-assinada para download
        url = get_minio_client().get_file_url(object_key)
        if not url:
            raise HTTPException(status_code=500, detail="Erro ao gerar URL do arquivo")
        
        # Redirecionar para a URL do MinIO
        return RedirectResponse(url=url)
        
    except Exception as e:
        print(f"❌ Erro ao servir arquivo: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao servir arquivo: {str(e)}")

@router.get("/{object_key:path}/info")
async def get_file_info(object_key: str):
    """Obter informações de um arquivo no MinIO"""
    try:
        info = get_minio_client().get_file_info(object_key)
        if not info:
            raise HTTPException(status_code=404, detail="Arquivo não encontrado")
        
        return info
        
    except Exception as e:
        print(f"❌ Erro ao obter informações do arquivo: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter informações: {str(e)}")

@router.get("/photos/{photo_id:path}")
async def get_photo_info(photo_id: str):
    """Obter informações de uma foto específica"""
    try:
        print(f"🔍 Buscando foto: {photo_id}")
        
        # Buscar informações da foto no MinIO
        # O photo_id pode ser apenas o nome do arquivo ou o object_key completo
        possible_keys = [
            f"uploads/{photo_id}",
            photo_id
        ]
        
        photo_object_key = None
        for key in possible_keys:
            print(f"   Verificando: {key}")
            try:
                if get_minio_client().file_exists(key):
                    photo_object_key = key
                    print(f"   ✅ Encontrado: {key}")
                    break
            except Exception as e:
                print(f"   ⚠️  Erro ao verificar {key}: {e}")
                continue
        
        if not photo_object_key:
            # Tentar buscar por padrão de nome de arquivo
            try:
                print("   🔍 Listando objetos no bucket...")
                # Listar objetos no bucket para encontrar a foto
                objects = get_minio_client().client.list_objects(get_minio_client().bucket_name, prefix="uploads/", recursive=True)
                for obj in objects:
                    if photo_id in obj.object_name:
                        photo_object_key = obj.object_name
                        print(f"   ✅ Encontrado via listagem: {obj.object_name}")
                        break
            except Exception as e:
                print(f"Erro ao listar objetos: {e}")
        
        if not photo_object_key:
            print(f"   ❌ Foto não encontrada: {photo_id}")
            raise HTTPException(status_code=404, detail="Foto não encontrada")
        
        # Obter informações do arquivo
        try:
            file_info = get_minio_client().get_file_info(photo_object_key)
            if not file_info:
                raise HTTPException(status_code=404, detail="Informações da foto não encontradas")
        except Exception as e:
            print(f"   ⚠️  Erro ao obter info do arquivo: {e}")
            file_info = {"content_type": "image/jpeg"}
        
        # Gerar URL de upload
        try:
            upload_url = get_minio_client().get_file_url(photo_object_key)
        except Exception as e:
            print(f"   ⚠️  Erro ao gerar URL: {e}")
            upload_url = None
        
        # Extrair nome do arquivo do object_key
        file_name = photo_object_key.split("/")[-1] if "/" in photo_object_key else photo_object_key
        
        result = {
            "id": photo_id,
            "fileName": file_name,
            "fileType": file_info.get("content_type", "image/jpeg"),
            "uploadUrl": upload_url,
            "objectKey": photo_object_key,
            "uploadStatus": "completed",
            "orderIndex": 0
        }
        
        print(f"   ✅ Retornando: {result}")
        return result
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        print(f"❌ Erro ao obter informações da foto: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao obter informações da foto: {str(e)}")
