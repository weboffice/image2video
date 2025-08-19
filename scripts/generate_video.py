#!/usr/bin/env python3
"""
Script para gerar vídeo usando templates.
Uso: python scripts/generate_video.py <job_id> [template_id]
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

from templates import TEMPLATES

# Imports para MinIO
try:
    from backend.minio_client import minio_client
except ImportError:
    from minio_client import minio_client

class VideoGenerator:
    def __init__(self):
        self.storage_dir = Path(__file__).parent.parent / "backend" / "storage"
        self.videos_dir = self.storage_dir / "videos"
        self.photos_dir = self.storage_dir / "photos"
        self.temp_dir = Path(tempfile.gettempdir()) / "video_generator"
        self.temp_dir.mkdir(exist_ok=True)
        
    def get_template_by_id(self, template_id: str):
        """Busca template pelo ID"""
        return TEMPLATES.get(template_id)
    
    def load_job_config(self, job_id: str) -> Dict[str, Any]:
        """Carrega configuração do job"""
        job_dir = self.videos_dir / job_id
        config_file = job_dir / f"{job_id}_config.json"
        
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
    
    def create_grid_layout(self, photos: List[str], grid_cols: int, grid_rows: int, 
                          spacing: int = 15, output_size: Tuple[int, int] = (1920, 1080)) -> str:
        """Cria layout de grade usando FFmpeg"""
        if len(photos) == 0:
            raise ValueError("Nenhuma foto fornecida")
        
        # Redimensionar todas as fotos para o mesmo tamanho
        cell_width = (output_size[0] - (grid_cols + 1) * spacing) // grid_cols
        cell_height = (output_size[1] - (grid_rows + 1) * spacing) // grid_rows
        
        resized_photos = []
        for i, photo in enumerate(photos[:grid_cols * grid_rows]):
            resized_photo = self.temp_dir / f"resized_{i:02d}.jpg"
            
            # Redimensionar foto para caber na célula
            cmd = [
                "ffmpeg", "-y",
                "-i", photo,
                "-vf", f"scale={cell_width}:{cell_height}:force_original_aspect_ratio=decrease,pad={cell_width}:{cell_height}:(ow-iw)/2:(oh-ih)/2:color=black",
                "-q:v", "2",
                str(resized_photo)
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            resized_photos.append(str(resized_photo))
        
        # Preencher células vazias com fotos existentes
        while len(resized_photos) < grid_cols * grid_rows:
            resized_photos.append(resized_photos[len(resized_photos) % len(photos)])
        
        # Criar layout de grade
        grid_output = self.temp_dir / "grid_layout.jpg"
        
        # Construir comando para criar grade
        inputs = []
        for photo in resized_photos:
            inputs.extend(["-i", photo])
        
        # Criar filtro complexo para grade
        filter_complex = []
        for i in range(grid_cols * grid_rows):
            filter_complex.append(f"[{i}:v]")
        
        # Posicionar cada foto na grade
        positions = []
        for row in range(grid_rows):
            for col in range(grid_cols):
                index = row * grid_cols + col
                x = col * (cell_width + spacing) + spacing
                y = row * (cell_height + spacing) + spacing
                positions.append(f"[{index}]setpts=PTS-STARTPTS[img{index}]")
        
        # Combinar todas as imagens
        combine_inputs = []
        for i in range(grid_cols * grid_rows):
            combine_inputs.append(f"[img{i}]")
        
        filter_complex.extend(positions)
        filter_complex.append(f"{''.join(combine_inputs)}concat=n={len(combine_inputs)}:v=1:a=0[out]")
        
        cmd = ["ffmpeg", "-y"] + inputs + [
            "-filter_complex", ";".join(filter_complex),
            "-map", "[out]",
            "-q:v", "2",
            str(grid_output)
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return str(grid_output)
        except subprocess.CalledProcessError as e:
            print(f"Erro ao criar grade: {e}")
            # Fallback: usar apenas a primeira foto
            return resized_photos[0] if resized_photos else photos[0]
    
    def create_zoom_effect(self, photo: str, zoom_start: float = 1.0, zoom_end: float = 1.3, 
                          duration: float = 4.0, fps: int = 30, pan_x: float = 0.0, pan_y: float = 0.0) -> str:
        """Cria efeito de zoom com Ken Burns em uma foto"""
        frames = int(duration * fps)
        
        # Criar uma versão temporária do arquivo com nome simples
        temp_input = self.temp_dir / f"input_{abs(hash(photo)) % 10000}.jpg"
        subprocess.run(["cp", photo, str(temp_input)], check=True)
        
        zoom_output = self.temp_dir / f"zoom_{abs(hash(photo)) % 10000}.mp4"
        
        # Criar efeito de zoom e pan com Ken Burns - formato 16:9
        # Zoom formula: scale=iw*z:ih*z onde z varia de zoom_start para zoom_end
        # Pan formula: crop com movimento
        zoom_filter = (
            f"scale=1920:1080:force_original_aspect_ratio=increase,"
            f"crop=1920:1080,"
            f"zoompan=z='if(lte(zoom,1.0),{zoom_start},{zoom_start}+({zoom_end}-{zoom_start})*(on-1)/({frames}-1))'"
            f":x='iw/2-(iw/zoom/2)+{pan_x}*iw/zoom'"
            f":y='ih/2-(ih/zoom/2)+{pan_y}*ih/zoom'"
            f":d={frames}"
            f":s=1920x1080:fps={fps}"
        )
        
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(temp_input),
            "-vf", zoom_filter,
            "-t", str(duration),
            "-r", str(fps),
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            str(zoom_output)
        ]
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True)
            return str(zoom_output)
        except subprocess.CalledProcessError as e:
            # Fallback: usar zoom simples sem Ken Burns
            print(f"⚠️  Fallback para zoom simples em {os.path.basename(photo)}")
            cmd_fallback = [
                "ffmpeg", "-y",
                "-loop", "1",
                "-i", str(temp_input),
                "-vf", f"scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,scale=iw*{zoom_end}:ih*{zoom_end}",
                "-t", str(duration),
                "-r", str(fps),
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                "-pix_fmt", "yuv420p",
                str(zoom_output)
            ]
            subprocess.run(cmd_fallback, check=True, capture_output=True)
            return str(zoom_output)
    
    def create_fade_effect(self, photo: str, duration: float = 2.0, fps: int = 30) -> str:
        """Cria efeito de fade-in em formato 16:9"""
        # Criar uma versão temporária do arquivo com nome simples
        temp_input = self.temp_dir / f"input_{abs(hash(photo)) % 10000}.jpg"
        subprocess.run(["cp", photo, str(temp_input)], check=True)
        
        fade_output = self.temp_dir / f"fade_{abs(hash(photo)) % 10000}.mp4"
        
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(temp_input),
            "-vf", f"scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fade=t=in:st=0:d={min(duration, 1.0)}",
            "-t", str(duration),
            "-r", str(fps),
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            str(fade_output)
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        return str(fade_output)
    
    def create_grid_video(self, photos: List[str], grid_cols: int, grid_rows: int, 
                         duration: float = 8.0, fps: int = 30) -> str:
        """Cria vídeo com layout de grade das fotos em formato 16:9"""
        if len(photos) == 0:
            raise ValueError("Nenhuma foto fornecida")
        
        grid_output = self.temp_dir / f"grid_{abs(hash(''.join(photos))) % 10000}.mp4"
        
        # Usar apenas as fotos necessárias para a grade
        num_cells = grid_cols * grid_rows
        selected_photos = photos[:num_cells]
        
        # Preencher células vazias repetindo fotos se necessário
        while len(selected_photos) < num_cells:
            selected_photos.extend(photos[:min(len(photos), num_cells - len(selected_photos))])
        
        # Construir inputs do FFmpeg
        inputs = []
        for photo in selected_photos:
            inputs.extend(["-i", photo])
        
        # Criar filtro complexo para grade
        cell_width = 1920 // grid_cols
        cell_height = 1080 // grid_rows
        
        # Redimensionar cada input
        filter_parts = []
        for i in range(len(selected_photos)):
            filter_parts.append(
                f"[{i}:v]scale={cell_width}:{cell_height}:force_original_aspect_ratio=increase,"
                f"crop={cell_width}:{cell_height}[img{i}]"
            )
        
        # Posicionar imagens na grade
        overlay_parts = ["color=black:1920x1080:d={duration}[base]".format(duration=duration)]
        current = "base"
        
        for row in range(grid_rows):
            for col in range(grid_cols):
                idx = row * grid_cols + col
                if idx < len(selected_photos):
                    x = col * cell_width
                    y = row * cell_height
                    next_name = f"tmp{idx}" if idx < len(selected_photos) - 1 else "out"
                    overlay_parts.append(f"[{current}][img{idx}]overlay={x}:{y}[{next_name}]")
                    current = next_name
        
        filter_complex = ";".join(filter_parts + overlay_parts)
        
        cmd = ["ffmpeg", "-y"] + inputs + [
            "-filter_complex", filter_complex,
            "-map", "[out]",
            "-t", str(duration),
            "-r", str(fps),
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            str(grid_output)
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return str(grid_output)
        except subprocess.CalledProcessError as e:
            # Fallback: usar apenas a primeira foto
            print(f"⚠️  Erro ao criar grade, usando primeira foto")
            return self.create_fade_effect(photos[0], duration, fps)
    
    def add_background_audio(self, video_path: str, output_path: Path, duration: float):
        """Adiciona áudio de fundo ao vídeo"""
        # Caminho para o áudio de fundo (usar versão limpa sem metadados)
        audio_path = self.storage_dir.parent / "assets" / "source_bg_clean.mp3"
        
        if not audio_path.exists():
            print("🔇 Áudio de fundo não encontrado, criando vídeo sem áudio")
            # Apenas copiar o vídeo sem áudio
            subprocess.run(["cp", str(video_path), str(output_path)], check=True)
            return
        
        print(f"🎵 Adicionando áudio de fundo: {audio_path}")
        
        # Comando FFmpeg para adicionar áudio de fundo
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),  # Vídeo de entrada
            "-i", str(audio_path),  # Áudio de fundo
            "-c:v", "copy",  # Copiar vídeo sem recodificar
            "-c:a", "aac",   # Codificar áudio como AAC
            "-b:a", "128k",  # Bitrate do áudio
            "-shortest",     # Terminar quando o stream mais curto acabar
            "-filter_complex", f"[1:a]volume=0.3,afade=t=in:st=0:d=2,afade=t=out:st={duration-2}:d=2[audio_out]",
            "-map", "0:v",   # Mapear vídeo do primeiro input
            "-map", "[audio_out]",  # Mapear áudio processado
            str(output_path)
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            print("✅ Áudio de fundo adicionado com sucesso")
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Erro ao adicionar áudio, criando vídeo sem áudio: {e}")
            # Fallback: copiar vídeo sem áudio
            subprocess.run(["cp", str(video_path), str(output_path)], check=True)
        
        # Limpar arquivo temporário
        try:
            os.remove(video_path)
        except:
            pass
    
    def generate_video(self, job_id: str, template_id: str = None, output_name: str = None):
        """Gera vídeo completo usando template"""
        print(f"🎬 Gerando vídeo para job: {job_id}")
        print("=" * 50)
        
        try:
            # Carregar configuração e fotos (configuração é opcional)
            config = {}
            try:
                config = self.load_job_config(job_id)
                print("✅ Configuração carregada do arquivo")
            except FileNotFoundError:
                print("⚠️  Arquivo de configuração não encontrado, usando configuração padrão")
            
            photos = self.get_job_photos(job_id)
            
            if not photos:
                print("❌ Nenhuma foto encontrada")
                return
            
            # Determinar template
            if template_id:
                template = self.get_template_by_id(template_id)
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
            
            print(f"✅ Template: {template['name']}")
            print(f"✅ Fotos: {len(photos)}")
            
            # Gerar segmentos de vídeo
            video_segments = []
            current_time = 0
            
            for scene in template['scenes']:
                print(f"🎭 Processando cena: {scene['name']}")
                
                if scene['type'] in ['thumbnail', 'grid']:
                    # Buscar parâmetros da grade
                    grid_params = next((effect['parameters'] for effect in scene['effects'] 
                                      if effect['type'] == 'fade' and 'grid_columns' in effect['parameters']), {})
                    
                    if grid_params:
                        grid_cols = grid_params.get('grid_columns', 3)
                        grid_rows = grid_params.get('grid_rows', 2)
                        print(f"   Criando grade {grid_cols}x{grid_rows} com {len(photos)} fotos")
                        segment = self.create_grid_video(photos, grid_cols, grid_rows, scene['duration'])
                    else:
                        print(f"   Criando cena de fade simples")
                        segment = self.create_fade_effect(photos[0], scene['duration'])
                    
                    video_segments.append(segment)
                    current_time += scene['duration']
                    
                elif scene['type'] == 'zoom':
                    # Cena de zoom individual com efeitos
                    photos_in_scene = min(len(photos), scene['max_photos'])
                    
                    for i in range(photos_in_scene):
                        # Buscar parâmetros de zoom
                        zoom_params = next((effect['parameters'] for effect in scene['effects'] 
                                          if effect['type'] == 'zoom'), {})
                        zoom_start = zoom_params.get('zoom_start', 1.0)
                        zoom_end = zoom_params.get('zoom_end', 1.3)
                        
                        # Buscar parâmetros de pan
                        pan_params = next((effect['parameters'] for effect in scene['effects'] 
                                         if effect['type'] == 'pan'), {})
                        pan_x = pan_params.get('pan_end', {}).get('x', 0.0) if pan_params else 0.0
                        pan_y = pan_params.get('pan_end', {}).get('y', 0.0) if pan_params else 0.0
                        
                        print(f"   Zoom na foto {i+1} (z:{zoom_start}->{zoom_end}, pan:{pan_x},{pan_y}): {os.path.basename(photos[i])}")
                        segment = self.create_zoom_effect(
                            photos[i], zoom_start, zoom_end, scene['duration'], 30, pan_x, pan_y
                        )
                        video_segments.append(segment)
                        current_time += scene['duration']
                
                elif scene['type'] in ['fade', 'ken_burns', 'showcase', 'finale']:
                    # Cenas especiais com efeitos específicos
                    photos_in_scene = min(len(photos), scene['max_photos'])
                    
                    for i in range(photos_in_scene):
                        # Buscar parâmetros específicos
                        zoom_params = next((effect['parameters'] for effect in scene['effects'] 
                                          if effect['type'] == 'zoom'), {})
                        zoom_start = zoom_params.get('zoom_start', 1.2)
                        zoom_end = zoom_params.get('zoom_end', 1.8)
                        
                        pan_params = next((effect['parameters'] for effect in scene['effects'] 
                                         if effect['type'] == 'pan'), {})
                        pan_x = pan_params.get('pan_end', {}).get('x', 0.1) if pan_params else 0.1
                        pan_y = pan_params.get('pan_end', {}).get('y', 0.1) if pan_params else 0.1
                        
                        print(f"   Cena {scene['type']} na foto {i+1}: {os.path.basename(photos[i])}")
                        segment = self.create_zoom_effect(
                            photos[i], zoom_start, zoom_end, scene['duration'], 30, pan_x, pan_y
                        )
                        video_segments.append(segment)
                        current_time += scene['duration']
            
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
            if not output_name:
                output_name = f"{job_id}_generated.mp4"
            
            # Salvar no diretório específico do job
            job_dir = self.videos_dir / job_id
            job_dir.mkdir(parents=True, exist_ok=True)
            output_path = job_dir / output_name
            
            # Concatenar segmentos
            print("🔗 Concatenando segmentos...")
            
            # Primeiro, criar vídeo sem áudio
            temp_video = self.temp_dir / f"{job_id}_temp_video.mp4"
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_file),
                "-c", "copy",
                str(temp_video)
            ]
            
            subprocess.run(cmd, check=True)
            
            # Adicionar áudio de fundo se disponível
            self.add_background_audio(temp_video, output_path, current_time)
            
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
            
            # Limpar arquivos temporários do MinIO
            for photo in photos:
                if photo.startswith(str(self.storage_dir / "temp_")):
                    try:
                        os.remove(photo)
                        print(f"🧹 Limpo arquivo temporário: {os.path.basename(photo)}")
                    except:
                        pass
            
            print("🎉 Processo concluído!")
            
        except Exception as e:
            print(f"❌ Erro: {e}")
            import traceback
            traceback.print_exc()

def main():
    if len(sys.argv) < 2:
        print("Uso: python scripts/generate_video.py <job_id> [template_id] [output_name]")
        print("\nTemplates disponíveis:")
        for template_id, template in TEMPLATES.items():
            print(f"  - {template_id}: {template['name']}")
        return
    
    job_id = sys.argv[1]
    template_id = sys.argv[2] if len(sys.argv) > 2 else None
    output_name = sys.argv[3] if len(sys.argv) > 3 else None
    
    generator = VideoGenerator()
    generator.generate_video(job_id, template_id, output_name)

if __name__ == "__main__":
    main()
