"""
MoviePy Video Editor
Classe para processamento de vídeo usando MoviePy como alternativa ao FFmpeg
"""

import os
import logging
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import json

# Import para banco de dados e otimizações
try:
    from .video_config_db import update_video_config
    from .video_optimization import optimize_photos_for_video, get_moviepy_optimization_settings, cleanup_optimized_photos
except ImportError:
    from video_config_db import update_video_config
    from video_optimization import optimize_photos_for_video, get_moviepy_optimization_settings, cleanup_optimized_photos

# Imports do MoviePy
from moviepy.editor import (
    VideoFileClip, ImageClip, CompositeVideoClip, AudioFileClip,
    concatenate_videoclips, CompositeAudioClip, ColorClip
)
import moviepy.video.fx.all as vfx
import moviepy.audio.fx.all as afx

# Imports resilientes para MinIO
try:
    from .minio_client import minio_client
except ImportError:
    from minio_client import minio_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MoviePyEditor:
    """Editor de vídeo usando MoviePy"""
    
    def __init__(self, storage_dir: Path):
        self.storage_dir = storage_dir
        self.videos_dir = storage_dir / "videos"
        # Corrigir caminho para assets - está em backend/assets
        self.assets_dir = Path(__file__).parent / "assets"
        
        # Configurar diretório temporário do MoviePy
        self.temp_dir = storage_dir / "temp"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Configurar variáveis de ambiente para MoviePy usar nosso diretório temporário
        os.environ['TMPDIR'] = str(self.temp_dir)
        os.environ['TEMP'] = str(self.temp_dir)
        os.environ['TMP'] = str(self.temp_dir)
        
        # Configurar tempfile para usar nosso diretório
        tempfile.tempdir = str(self.temp_dir)
        
        logger.info(f"🗂️ Diretório temporário do MoviePy configurado: {self.temp_dir}")
        
        # Configurações padrão otimizadas para performance
        self.default_fps = 24  # FPS otimizado
        self.default_resolution = (1280, 720)  # 720p para melhor performance
        self.background_audio_volume = 0.3
        
    def create_video_from_config(self, config_path: Path) -> Dict[str, Any]:
        """Cria um vídeo baseado na configuração fornecida"""
        try:
            # Carregar configuração
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            job_id = config['job_id']
            template = config['template']
            photos = config['photos']
            output_format = config['output_format']
            resolution = config['resolution']
            fps = config['fps']
            background_audio = config.get('background_audio', True)
            
            logger.info(f"🎬 Iniciando criação do vídeo {job_id} com MoviePy")
            
            # Atualizar status para processing
            self._update_status(config_path, "processing", 5)
            
            # Criar diretório do job
            job_dir = self.videos_dir / job_id
            job_dir.mkdir(parents=True, exist_ok=True)
            output_path = job_dir / f"{job_id}_video.{output_format}"
            
            # Obter dimensões do vídeo
            width, height = self._get_resolution_dimensions(resolution)
            
            # Processar fotos e criar clips
            photo_clips = self._create_photo_clips(photos, template, width, height, fps, config)
            
            if not photo_clips:
                error_msg = "Nenhuma foto válida encontrada para criar o vídeo"
                logger.error(error_msg)
                self._update_status(config_path, "error", 0, error_msg)
                return {"success": False, "error": error_msg}
            
            self._update_status(config_path, "processing", 25)
            
            # Concatenar clips de vídeo
            logger.info("🔗 Concatenando clips de vídeo...")
            final_video = concatenate_videoclips(photo_clips, method="compose")
            
            self._update_status(config_path, "processing", 50)
            
            # Adicionar áudio de fundo se habilitado
            if background_audio:
                final_video = self._add_background_audio(final_video, job_id, template)
            
            self._update_status(config_path, "processing", 75)
            
            # Exportar vídeo final
            logger.info(f"💾 Exportando vídeo para {output_path}")
            
            # Configurar logging do MoviePy para evitar problemas
            import logging as mp_logging
            mp_logging.getLogger('moviepy').setLevel(mp_logging.WARNING)
            
            # 🚀 OTIMIZAÇÃO: Usar configurações otimizadas do MoviePy
            preset = config.get('quality_preset', 'fast')
            if preset not in ['fast', 'balanced', 'high_quality']:
                preset = "fast" if width <= 1280 else "balanced" if width <= 1920 else "high_quality"
            
            optimization_settings = get_moviepy_optimization_settings(preset)
            
            logger.info(f"🚀 Exportando com preset de otimização: {preset}")
            
            try:
                final_video.write_videofile(
                    str(output_path),
                    fps=optimization_settings['fps'],
                    codec=optimization_settings['codec'],
                    preset=optimization_settings['preset'],
                    ffmpeg_params=optimization_settings['ffmpeg_params'],
                    audio_codec='aac' if background_audio else None,
                    verbose=False,
                    logger=None,
                    temp_audiofile=None  # Não usar arquivo temporário de áudio
                )
            except Exception as e:
                # Fallback: tentar sem áudio se houver problema
                logger.warning(f"Erro na exportação com áudio, tentando sem áudio: {e}")
                if background_audio:
                    final_video_no_audio = final_video.without_audio()
                    final_video_no_audio.write_videofile(
                        str(output_path),
                        fps=optimization_settings['fps'],
                        codec=optimization_settings['codec'],
                        preset=optimization_settings['preset'],
                        ffmpeg_params=optimization_settings['ffmpeg_params'],
                        verbose=False,
                        logger=None
                    )
                    final_video_no_audio.close()
                else:
                    raise e
            
            # Limpar recursos
            final_video.close()
            for clip in photo_clips:
                clip.close()
            
            # Limpar fotos temporárias
            self._cleanup_temp_photos()
            
            # Limpar arquivos temporários do MoviePy
            self._cleanup_moviepy_temp_files()
            
            self._update_status(config_path, "completed", 100, output_path=str(output_path))
            
            logger.info(f"✅ Vídeo criado com sucesso: {output_path}")
            return {
                "success": True,
                "output_path": str(output_path),
                "duration": final_video.duration
            }
            
        except Exception as e:
            error_msg = f"Erro ao criar vídeo com MoviePy: {str(e)}"
            logger.error(error_msg)
            
            # Limpar fotos temporárias mesmo em caso de erro
            self._cleanup_temp_photos()
            
            # Limpar arquivos temporários do MoviePy mesmo em caso de erro
            self._cleanup_moviepy_temp_files()
            
            self._update_status(config_path, "error", 0, error_msg)
            return {"success": False, "error": error_msg}
    
    def _download_photos_from_minio(self, photos: List[Dict]) -> List[str]:
        """Baixa fotos do MinIO para processamento local"""
        photo_paths = []
        temp_dir = self.storage_dir / "temp_photos"
        temp_dir.mkdir(exist_ok=True)
        
        for photo in photos:
            object_key = photo['filePath']
            filename = Path(object_key).name
            local_path = temp_dir / filename
            
            # Primeiro, tentar encontrar no sistema local
            local_storage_path = self.storage_dir / object_key
            if local_storage_path.exists():
                photo_paths.append(str(local_storage_path))
                logger.info(f"✅ Foto encontrada localmente: {local_storage_path}")
                continue
            
            # Se não encontrar localmente, baixar do MinIO
            try:
                if minio_client.download_file(object_key, local_path):
                    photo_paths.append(str(local_path))
                    logger.info(f"✅ Foto baixada do MinIO: {object_key} -> {local_path}")
                else:
                    logger.warning(f"❌ Falha ao baixar foto do MinIO: {object_key}")
            except Exception as e:
                logger.error(f"❌ Erro ao baixar foto {object_key}: {e}")
                
        return photo_paths

    def _create_photo_clips(self, photos: List[Dict], template: Dict, 
                           width: int, height: int, fps: int, config: Dict = None) -> List[VideoFileClip]:
        """Cria clips de vídeo a partir das fotos baseado no template"""
        clips = []
        
        # Baixar fotos do MinIO se necessário
        photo_paths = self._download_photos_from_minio(photos)
        
        if not photo_paths:
            logger.error("❌ Nenhuma foto válida encontrada")
            return []
        
        # 🚀 OTIMIZAÇÃO: Redimensionar fotos proporcionalmente para melhor performance
        logger.info("🚀 Otimizando fotos para melhor performance...")
        try:
            # Usar preset da configuração ou determinar baseado na resolução
            preset = config.get('quality_preset', 'fast')
            if preset not in ['fast', 'balanced', 'high_quality']:
                preset = "fast" if width <= 1280 else "balanced" if width <= 1920 else "high_quality"
            
            # Otimizar fotos
            optimized_photo_paths = optimize_photos_for_video(
                photo_paths, 
                preset=preset,
                temp_dir=self.temp_dir / "optimized"
            )
            
            if optimized_photo_paths:
                photo_paths = optimized_photo_paths
                logger.info(f"✅ {len(photo_paths)} fotos otimizadas com preset '{preset}'")
            else:
                logger.warning("⚠️  Falha na otimização, usando fotos originais")
                
        except Exception as e:
            logger.warning(f"⚠️  Erro na otimização de fotos: {e}, usando fotos originais")
        
        # Processar cenas do template
        template_id = template.get('id', '')
        
        for scene in template['scenes']:
            scene_clips = self._create_scene_clips(
                photo_paths, scene, template_id, width, height, fps
            )
            clips.extend(scene_clips)
        
        return clips
    
    def _cleanup_temp_photos(self):
        """Remove fotos temporárias baixadas do MinIO"""
        temp_dir = self.storage_dir / "temp_photos"
        if temp_dir.exists():
            try:
                import shutil
                shutil.rmtree(temp_dir)
                logger.info("🧹 Fotos temporárias removidas")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao remover fotos temporárias: {e}")
    
    def _cleanup_moviepy_temp_files(self):
        """Remove arquivos temporários criados pelo MoviePy"""
        if self.temp_dir.exists():
            try:
                import shutil
                # Listar arquivos temporários antes de remover
                temp_files = list(self.temp_dir.glob("*"))
                if temp_files:
                    logger.info(f"🧹 Removendo {len(temp_files)} arquivos temporários do MoviePy")
                    for temp_file in temp_files:
                        try:
                            if temp_file.is_file():
                                temp_file.unlink()
                                logger.debug(f"🗑️ Removido: {temp_file.name}")
                            elif temp_file.is_dir():
                                shutil.rmtree(temp_file)
                                logger.debug(f"🗑️ Diretório removido: {temp_file.name}")
                        except Exception as e:
                            logger.warning(f"⚠️ Erro ao remover {temp_file}: {e}")
                    logger.info("✅ Limpeza de arquivos temporários do MoviePy concluída")
                else:
                    logger.debug("📁 Nenhum arquivo temporário do MoviePy encontrado")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao limpar arquivos temporários do MoviePy: {e}")
    
    def _create_scene_clips(self, photo_paths: List[str], scene: Dict, 
                           template_id: str, width: int, height: int, fps: int) -> List[VideoFileClip]:
        """Cria clips para uma cena específica"""
        clips = []
        scene_type = scene['type']
        duration = scene['duration']
        max_photos = scene.get('max_photos', len(photo_paths))
        
        # Limitar fotos para esta cena
        scene_photos = photo_paths[:max_photos]
        
        if scene_type == 'grid':
            # Criar layout de grade
            clip = self._create_grid_clip(scene_photos, scene, width, height, duration, fps)
            if clip:
                clips.append(clip)
                
        elif scene_type in ['zoom', 'fade', 'ken_burns', 'showcase', 'finale']:
            # Criar clips individuais com efeitos
            for i, photo_path in enumerate(scene_photos):
                clip = self._create_photo_clip_with_effects(
                    photo_path, scene, width, height, duration, fps
                )
                if clip:
                    clips.append(clip)
                    
        elif scene_type == 'slideshow':
            # Slideshow simples com fade
            for photo_path in scene_photos:
                clip = self._create_simple_slideshow_clip(
                    photo_path, width, height, duration, fps
                )
                if clip:
                    clips.append(clip)
        
        return clips
    
    def _create_photo_clip_with_effects(self, photo_path: str, scene: Dict, 
                                      width: int, height: int, duration: float, fps: int) -> Optional[VideoFileClip]:
        """Cria um clip de foto com efeitos baseados na cena"""
        try:
            # Criar clip de imagem
            img_clip = ImageClip(photo_path, duration=duration)
            
            # Redimensionar para caber na tela mantendo proporção
            img_clip = img_clip.resize(height=height).resize(
                lambda t: min(width/img_clip.w, height/img_clip.h)
            )
            
            # Centralizar na tela
            img_clip = img_clip.set_position('center')
            
            # Aplicar efeitos baseados na cena
            for effect in scene.get('effects', []):
                img_clip = self._apply_effect(img_clip, effect, duration)
            
            # Criar fundo preto
            bg_clip = ColorClip(size=(width, height), color=(0, 0, 0), duration=duration)
            
            # Compor clip final
            final_clip = CompositeVideoClip([bg_clip, img_clip], size=(width, height))
            final_clip = final_clip.set_fps(fps)
            
            return final_clip
            
        except Exception as e:
            logger.error(f"Erro ao criar clip para {photo_path}: {e}")
            return None
    
    def _create_simple_slideshow_clip(self, photo_path: str, width: int, height: int, 
                                    duration: float, fps: int) -> Optional[VideoFileClip]:
        """Cria um clip simples de slideshow com fade"""
        try:
            # Criar clip de imagem
            img_clip = ImageClip(photo_path, duration=duration)
            
            # Redimensionar e centralizar
            img_clip = img_clip.resize(height=height).resize(
                lambda t: min(width/img_clip.w, height/img_clip.h)
            )
            img_clip = img_clip.set_position('center')
            
            # Adicionar fade in e fade out
            fade_duration = min(0.5, duration / 4)
            img_clip = img_clip.fx(vfx.fadein, fade_duration)
            img_clip = img_clip.fx(vfx.fadeout, fade_duration)
            
            # Criar fundo preto
            bg_clip = ColorClip(size=(width, height), color=(0, 0, 0), duration=duration)
            
            # Compor clip final
            final_clip = CompositeVideoClip([bg_clip, img_clip], size=(width, height))
            final_clip = final_clip.set_fps(fps)
            
            return final_clip
            
        except Exception as e:
            logger.error(f"Erro ao criar slideshow clip para {photo_path}: {e}")
            return None
    
    def _create_grid_clip(self, photo_paths: List[str], scene: Dict, 
                         width: int, height: int, duration: float, fps: int) -> Optional[VideoFileClip]:
        """Cria um clip com layout de grade"""
        try:
            # Buscar parâmetros da grade nos efeitos
            grid_params = {}
            for effect in scene.get('effects', []):
                if effect['type'] == 'fade' and 'grid_columns' in effect.get('parameters', {}):
                    grid_params = effect['parameters']
                    break
            
            grid_cols = grid_params.get('grid_columns', 3)
            grid_rows = grid_params.get('grid_rows', 2)
            
            # Calcular dimensões das células
            cell_width = width // grid_cols
            cell_height = height // grid_rows
            
            # Criar clips para cada foto
            photo_clips = []
            for i, photo_path in enumerate(photo_paths[:grid_cols * grid_rows]):
                try:
                    img_clip = ImageClip(photo_path, duration=duration)
                    
                    # Redimensionar para caber na célula
                    img_clip = img_clip.resize((cell_width, cell_height))
                    
                    # Calcular posição na grade
                    row = i // grid_cols
                    col = i % grid_cols
                    x = col * cell_width
                    y = row * cell_height
                    
                    img_clip = img_clip.set_position((x, y))
                    photo_clips.append(img_clip)
                    
                except Exception as e:
                    logger.warning(f"Erro ao processar foto {photo_path} na grade: {e}")
            
            if not photo_clips:
                return None
            
            # Criar fundo preto
            bg_clip = ColorClip(size=(width, height), color=(0, 0, 0), duration=duration)
            
            # Compor todas as fotos na grade
            final_clip = CompositeVideoClip([bg_clip] + photo_clips, size=(width, height))
            final_clip = final_clip.set_fps(fps)
            
            return final_clip
            
        except Exception as e:
            logger.error(f"Erro ao criar grid clip: {e}")
            return None
    
    def _apply_effect(self, clip: VideoFileClip, effect: Dict, duration: float) -> VideoFileClip:
        """Aplica um efeito específico ao clip"""
        effect_type = effect['type']
        parameters = effect.get('parameters', {})
        
        if effect_type == 'fade':
            fade_duration = min(parameters.get('fade_duration', 0.5), duration / 4)
            clip = clip.fx(vfx.fadein, fade_duration)
            clip = clip.fx(vfx.fadeout, fade_duration)
            
        elif effect_type == 'zoom':
            # Implementar zoom usando resize animado
            zoom_start = parameters.get('zoom_start', 1.0)
            zoom_end = parameters.get('zoom_end', 1.3)
            
            def zoom_function(t):
                progress = t / duration
                current_zoom = zoom_start + (zoom_end - zoom_start) * progress
                return current_zoom
            
            clip = clip.resize(zoom_function)
        
        return clip
    
    def _add_background_audio(self, video_clip: VideoFileClip, job_id: str, template: Dict = None) -> VideoFileClip:
        """Adiciona áudio de fundo ao vídeo"""
        # Usar música específica do template se disponível
        if template and template.get('background_music'):
            audio_filename = template['background_music']
        else:
            audio_filename = "source_bg.mp3"  # Fallback padrão
            
        audio_path = self.assets_dir / audio_filename
        
        if not audio_path.exists():
            logger.warning(f"🔇 Áudio de fundo não encontrado: {audio_path}")
            # Tentar fallback para música padrão
            fallback_path = self.assets_dir / "source_bg.mp3"
            if fallback_path.exists():
                audio_path = fallback_path
                logger.info(f"🎵 Usando música padrão como fallback: {audio_path}")
            else:
                logger.info("🔇 Nenhuma música disponível")
                return video_clip
        
        try:
            logger.info(f"🎵 Adicionando áudio de fundo específico do template: {audio_path}")
            
            # Carregar áudio
            audio_clip = AudioFileClip(str(audio_path))
            
            # Ajustar duração do áudio para o vídeo
            video_duration = video_clip.duration
            if audio_clip.duration > video_duration:
                # Cortar áudio se for mais longo
                audio_clip = audio_clip.subclip(0, video_duration)
            else:
                # Loop do áudio se for mais curto
                loops_needed = int(video_duration / audio_clip.duration) + 1
                audio_clips = [audio_clip] * loops_needed
                from moviepy.editor import concatenate_audioclips
                audio_clip = concatenate_audioclips(audio_clips)
                audio_clip = audio_clip.subclip(0, video_duration)
            
            # Reduzir volume e adicionar fade
            audio_clip = audio_clip.fx(afx.volumex, self.background_audio_volume)
            
            # Adicionar fade in/out
            fade_duration = min(2.0, video_duration / 4)
            audio_clip = audio_clip.audio_fadein(fade_duration)
            audio_clip = audio_clip.audio_fadeout(fade_duration)
            
            # Combinar com o vídeo
            final_video = video_clip.set_audio(audio_clip)
            
            # Limpar recursos
            audio_clip.close()
            
            return final_video
            
        except Exception as e:
            logger.error(f"Erro ao adicionar áudio de fundo: {e}")
            return video_clip
    
    def _get_resolution_dimensions(self, resolution: str) -> Tuple[int, int]:
        """Converte string de resolução para dimensões"""
        if resolution == "1080p":
            return 1920, 1080
        elif resolution == "720p":
            return 1280, 720
        elif resolution == "4k":
            return 3840, 2160
        else:
            return 1920, 1080
    
    def _find_photo_by_name(self, filename: str) -> Optional[str]:
        """Busca uma foto por nome em todos os diretórios de upload"""
        uploads_dir = self.storage_dir / "uploads"
        if not uploads_dir.exists():
            return None
        
        # Buscar recursivamente pelo nome exato do arquivo
        for pattern in ["*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG"]:
            found_files = list(uploads_dir.rglob(pattern))
            for file_path in found_files:
                if file_path.name == filename:
                    return str(file_path)
        
        return None
    
    def _update_status(self, config_path: Path, status: str, progress: int, 
                      error: str = None, output_path: str = None):
        """Atualiza o status do processamento no banco de dados"""
        try:
            # Extrair job_id do nome do arquivo de configuração
            job_id = None
            
            # Tentar extrair do nome do arquivo (ex: "123ABC_temp_config.json" -> "123ABC")
            config_filename = config_path.name
            if "_temp_config.json" in config_filename:
                job_id = config_filename.replace("_temp_config.json", "")
            elif "_config.json" in config_filename:
                job_id = config_filename.replace("_config.json", "")
            
            # Se não conseguiu extrair do nome, tentar ler do arquivo
            if not job_id:
                try:
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                    job_id = config.get('job_id')
                except:
                    pass
            
            if job_id:
                # Atualizar no banco de dados
                update_video_config(
                    job_id=job_id,
                    status=status,
                    progress=progress,
                    error_message=error,
                    output_path=output_path
                )
                logger.info(f"✅ Status atualizado no banco: {job_id} -> {status} ({progress}%)")
            else:
                logger.warning(f"⚠️  Não foi possível extrair job_id de {config_path}")
            
            # Também atualizar o arquivo temporário para compatibilidade
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                config['status'] = status
                config['progress'] = progress
                
                if error:
                    config['error'] = error
                
                if output_path:
                    config['output_path'] = output_path
                
                with open(config_path, 'w') as f:
                    json.dump(config, f, indent=2)
            
        except Exception as e:
            logger.error(f"Erro ao atualizar status: {e}")


# Função de conveniência para processamento
def process_video_with_moviepy(config_path: Path, storage_dir: Path) -> Dict[str, Any]:
    """Processa um vídeo usando MoviePy"""
    editor = MoviePyEditor(storage_dir)
    return editor.create_video_from_config(config_path)
