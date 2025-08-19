#!/usr/bin/env python3
"""
Script simples para gerar vídeo de slideshow.
Uso: python scripts/simple_video_generator.py <job_id>
"""

import sys
import json
import os
import subprocess
from pathlib import Path
from typing import Dict, Any, List

# Adicionar o diretório backend ao path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from main import AVAILABLE_TEMPLATES

# Imports para MinIO
try:
    from backend.minio_client import minio_client
except ImportError:
    from minio_client import minio_client

class SimpleVideoGenerator:
    def __init__(self):
        self.storage_dir = Path(__file__).parent.parent / "backend" / "storage"
        self.videos_dir = self.storage_dir / "videos"
        
    def load_job_config(self, job_id: str) -> Dict[str, Any]:
        """Carrega configuração do job"""
        config_file = self.videos_dir / f"{job_id}_config.json"
        
        if not config_file.exists():
            raise FileNotFoundError(f"Arquivo de configuração não encontrado: {config_file}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_job_photos(self, job_id: str) -> List[str]:
        """Obtém lista de fotos do job"""
        photos = []
        
        try:
            config = self.load_job_config(job_id)
            if 'photos' in config:
                for photo_info in config['photos']:
                    if 'filePath' in photo_info:
                        # Verificar se o arquivo existe localmente ou no MinIO
                        photo_path = self.storage_dir / photo_info['filePath']
                        if photo_path.exists():
                            # Arquivo existe localmente
                            photos.append(str(photo_path))
                        elif minio_client.file_exists(photo_info['filePath']):
                            # Arquivo existe no MinIO, baixar temporariamente
                            temp_path = self.storage_dir / f"temp_{job_id}_{len(photos)}.jpg"
                            if minio_client.download_file(photo_info['filePath'], temp_path):
                                photos.append(str(temp_path))
                                print(f"✅ Baixado do MinIO: {photo_info['filePath']}")
                            else:
                                print(f"⚠️  Falha ao baixar do MinIO: {photo_info['filePath']}")
                        else:
                            print(f"⚠️  Foto não encontrada: {photo_info['filePath']}")
        except Exception as e:
            print(f"⚠️  Erro ao carregar configuração: {e}")
        
        return sorted(photos)
    
    def create_simple_slideshow(self, photos: List[str], duration_per_photo: float = 4.0, 
                               output_path: str = None) -> str:
        """Cria slideshow simples com fade entre fotos"""
        if not photos:
            raise ValueError("Nenhuma foto fornecida")
        
        if not output_path:
            output_path = str(self.videos_dir / "simple_slideshow.mp4")
        
        # Criar arquivo de lista para concatenação
        concat_file = self.videos_dir / "concat_list.txt"
        
        with open(concat_file, 'w') as f:
            for photo in photos:
                f.write(f"file '{photo}'\n")
                f.write(f"duration {duration_per_photo}\n")
            # Adicionar última foto novamente para garantir duração
            f.write(f"file '{photos[-1]}'\n")
        
        # Comando FFmpeg para criar slideshow
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file),
            "-vf", "fps=30,scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            output_path
        ]
        
        print(f"🎬 Executando: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        
        # Limpar arquivo temporário
        try:
            os.remove(concat_file)
        except:
            pass
        
        # Limpar arquivos temporários do MinIO
        for photo in photos:
            if photo.startswith(str(self.storage_dir / "temp_")):
                try:
                    os.remove(photo)
                    print(f"🧹 Limpo arquivo temporário: {os.path.basename(photo)}")
                except:
                    pass
        
        return output_path
    
    def generate_video(self, job_id: str, duration_per_photo: float = 4.0):
        """Gera vídeo simples para o job"""
        print(f"🎬 Gerando vídeo simples para job: {job_id}")
        print("=" * 50)
        
        try:
            # Carregar configuração e fotos
            config = self.load_job_config(job_id)
            photos = self.get_job_photos(job_id)
            
            if not photos:
                print("❌ Nenhuma foto encontrada")
                return
            
            print(f"✅ Fotos encontradas: {len(photos)}")
            for i, photo in enumerate(photos):
                print(f"   {i+1}. {os.path.basename(photo)}")
            
            # Calcular duração total
            total_duration = len(photos) * duration_per_photo
            print(f"✅ Duração total: {total_duration:.1f} segundos ({total_duration/60:.1f} minutos)")
            
            # Gerar vídeo
            output_path = str(self.videos_dir / f"{job_id}_simple.mp4")
            result_path = self.create_simple_slideshow(photos, duration_per_photo, output_path)
            
            print(f"✅ Vídeo gerado com sucesso: {result_path}")
            
            # Verificar tamanho do arquivo
            if os.path.exists(result_path):
                file_size = os.path.getsize(result_path) / (1024 * 1024)
                print(f"📁 Tamanho: {file_size:.1f} MB")
                
                # Upload do vídeo para MinIO
                video_object_key = f"videos/{job_id}_simple.mp4"
                print(f"📤 Fazendo upload do vídeo para MinIO: {video_object_key}")
                
                success = minio_client.upload_file(video_object_key, result_path, "video/mp4")
                if success:
                    print(f"✅ Vídeo enviado para MinIO: {video_object_key}")
                else:
                    print(f"⚠️  Falha ao enviar vídeo para MinIO")
            
            print("🎉 Processo concluído!")
            
        except Exception as e:
            print(f"❌ Erro: {e}")
            import traceback
            traceback.print_exc()

def main():
    if len(sys.argv) < 2:
        print("Uso: python scripts/simple_video_generator.py <job_id> [duration_per_photo]")
        return
    
    job_id = sys.argv[1]
    duration_per_photo = float(sys.argv[2]) if len(sys.argv) > 2 else 4.0
    
    generator = SimpleVideoGenerator()
    generator.generate_video(job_id, duration_per_photo)

if __name__ == "__main__":
    main()
