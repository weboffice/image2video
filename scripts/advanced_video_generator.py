#!/usr/bin/env python3
"""
Script avançado para gerar vídeo usando templates com efeitos.
Uso: python scripts/advanced_video_generator.py <job_id> [template_id]
"""

import sys
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Tuple
import math

# Adicionar o diretório backend ao path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from main import AVAILABLE_TEMPLATES

class AdvancedVideoGenerator:
    def __init__(self):
        self.storage_dir = Path(__file__).parent.parent / "backend" / "storage"
        self.videos_dir = self.storage_dir / "videos"
        self.temp_dir = Path(tempfile.gettempdir()) / "advanced_video_generator"
        self.temp_dir.mkdir(exist_ok=True)
        
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
        
        try:
            config = self.load_job_config(job_id)
            if 'photos' in config:
                for photo_info in config['photos']:
                    if 'filePath' in photo_info:
                        photo_path = self.storage_dir / photo_info['filePath']
                        if photo_path.exists():
                            photos.append(str(photo_path))
                        else:
                            print(f"⚠️  Foto não encontrada: {photo_path}")
        except Exception as e:
            print(f"⚠️  Erro ao carregar configuração: {e}")
        
        return sorted(photos)
    
    def create_grid_scene(self, photos: List[str], duration: float = 8.0, 
                          grid_cols: int = 3, grid_rows: int = 2) -> str:
        """Cria cena de grade com as fotos"""
        if len(photos) == 0:
            raise ValueError("Nenhuma foto fornecida")
        
        # Redimensionar fotos para o mesmo tamanho
        cell_width = 640  # Tamanho da célula
        cell_height = 480
        
        resized_photos = []
        for i, photo in enumerate(photos[:grid_cols * grid_rows]):
            resized_photo = self.temp_dir / f"grid_resized_{i:02d}.jpg"
            
            # Redimensionar foto
            cmd = [
                "ffmpeg", "-y",
                "-i", photo,
                "-vf", f"scale={cell_width}:{cell_height}:force_original_aspect_ratio=decrease,pad={cell_width}:{cell_height}:(ow-iw)/2:(oh-ih)/2:color=black",
                "-q:v", "2",
                str(resized_photo)
            ]
            
            try:
                subprocess.run(cmd, check=True, capture_output=True)
                resized_photos.append(str(resized_photo))
            except subprocess.CalledProcessError:
                print(f"⚠️  Erro ao redimensionar {os.path.basename(photo)}")
                continue
        
        if not resized_photos:
            raise ValueError("Nenhuma foto foi redimensionada com sucesso")
        
        # Preencher células vazias
        while len(resized_photos) < grid_cols * grid_rows:
            resized_photos.append(resized_photos[len(resized_photos) % len(resized_photos)])
        
        # Criar layout de grade usando montage (ImageMagick) ou fallback para FFmpeg
        grid_output = self.temp_dir / "grid_layout.jpg"
        
        try:
            # Tentar usar ImageMagick montage
            montage_cmd = ["montage"] + resized_photos[:grid_cols * grid_rows] + [
                "-tile", f"{grid_cols}x{grid_rows}",
                "-geometry", f"{cell_width}x{cell_height}+10+10",
                "-background", "black",
                str(grid_output)
            ]
            subprocess.run(montage_cmd, check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback: usar apenas a primeira foto
            print("⚠️  ImageMagick não disponível, usando primeira foto")
            grid_output = Path(resized_photos[0])
        
        # Criar vídeo da grade (forçar 1920x1080 e aplicar fade dinâmico)
        grid_video = self.temp_dir / "grid_scene.mp4"
        fade_out_start = max(0.0, duration - 2.0)
        
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(grid_output),
            "-t", str(duration),
            "-r", "30",
            "-vf", f"scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black,fade=t=in:st=0:d=2,fade=t=out:st={fade_out_start}:d=2",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            str(grid_video)
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        return str(grid_video)
     
    def create_zoom_scene(self, photo: str, duration: float = 4.0, 
                          zoom_start: float = 1.0, zoom_end: float = 1.3) -> str:
        """Cria cena de zoom em uma foto"""
        zoom_output = self.temp_dir / f"zoom_{os.path.basename(photo)}.mp4"
        
        # Usar filtro simples e forçar 1920x1080 ao final
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", photo,
            "-t", str(duration),
            "-r", "30",
            "-vf", f"scale=iw*{zoom_end}:ih*{zoom_end},scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            str(zoom_output)
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return str(zoom_output)
        except subprocess.CalledProcessError:
            # Fallback: sem zoom, mas mantendo 16:9
            print(f"⚠️  Fallback para sem zoom em {os.path.basename(photo)}")
            cmd_fallback = [
                "ffmpeg", "-y",
                "-loop", "1",
                "-i", photo,
                "-t", str(duration),
                "-r", "30",
                "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black",
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", "23",
                "-pix_fmt", "yuv420p",
                str(zoom_output)
            ]
            subprocess.run(cmd_fallback, check=True, capture_output=True)
            return str(zoom_output)
    
    def generate_video(self, job_id: str, template_id: str = None):
        """Gera vídeo completo usando template"""
        print(f"🎬 Gerando vídeo avançado para job: {job_id}")
        print("=" * 50)
        
        try:
            # Carregar configuração e fotos
            config = self.load_job_config(job_id)
            photos = self.get_job_photos(job_id)
            
            if not photos:
                print("❌ Nenhuma foto encontrada")
                return
            
            # Determinar template
            if template_id:
                template = self.get_template_by_id(template_id)
            else:
                if 'template' in config and 'id' in config['template']:
                    template_id = config['template']['id']
                else:
                    template_id = 'grid-showcase-template'
                
                template = self.get_template_by_id(template_id)
            
            if not template:
                print(f"❌ Template '{template_id}' não encontrado")
                return
            
            print(f"✅ Template: {template.name}")
            print(f"✅ Fotos: {len(photos)}")
            
            # Gerar segmentos de vídeo
            video_segments = []
            current_time = 0
            
            for scene in template.scenes:
                print(f"🎭 Processando cena: {scene.name}")
                
                if scene.type == 'grid':
                    # Cena de grade
                    grid_params = next((effect.parameters for effect in scene.effects 
                                      if effect.type == 'fade' and 'grid_columns' in effect.parameters), {})
                    grid_cols = grid_params.get('grid_columns', 3)
                    grid_rows = grid_params.get('grid_rows', 2)
                    
                    print(f"   Criando grade {grid_cols}x{grid_rows}")
                    segment = self.create_grid_scene(photos, scene.duration, grid_cols, grid_rows)
                    video_segments.append(segment)
                    current_time += scene.duration
                    
                elif scene.type == 'zoom':
                    # Cena de zoom individual
                    photos_in_scene = min(len(photos), scene.max_photos)
                    
                    for i in range(photos_in_scene):
                        zoom_params = next((effect.parameters for effect in scene.effects 
                                          if effect.type == 'zoom'), {})
                        zoom_start = zoom_params.get('zoom_start', 1.0)
                        zoom_end = zoom_params.get('zoom_end', 1.3)
                        
                        print(f"   Processando zoom na foto {i+1}: {os.path.basename(photos[i])}")
                        segment = self.create_zoom_scene(
                            photos[i], scene.duration, zoom_start, zoom_end
                        )
                        video_segments.append(segment)
                        current_time += scene.duration
                
                elif scene.type == 'thumbnail':
                    # Cena de thumbnails - usar primeira foto
                    print(f"   Usando primeira foto para thumbnails")
                    segment = self.create_zoom_scene(photos[0], scene.duration, 1.0, 1.0)
                    video_segments.append(segment)
                    current_time += scene.duration
            
            # Combinar todos os segmentos
            if not video_segments:
                print("❌ Nenhum segmento de vídeo gerado")
                return
            
            # Criar arquivo de lista para concatenação
            concat_file = self.temp_dir / "concat_list.txt"
            with open(concat_file, 'w') as f:
                for segment in video_segments:
                    f.write(f"file '{segment}'\n")
            
            # Definir nome do arquivo de saída
            output_path = self.videos_dir / f"{job_id}_advanced.mp4"
            
            # Concatenar segmentos
            print("🔗 Concatenando segmentos...")
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_file),
                "-c", "copy",
                str(output_path)
            ]
            
            subprocess.run(cmd, check=True)
            
            print(f"✅ Vídeo gerado com sucesso: {output_path}")
            print(f"📊 Duração: {current_time:.1f} segundos")
            print(f"📁 Tamanho: {output_path.stat().st_size / (1024*1024):.1f} MB")
            
            # Limpar arquivos temporários
            print("🧹 Limpando arquivos temporários...")
            for segment in video_segments:
                try:
                    os.remove(segment)
                except:
                    pass
            
            try:
                os.remove(concat_file)
            except:
                pass
            
            print("🎉 Processo concluído!")
            
        except Exception as e:
            print(f"❌ Erro: {e}")
            import traceback
            traceback.print_exc()

def main():
    if len(sys.argv) < 2:
        print("Uso: python scripts/advanced_video_generator.py <job_id> [template_id]")
        print("\nTemplates disponíveis:")
        for template in AVAILABLE_TEMPLATES:
            print(f"  - {template.id}: {template.name}")
        return
    
    job_id = sys.argv[1]
    template_id = sys.argv[2] if len(sys.argv) > 2 else None
    
    generator = AdvancedVideoGenerator()
    generator.generate_video(job_id, template_id)

if __name__ == "__main__":
    main()
