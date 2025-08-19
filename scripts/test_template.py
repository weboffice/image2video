#!/usr/bin/env python3
"""
Script para testar templates de vídeo diretamente.
Uso: python scripts/test_template.py <job_id>
"""

import sys
import json
import os
from pathlib import Path
from typing import Dict, Any, List
import subprocess
import time

# Adicionar o diretório backend ao path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from main import AVAILABLE_TEMPLATES, DEFAULT_TEMPLATE, GRID_SHOWCASE_TEMPLATE

# Imports para MinIO
try:
    from backend.minio_client import minio_client
except ImportError:
    from minio_client import minio_client

class TemplateTester:
    def __init__(self):
        self.storage_dir = Path(__file__).parent.parent / "backend" / "storage"
        self.videos_dir = self.storage_dir / "videos"
        self.photos_dir = self.storage_dir / "photos"
        
    def get_template_by_id(self, template_id: str):
        """Busca template pelo ID"""
        for template in AVAILABLE_TEMPLATES:
            if template.id == template_id:
                return template
        return None
    
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
        
        # Primeiro, tentar carregar a configuração do job para obter os caminhos das fotos
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
        
        # Fallback: procurar fotos no diretório do job
        if not photos:
            job_photos_dir = self.storage_dir / "uploads" / job_id
            
            if job_photos_dir.exists():
                for photo_file in job_photos_dir.glob("*.jpg"):
                    photos.append(str(photo_file))
                for photo_file in job_photos_dir.glob("*.png"):
                    photos.append(str(photo_file))
                for photo_file in job_photos_dir.glob("*.jpeg"):
                    photos.append(str(photo_file))
        
        return sorted(photos)
    
    def calculate_video_duration(self, template, photo_count: int) -> float:
        """Calcula duração total do vídeo"""
        total_duration = 0
        
        for scene in template.scenes:
            if scene.type in ['thumbnail', 'grid']:
                total_duration += scene.duration
            elif scene.type == 'zoom':
                photos_in_scene = min(photo_count, scene.max_photos)
                total_duration += photos_in_scene * scene.duration
        
        return total_duration
    
    def generate_video_script(self, template, photos: List[str], output_path: str) -> str:
        """Gera script FFmpeg para criar o vídeo"""
        script_lines = []
        
        # Configurações básicas
        script_lines.append("# FFmpeg script para gerar vídeo")
        script_lines.append(f"# Template: {template.name}")
        script_lines.append(f"# Fotos: {len(photos)}")
        script_lines.append("")
        
        # Input das fotos
        for i, photo in enumerate(photos):
            script_lines.append(f"# Foto {i+1}: {os.path.basename(photo)}")
        
        script_lines.append("")
        
        # Comando FFmpeg base
        ffmpeg_cmd = [
            "ffmpeg",
            "-y",  # Sobrescrever arquivo de saída
            "-framerate", "30",  # 30 FPS
        ]
        
        # Adicionar inputs das fotos
        for photo in photos:
            ffmpeg_cmd.extend(["-loop", "1", "-i", photo])
        
        # Configurações de saída
        ffmpeg_cmd.extend([
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-shortest",
            output_path
        ])
        
        script_lines.append(" ".join(ffmpeg_cmd))
        
        return "\n".join(script_lines)
    
    def create_scene_breakdown(self, template, photos: List[str]) -> List[Dict[str, Any]]:
        """Cria breakdown detalhado das cenas"""
        scenes_breakdown = []
        current_time = 0
        
        for scene in template.scenes:
            scene_info = {
                "scene_id": scene.id,
                "scene_name": scene.name,
                "scene_type": scene.type,
                "start_time": current_time,
                "duration": scene.duration,
                "effects": []
            }
            
            if scene.type in ['thumbnail', 'grid']:
                # Cena fixa - todas as fotos
                scene_info["photos"] = photos[:scene.max_photos]
                scene_info["end_time"] = current_time + scene.duration
                
                for effect in scene.effects:
                    scene_info["effects"].append({
                        "id": effect.id,
                        "type": effect.type,
                        "duration": effect.duration,
                        "parameters": effect.parameters
                    })
                
                current_time += scene.duration
                
            elif scene.type == 'zoom':
                # Cena individual - uma foto por vez
                photos_in_scene = min(len(photos), scene.max_photos)
                
                for i in range(photos_in_scene):
                    individual_scene = scene_info.copy()
                    individual_scene["photo_index"] = i
                    individual_scene["photo_path"] = photos[i]
                    individual_scene["start_time"] = current_time
                    individual_scene["end_time"] = current_time + scene.duration
                    
                    for effect in scene.effects:
                        individual_scene["effects"].append({
                            "id": effect.id,
                            "type": effect.type,
                            "duration": effect.duration,
                            "parameters": effect.parameters
                        })
                    
                    scenes_breakdown.append(individual_scene)
                    current_time += scene.duration
            
            if scene.type in ['thumbnail', 'grid']:
                scenes_breakdown.append(scene_info)
        
        return scenes_breakdown
    
    def test_template(self, job_id: str, template_id: str = None):
        """Testa template com job específico"""
        print(f"🔍 Testando job: {job_id}")
        print("=" * 50)
        
        try:
            # Carregar configuração do job
            config = self.load_job_config(job_id)
            print(f"✅ Configuração carregada")
            
            # Determinar template
            if template_id:
                template = self.get_template_by_id(template_id)
                if not template:
                    print(f"❌ Template '{template_id}' não encontrado")
                    return
            else:
                # Verificar se há template na configuração
                if 'template' in config and 'id' in config['template']:
                    template_id = config['template']['id']
                else:
                    template_id = 'thumbnail-zoom-template'
                
                template = self.get_template_by_id(template_id)
                if not template:
                    print(f"❌ Template '{template_id}' não encontrado")
                    return
            
            print(f"   Template ID: {template_id}")
            print(f"   Fotos: {len(config.get('photos', []))}")
            
            print(f"✅ Template: {template.name}")
            print(f"   Descrição: {template.description}")
            print(f"   Máximo de fotos: {template.max_photos}")
            
            # Obter fotos
            photos = self.get_job_photos(job_id)
            if not photos:
                print(f"❌ Nenhuma foto encontrada para o job {job_id}")
                return
            
            print(f"✅ Fotos encontradas: {len(photos)}")
            for i, photo in enumerate(photos[:5]):  # Mostrar apenas as primeiras 5
                print(f"   {i+1}. {os.path.basename(photo)}")
            if len(photos) > 5:
                print(f"   ... e mais {len(photos) - 5} fotos")
            
            # Calcular duração
            total_duration = self.calculate_video_duration(template, len(photos))
            print(f"✅ Duração total: {total_duration:.1f} segundos ({total_duration/60:.1f} minutos)")
            
            # Criar breakdown das cenas
            scenes_breakdown = self.create_scene_breakdown(template, photos)
            print(f"✅ Breakdown das cenas:")
            for i, scene in enumerate(scenes_breakdown):
                print(f"   Cena {i+1}: {scene['scene_name']}")
                print(f"     Tipo: {scene['scene_type']}")
                print(f"     Tempo: {scene['start_time']:.1f}s - {scene['end_time']:.1f}s")
                print(f"     Duração: {scene['duration']:.1f}s")
                if 'photo_index' in scene:
                    print(f"     Foto: {scene['photo_index'] + 1}")
                print(f"     Efeitos: {len(scene['effects'])}")
            
            # Gerar script FFmpeg
            output_path = str(self.videos_dir / f"{job_id}_test_output.mp4")
            script = self.generate_video_script(template, photos, output_path)
            
            script_file = self.videos_dir / f"{job_id}_ffmpeg_script.sh"
            with open(script_file, 'w', encoding='utf-8') as f:
                f.write(script)
            
            print(f"✅ Script FFmpeg gerado: {script_file}")
            print(f"✅ Arquivo de saída: {output_path}")
            
            # Salvar breakdown em JSON
            breakdown_file = self.videos_dir / f"{job_id}_breakdown.json"
            with open(breakdown_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "job_id": job_id,
                    "template": {
                        "id": template.id,
                        "name": template.name,
                        "description": template.description
                    },
                    "photos": photos,
                    "total_duration": total_duration,
                    "scenes_breakdown": scenes_breakdown
                }, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Breakdown salvo: {breakdown_file}")
            
            print("\n🎬 Para gerar o vídeo, execute:")
            print(f"   chmod +x {script_file}")
            print(f"   {script_file}")
            
        except Exception as e:
            print(f"❌ Erro: {e}")
            import traceback
            traceback.print_exc()

def main():
    if len(sys.argv) < 2:
        print("Uso: python scripts/test_template.py <job_id> [template_id]")
        print("\nTemplates disponíveis:")
        for template in AVAILABLE_TEMPLATES:
            print(f"  - {template.id}: {template.name}")
        return
    
    job_id = sys.argv[1]
    template_id = sys.argv[2] if len(sys.argv) > 2 else None
    
    tester = TemplateTester()
    tester.test_template(job_id, template_id)

if __name__ == "__main__":
    main()
