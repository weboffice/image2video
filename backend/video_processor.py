import subprocess
import json
import os
import tempfile
from pathlib import Path
from typing import List, Dict, Any
import logging

# Imports resilientes para MinIO, banco de dados e otimizações
try:
    from .minio_client import minio_client
    from .video_config_db import update_video_config
    from .video_optimization import optimize_photos_for_video, get_ffmpeg_optimization_args, cleanup_optimized_photos
except ImportError:
    from minio_client import minio_client
    from video_config_db import update_video_config
    from video_optimization import optimize_photos_for_video, get_ffmpeg_optimization_args, cleanup_optimized_photos

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VideoProcessor:
    def __init__(self, storage_dir: Path, use_moviepy: bool = True):
        self.storage_dir = storage_dir
        self.videos_dir = storage_dir / "videos"
        self.videos_dir.mkdir(parents=True, exist_ok=True)
        self.use_moviepy = use_moviepy
        
        # Configurar diretório temporário para FFmpeg
        self.temp_dir = storage_dir / "temp"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Configurar variáveis de ambiente para FFmpeg usar nosso diretório temporário
        os.environ['TMPDIR'] = str(self.temp_dir)
        os.environ['TEMP'] = str(self.temp_dir)
        os.environ['TMP'] = str(self.temp_dir)
        
        # Configurar tempfile para usar nosso diretório
        tempfile.tempdir = str(self.temp_dir)
        
        logger.info(f"🗂️ Diretório temporário do FFmpeg configurado: {self.temp_dir}")
        
        # Importar MoviePyEditor se necessário
        if use_moviepy:
            try:
                from .moviepy_editor import MoviePyEditor
                self.moviepy_editor = MoviePyEditor(storage_dir)
            except ImportError:
                from moviepy_editor import MoviePyEditor
                self.moviepy_editor = MoviePyEditor(storage_dir)
    
    def create_video(self, config_path: Path) -> Dict[str, Any]:
        """Cria um vídeo baseado na configuração fornecida"""
        # Se MoviePy estiver habilitado, usar MoviePyEditor
        if self.use_moviepy:
            logger.info("🎬 Usando MoviePy para processamento de vídeo")
            return self.moviepy_editor.create_video_from_config(config_path)
        
        # Caso contrário, usar FFmpeg (método original)
        logger.info("🎬 Usando FFmpeg para processamento de vídeo")
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
            background_audio = config.get('background_audio', True)  # Padrão True para compatibilidade
            
            logger.info(f"🎬 Iniciando criação do vídeo {job_id}")
            
            # Atualizar status para processing
            self._update_status(config_path, "processing", 5)
            
            # Criar arquivo de lista de imagens para FFmpeg
            logger.info(f"📝 Criando lista de imagens para {job_id}")
            # Gerar comando FFmpeg - salvar dentro da pasta do job
            job_dir = self.videos_dir / job_id
            job_dir.mkdir(parents=True, exist_ok=True)
            output_path = job_dir / f"{job_id}_video.{output_format}"
            
            self._update_status(config_path, "processing", 15)
            
            # Construir comando FFmpeg com efeitos do template
            ffmpeg_cmd = self._build_ffmpeg_command(
                job_id,  # Passar job_id para otimizações
                None,  # Não precisamos mais da lista de imagens
                output_path, 
                template, 
                photos, 
                resolution, 
                fps,
                background_audio
            )
            
            # Verificar se o comando foi construído corretamente
            if not ffmpeg_cmd or len(ffmpeg_cmd) < 3:
                error_msg = "Erro: Comando FFmpeg não pôde ser construído (fotos não encontradas ou template inválido)"
                logger.error(error_msg)
                self._update_status(config_path, "error", 0, error_msg)
                return {"success": False, "error": error_msg}
            
            logger.info(f"📹 Executando FFmpeg: {' '.join(ffmpeg_cmd)}")
            self._update_status(config_path, "processing", 25)
            
            # Executar FFmpeg com monitoramento de progresso
            result = self._run_ffmpeg_with_progress(ffmpeg_cmd, config_path, config)
            
            if result["returncode"] != 0:
                error_msg = f"Erro no FFmpeg: {result['stderr']}"
                logger.error(error_msg)
                self._update_status(config_path, "error", 0, error_msg)
                self._cleanup_temp_files()
                return {"success": False, "error": error_msg}
            
            # Verificar se o arquivo foi criado
            if not output_path.exists():
                error_msg = "Arquivo de vídeo não foi criado"
                logger.error(error_msg)
                self._update_status(config_path, "error", 0, error_msg)
                self._cleanup_temp_files()
                return {"success": False, "error": error_msg}
            
            # Upload do vídeo para MinIO
            video_object_key = f"videos/{job_id}_video.{output_format}"
            logger.info(f"📤 Fazendo upload do vídeo para MinIO: {video_object_key}")
            self._update_status(config_path, "processing", 90)
            
            success = minio_client.upload_file(video_object_key, output_path, "video/mp4")
            if success:
                logger.info(f"✅ Vídeo enviado para MinIO: {video_object_key}")
                # Atualizar status com caminho do MinIO
                self._update_status(config_path, "completed", 100, output_path=f"minio://{video_object_key}")
            else:
                logger.warning(f"⚠️  Falha ao enviar vídeo para MinIO, mantendo local")
                self._update_status(config_path, "completed", 100, output_path=str(output_path))
            
            # Limpar arquivos temporários
            self._cleanup_temp_files()
            
            file_size = output_path.stat().st_size
            logger.info(f"✅ Vídeo criado com sucesso: {output_path} ({file_size} bytes)")
            
            return {
                "success": True,
                "output_path": str(output_path),
                "minio_path": video_object_key if success else None,
                "file_size": file_size,
                "job_id": job_id
            }
            
        except Exception as e:
            error_msg = f"Erro ao processar vídeo: {str(e)}"
            logger.error(error_msg)
            self._update_status(config_path, "error", 0, error_msg)
            self._cleanup_temp_files()
            return {"success": False, "error": error_msg}
    
    def _create_image_list(self, job_id: str, photos: List[Dict], template: Dict) -> Path:
        """Cria arquivo de lista de imagens para FFmpeg"""
        job_dir = self.videos_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        image_list_path = job_dir / f"{job_id}_images.txt"
        temp_files = []  # Lista para rastrear arquivos temporários
        photo_paths = []  # Lista de caminhos das fotos
        
        # Primeiro, coletar todos os caminhos das fotos
        for photo in photos:
            photo_path = self.storage_dir / photo['filePath']
            
            # Verificar se o arquivo existe localmente ou no MinIO
            if photo_path.exists():
                # Arquivo existe localmente
                photo_paths.append(photo_path)
            elif minio_client.file_exists(photo['filePath']):
                # Arquivo existe no MinIO, baixar temporariamente
                temp_path = self.storage_dir / f"temp_{job_id}_{photo['order']}.jpg"
                if minio_client.download_file(photo['filePath'], temp_path):
                    photo_paths.append(temp_path)
                    temp_files.append(temp_path)  # Adicionar à lista para limpeza posterior
                else:
                    logger.warning(f"Falha ao baixar arquivo do MinIO: {photo['filePath']}")
            else:
                logger.warning(f"Arquivo não encontrado: {photo['filePath']}")
        
        # Agora criar o arquivo de lista com todas as fotos
        with open(image_list_path, 'w') as f:
            self._add_photo_entries(f, photo_paths, template)
        
        # Armazenar lista de arquivos temporários para limpeza posterior
        self.temp_files = temp_files
        
        return image_list_path
    
    def _add_photo_entries(self, file, photo_paths: List[Path], template: Dict):
        """Adiciona entradas de foto baseadas no template, distribuindo fotos entre cenas"""
        template_id = template.get('id', '')
        
        # Log do template sendo usado
        logger.info(f"🎬 Processando template: {template_id}")
        logger.info(f"📸 Total de fotos disponíveis: {len(photo_paths)}")
        
        if not photo_paths:
            logger.error("❌ Nenhuma foto disponível")
            return
        
        photo_index = 0
        
        for scene in template['scenes']:
            scene_type = scene['type']
            duration = scene['duration']
            max_photos = scene.get('max_photos', 10)
            
            logger.info(f"📽️ Cena: {scene['name']} (tipo: {scene_type}, duração: {duration}s, max_fotos: {max_photos})")
            
            # Determinar quantas fotos usar nesta cena (limitado pelas fotos restantes)
            remaining_photos = len(photo_paths) - photo_index
            if remaining_photos <= 0:
                # Se não há mais fotos, usar a primeira foto novamente
                photos_for_scene = 1
                photo_index = 0
            else:
                photos_for_scene = min(max_photos, remaining_photos)
            
            # Calcular duração por foto nesta cena
            duration_per_photo = duration / photos_for_scene
            
            logger.info(f"   Usando {photos_for_scene} fotos (índice {photo_index}-{photo_index + photos_for_scene - 1}), {duration_per_photo:.2f}s por foto")
            
            # Adicionar fotos para esta cena
            for i in range(photos_for_scene):
                current_photo = photo_paths[photo_index % len(photo_paths)]
                logger.info(f"      Foto {i+1}: {current_photo.name}")
                
                # Adicionar entrada para esta foto
                for _ in range(int(duration_per_photo * 30)):  # 30fps
                    file.write(f"file '{current_photo}'\n")
                    file.write(f"duration 0.033\n")  # 1/30 segundos
                
                photo_index += 1
    
    def _build_ffmpeg_command(self, job_id: str, image_list_path: Path, output_path: Path, 
                            template: Dict, photos: List[Dict], 
                            resolution: str, fps: int, background_audio: bool = True) -> List[str]:
        """Constrói comando FFmpeg avançado com efeitos baseados no template"""
        
        # Configurar resolução
        if resolution == "1080p":
            width, height = 1920, 1080
        elif resolution == "720p":
            width, height = 1280, 720
        elif resolution == "4k":
            width, height = 3840, 2160
        else:
            width, height = 1920, 1080
        
        # Calcular duração total
        total_duration = sum(scene['duration'] for scene in template['scenes'])
        logger.info(f"⏱️ Duração total calculada: {total_duration}s")
        
        # Construir comando FFmpeg com efeitos avançados baseados no template
        # Ler configuração para passar para otimizações
        config_data = {}
        try:
            # Buscar configuração do banco de dados
            from video_config_db import get_video_config
            video_config = get_video_config(job_id)
            if video_config and video_config.config_data:
                config_data = video_config.config_data
        except Exception as e:
            logger.warning(f"⚠️  Não foi possível obter configuração do banco: {e}")
        
        return self._build_advanced_ffmpeg_command(
            job_id, photos, template, width, height, fps, total_duration, output_path, background_audio, config_data
        )
        
    
    def _build_advanced_ffmpeg_command(self, job_id: str, photos: List[Dict], template: Dict, 
                                     width: int, height: int, fps: int, 
                                     total_duration: float, output_path: Path, 
                                     background_audio: bool = True, config: Dict = None) -> List[str]:
        """Constrói comando FFmpeg com efeitos baseados no template"""
        
        # Coletar caminhos das fotos
        photo_paths = []
        for photo in photos:
            photo_path = self.storage_dir / photo['filePath']
            
            if photo_path.exists():
                photo_paths.append(str(photo_path))
                logger.info(f"✅ Foto encontrada: {photo_path}")
            else:
                # Tentar busca inteligente por nome de arquivo
                filename = Path(photo['filePath']).name
                found_alternative = self._find_photo_by_name(filename)
                
                if found_alternative:
                    photo_paths.append(found_alternative)
                    logger.info(f"✅ Foto encontrada por nome: {found_alternative}")
                else:
                    logger.warning(f"❌ Foto não encontrada: {photo_path}")
                    logger.warning(f"❌ Também não encontrada por nome: {filename}")
        
        if not photo_paths:
            logger.error("❌ Nenhuma foto válida encontrada")
            # Tentar usar fotos disponíveis como fallback
            available_photos = self._get_available_photos()
            if available_photos:
                logger.info(f"🔄 Usando {len(available_photos)} fotos disponíveis como fallback")
                photo_paths = available_photos[:len(photos)]  # Usar o mesmo número de fotos solicitadas
            else:
                return []
        
        # 🚀 OTIMIZAÇÃO: Redimensionar fotos proporcionalmente para melhor performance
        logger.info("🚀 Otimizando fotos para melhor performance...")
        try:
            # Usar preset da configuração ou determinar baseado na resolução
            preset = config.get('quality_preset', 'fast') if config else 'fast'
            if preset not in ['fast', 'balanced', 'high_quality']:
                preset = "fast" if width <= 1280 else "balanced" if width <= 1920 else "high_quality"
            
            # Criar diretório temporário para fotos otimizadas
            temp_dir = self.storage_dir / "temp" / f"opt_{job_id}"
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            # Otimizar fotos
            optimized_photo_paths = optimize_photos_for_video(
                photo_paths, 
                preset=preset,
                temp_dir=temp_dir
            )
            
            if optimized_photo_paths:
                photo_paths = optimized_photo_paths
                logger.info(f"✅ {len(photo_paths)} fotos otimizadas com preset '{preset}'")
            else:
                logger.warning("⚠️  Falha na otimização, usando fotos originais")
                
        except Exception as e:
            logger.warning(f"⚠️  Erro na otimização de fotos: {e}, usando fotos originais")
        
        template_id = template.get('id', '')
        logger.info(f"🎬 Construindo comando FFmpeg para template: {template_id}")
        
        # Usar método simples que funciona - criar slideshow com efeitos baseados no template
        return self._build_simple_slideshow_command(photo_paths, template, width, height, fps, total_duration, output_path, background_audio)
    
    def _build_simple_slideshow_command(self, photo_paths: List[str], template: Dict, 
                                      width: int, height: int, fps: int, 
                                      total_duration: float, output_path: Path, 
                                      background_audio: bool = True) -> List[str]:
        """Constrói comando FFmpeg simples que funciona, com variações baseadas no template"""
        
        # Criar arquivo de lista de imagens (método que funcionava)
        job_id = output_path.stem.replace('_video', '')
        job_dir = output_path.parent
        image_list_path = job_dir / f"{job_id}_images.txt"
        
        # Calcular duração por foto
        duration_per_photo = total_duration / len(photo_paths)
        
        # Criar lista de imagens com durações
        with open(image_list_path, 'w') as f:
            for photo_path in photo_paths:
                f.write(f"file '{photo_path}'\n")
                f.write(f"duration {duration_per_photo}\n")
        
        template_id = template.get('id', '')
        
        # Caminho para o áudio de fundo - usar música específica do template se disponível
        if template.get('background_music'):
            audio_filename = template['background_music']
        else:
            audio_filename = "source_bg.mp3"  # Fallback padrão
            
        # Corrigir caminho para assets - está em backend/assets
        background_audio_path = Path(__file__).parent / "assets" / audio_filename
        
        # Comando base
        cmd = [
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', str(image_list_path)
        ]
        
        # Adicionar áudio de fundo se habilitado e arquivo existir
        if background_audio and background_audio_path.exists():
            cmd.extend(['-i', str(background_audio_path)])
            logger.info(f"🎵 Adicionando áudio de fundo específico do template: {background_audio_path}")
        elif background_audio:
            # Tentar fallback para música padrão
            fallback_path = Path(__file__).parent / "assets" / "source_bg.mp3"
            if fallback_path.exists():
                cmd.extend(['-i', str(fallback_path)])
                logger.info(f"🎵 Usando música padrão como fallback: {fallback_path}")
            else:
                logger.info("🔇 Nenhuma música disponível")
        else:
            logger.info("🔇 Áudio de fundo desabilitado")
        
        # Aplicar filtros baseados no template
        if 'grid' in template_id:
            # Para grid, usar um zoom leve
            vf = f'scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black,zoompan=z=1.1:d={fps*duration_per_photo}:x=iw/2-(iw/zoom/2):y=ih/2-(ih/zoom/2)'
        elif 'cinematic' in template_id:
            # Para cinematográfico, usar zoom mais dramático e efeitos de cor
            vf = f'scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black,zoompan=z=1.3:d={fps*duration_per_photo}:x=iw/2-(iw/zoom/2):y=ih/2-(ih/zoom/2),eq=contrast=1.2:brightness=0.05:saturation=1.1'
        elif 'slideshow' in template_id:
            # Para slideshow, usar fade suave
            vf = f'scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black,fade=t=in:st=0:d=0.5,fade=t=out:st={duration_per_photo-0.5}:d=0.5'
        else:
            # Template padrão
            vf = f'scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black'
        
        # 🚀 OTIMIZAÇÃO: Usar configurações otimizadas do FFmpeg
        # Usar preset da configuração ou determinar baseado na resolução
        preset = config.get('quality_preset', 'fast') if config else 'fast'
        if preset not in ['fast', 'balanced', 'high_quality']:
            preset = "fast" if width <= 1280 else "balanced" if width <= 1920 else "high_quality"
        
        optimization_args = get_ffmpeg_optimization_args(preset)
        
        cmd.extend([
            '-vf', vf,
            '-r', str(fps),
            '-c:v', 'libx264'
        ])
        
        # Adicionar argumentos de otimização
        cmd.extend(optimization_args)
        
        logger.info(f"🚀 Usando preset de otimização: {preset}")
        
        # Configurações de áudio
        if background_audio and background_audio_path.exists():
            cmd.extend([
                '-c:a', 'aac',
                '-b:a', '128k',
                '-shortest',  # Termina quando o vídeo ou áudio mais curto acabar
                '-filter_complex', f'[1:a]volume=0.3,afade=t=in:st=0:d=2,afade=t=out:st={total_duration-2}:d=2[audio_out]',
                '-map', '0:v',
                '-map', '[audio_out]'
            ])
        
        cmd.extend([
            '-t', str(total_duration),
            str(output_path)
        ])
        
        return cmd
    
    def _get_available_photos(self) -> List[str]:
        """Busca fotos disponíveis no sistema para usar como fallback"""
        import random
        available_photos = []
        
        # Buscar em diretórios de upload
        uploads_dir = self.storage_dir / "uploads"
        if uploads_dir.exists():
            # Buscar recursivamente por arquivos de imagem
            for pattern in ["*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG"]:
                found_files = list(uploads_dir.rglob(pattern))
                available_photos.extend([str(f) for f in found_files])
        
        # Se não encontrou nada, tentar foto de teste
        if not available_photos:
            test_image = self.storage_dir / "test_image.jpg"
            if test_image.exists():
                available_photos = [str(test_image)]
        
        # Randomizar a ordem das fotos para variedade
        if available_photos:
            random.shuffle(available_photos)
        
        logger.info(f"📸 Encontradas {len(available_photos)} fotos disponíveis para fallback (randomizadas)")
        return available_photos[:10]  # Limitar a 10 fotos para não sobrecarregar
    
    def _find_photo_by_name(self, filename: str) -> str:
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
        
        # Se não encontrou exato, tentar busca parcial (sem extensão ou prefixos)
        base_name = Path(filename).stem
        for pattern in ["*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG"]:
            found_files = list(uploads_dir.rglob(pattern))
            for file_path in found_files:
                if base_name in file_path.stem or file_path.stem in base_name:
                    logger.info(f"🔍 Encontrada foto similar: {file_path.name} para {filename}")
                    return str(file_path)
        
        return None
    
    def _build_template_filters(self, template: Dict, photo_paths: List[str], 
                              width: int, height: int, fps: int) -> str:
        """Constrói filtros FFmpeg baseados nos efeitos do template"""
        
        template_id = template.get('id', '')
        filters = []
        photo_count = len(photo_paths)
        
        logger.info(f"🎬 Construindo filtros para template: {template_id} com {photo_count} fotos")
        
        # Por enquanto, usar um filtro simples que funciona
        if photo_count == 1:
            # Uma foto apenas
            filters.append(f"[0:v]scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black[out]")
        elif photo_count == 2:
            # Duas fotos lado a lado
            cell_width = width // 2
            filters.append(f"[0:v]scale={cell_width}:{height}:force_original_aspect_ratio=decrease,pad={cell_width}:{height}:(ow-iw)/2:(oh-ih)/2:black[left]")
            filters.append(f"[1:v]scale={cell_width}:{height}:force_original_aspect_ratio=decrease,pad={cell_width}:{height}:(ow-iw)/2:(oh-ih)/2:black[right]")
            filters.append("[left][right]hstack=inputs=2[out]")
        elif photo_count >= 3:
            # Grid 2x2 simples
            cell_width = width // 2
            cell_height = height // 2
            
            filters.append(f"[0:v]scale={cell_width}:{cell_height}:force_original_aspect_ratio=decrease,pad={cell_width}:{cell_height}:(ow-iw)/2:(oh-ih)/2:black[tl]")
            filters.append(f"[1:v]scale={cell_width}:{cell_height}:force_original_aspect_ratio=decrease,pad={cell_width}:{cell_height}:(ow-iw)/2:(oh-ih)/2:black[tr]")
            filters.append(f"[2:v]scale={cell_width}:{cell_height}:force_original_aspect_ratio=decrease,pad={cell_width}:{cell_height}:(ow-iw)/2:(oh-ih)/2:black[bl]")
            
            if photo_count >= 4:
                filters.append(f"[3:v]scale={cell_width}:{cell_height}:force_original_aspect_ratio=decrease,pad={cell_width}:{cell_height}:(ow-iw)/2:(oh-ih)/2:black[br]")
                filters.append("[tl][tr]hstack=inputs=2[top]")
                filters.append("[bl][br]hstack=inputs=2[bottom]")
                filters.append("[top][bottom]vstack=inputs=2[out]")
            else:
                # 3 fotos - duplicar a terceira foto para completar o grid
                filters.append(f"[2:v]scale={cell_width}:{cell_height}:force_original_aspect_ratio=decrease,pad={cell_width}:{cell_height}:(ow-iw)/2:(oh-ih)/2:black[br]")
                filters.append("[tl][tr]hstack=inputs=2[top]")
                filters.append("[bl][br]hstack=inputs=2[bottom]")
                filters.append("[top][bottom]vstack=inputs=2[out]")
        
        filter_string = ';'.join(filters) if filters else ''
        logger.info(f"🔧 Filtros construídos: {filter_string}")
        
        return filter_string
    
    def _build_cinematic_filters(self, template: Dict, photo_paths: List[str], 
                               width: int, height: int) -> List[str]:
        """Constrói filtros cinematográficos avançados"""
        filters = []
        photo_count = len(photo_paths)
        
        for i, scene in enumerate(template['scenes']):
            scene_type = scene['type']
            duration = scene['duration']
            effects = scene.get('effects', [])
            
            # Selecionar foto para esta cena
            photo_index = i % photo_count
            
            # Filtro base de escala e posicionamento
            base_filter = f"[{photo_index}:v]scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black"
            
            # Aplicar efeitos baseados no tipo de cena
            if scene_type == 'zoom' or scene_type == 'ken_burns':
                # Efeito Ken Burns (zoom + pan)
                zoom_start = 1.0
                zoom_end = 1.5
                
                # Extrair parâmetros dos efeitos
                for effect in effects:
                    if effect['type'] == 'zoom':
                        params = effect.get('parameters', {})
                        zoom_start = params.get('zoom_start', 1.0)
                        zoom_end = params.get('zoom_end', 1.5)
                
                # Aplicar zoom progressivo
                base_filter += f",zoompan=z='min(zoom+0.0015,{zoom_end})':d={int(duration * 30)}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                
            elif scene_type == 'fade':
                # Efeito de fade
                base_filter += f",fade=t=in:st=0:d=1,fade=t=out:st={duration-1}:d=1"
                
            elif scene_type == 'grid':
                # Para grid, usar layout especial (implementar depois)
                pass
            
            # Adicionar efeitos de cor cinematográfica
            base_filter += ",eq=contrast=1.1:brightness=0.05:saturation=1.2"
            
            # Adicionar vinheta sutil
            base_filter += f",vignette=PI/4:0.2"
            
            filters.append(f"{base_filter}[v{i}]")
        
        # Concatenar todas as cenas
        if len(filters) > 1:
            concat_inputs = ''.join(f'[v{i}]' for i in range(len(filters)))
            filters.append(f"{concat_inputs}concat=n={len(filters)}:v=1:a=0[out]")
        elif len(filters) == 1:
            filters.append("[v0]copy[out]")
        
        return filters
    
    def _build_grid_filters(self, template: Dict, photo_paths: List[str], 
                          width: int, height: int) -> List[str]:
        """Constrói filtros para layout em grid"""
        filters = []
        photo_count = len(photo_paths)
        
        if photo_count == 0:
            return []
        
        # Para grid simples, usar layout 2x2 ou 3x2 dependendo do número de fotos
        if photo_count == 1:
            # Uma foto apenas - usar zoom simples
            filters.append(f"[0:v]scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black,fade=t=in:st=0:d=1,fade=t=out:st=7:d=1[out]")
        elif photo_count == 2:
            # Duas fotos - lado a lado
            cell_width = width // 2
            filters.append(f"[0:v]scale={cell_width}:{height}:force_original_aspect_ratio=decrease,pad={cell_width}:{height}:(ow-iw)/2:(oh-ih)/2:black[img0]")
            filters.append(f"[1:v]scale={cell_width}:{height}:force_original_aspect_ratio=decrease,pad={cell_width}:{height}:(ow-iw)/2:(oh-ih)/2:black[img1]")
            filters.append("[img0][img1]hstack=inputs=2[out]")
        elif photo_count >= 3:
            # Grid simples 2x2 para 3+ fotos
            cols = 2
            rows = 2
            grid_size = min(4, photo_count)
            
            cell_width = width // cols
            cell_height = height // rows
            
            # Redimensionar cada foto
            for i in range(grid_size):
                filters.append(f"[{i}:v]scale={cell_width}:{cell_height}:force_original_aspect_ratio=decrease,pad={cell_width}:{cell_height}:(ow-iw)/2:(oh-ih)/2:black[img{i}]")
            
            # Criar grid 2x2
            if grid_size >= 4:
                # Grid completo 2x2
                filters.append("[img0][img1]hstack=inputs=2[top]")
                filters.append("[img2][img3]hstack=inputs=2[bottom]")
                filters.append("[top][bottom]vstack=inputs=2[out]")
            elif grid_size == 3:
                # 3 fotos - 2 em cima, 1 embaixo centralizada
                filters.append("[img0][img1]hstack=inputs=2[top]")
                filters.append(f"[img2]pad={width}:{cell_height}:({width}-{cell_width})/2:0:black[bottom]")
                filters.append("[top][bottom]vstack=inputs=2[out]")
        
        return filters
    
    def _build_slideshow_filters(self, template: Dict, photo_paths: List[str], 
                               width: int, height: int) -> List[str]:
        """Constrói filtros para slideshow simples"""
        filters = []
        photo_count = len(photo_paths)
        
        for i in range(photo_count):
            # Filtro básico com fade
            filter_str = f"[{i}:v]scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black,fade=t=in:st=0:d=0.5,fade=t=out:st=2.5:d=0.5[v{i}]"
            filters.append(filter_str)
        
        # Concatenar todas as fotos
        if photo_count > 1:
            concat_inputs = ''.join(f'[v{i}]' for i in range(photo_count))
            filters.append(f"{concat_inputs}concat=n={photo_count}:v=1:a=0[out]")
        else:
            filters.append("[v0]copy[out]")
        
        return filters
    
    def _build_default_filters(self, template: Dict, photo_paths: List[str], 
                             width: int, height: int) -> List[str]:
        """Constrói filtros padrão básicos"""
        filters = []
        photo_count = len(photo_paths)
        
        # Aplicar efeitos básicos a cada foto
        for i in range(photo_count):
            filter_str = f"[{i}:v]scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black[v{i}]"
            filters.append(filter_str)
        
        # Concatenar
        if photo_count > 1:
            concat_inputs = ''.join(f'[v{i}]' for i in range(photo_count))
            filters.append(f"{concat_inputs}concat=n={photo_count}:v=1:a=0[out]")
        else:
            filters.append("[v0]copy[out]")
        
        return filters
    
    def _update_status(self, config_path: Path, status: str, progress: int, 
                      error: str = None, output_path: str = None):
        """Atualiza o status do job de vídeo no banco de dados"""
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
                print(f"✅ Status atualizado no banco: {job_id} -> {status} ({progress}%)")
            else:
                print(f"⚠️  Não foi possível extrair job_id de {config_path}")
            
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

    def _run_ffmpeg_with_progress(self, ffmpeg_cmd: List[str], config_path: Path, config: Dict) -> Dict[str, Any]:
        """Executa FFmpeg com monitoramento de progresso"""
        try:
            # Calcular duração total estimada
            total_duration = config.get('total_duration', 60)
            
            # Executar FFmpeg com pipe para capturar saída em tempo real
            process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.storage_dir,
                bufsize=1,
                universal_newlines=True
            )
            
            stderr_lines = []
            start_time = None
            
            # Monitorar saída do FFmpeg
            while True:
                stderr_line = process.stderr.readline()
                if stderr_line == '' and process.poll() is not None:
                    break
                
                if stderr_line:
                    stderr_lines.append(stderr_line.strip())
                    
                    # Extrair tempo atual do FFmpeg
                    if 'time=' in stderr_line:
                        try:
                            # Parsear linha de tempo do FFmpeg (formato: time=00:00:15.00)
                            time_part = stderr_line.split('time=')[1].split()[0]
                            if ':' in time_part:
                                time_parts = time_part.split(':')
                                if len(time_parts) >= 3:
                                    hours = int(time_parts[0])
                                    minutes = int(time_parts[1])
                                    seconds = float(time_parts[2])
                                    current_time = hours * 3600 + minutes * 60 + seconds
                                    
                                    # Calcular progresso baseado no tempo
                                    progress = min(int((current_time / total_duration) * 70) + 25, 85)
                                    self._update_status(config_path, "processing", progress)
                                    
                                    if start_time is None:
                                        start_time = current_time
                        except Exception as e:
                            logger.debug(f"Erro ao parsear tempo do FFmpeg: {e}")
            
            # Aguardar processo terminar
            returncode = process.wait()
            
            return {
                "returncode": returncode,
                "stdout": "",
                "stderr": "\n".join(stderr_lines)
            }
            
        except Exception as e:
            logger.error(f"Erro ao executar FFmpeg com progresso: {e}")
            return {
                "returncode": 1,
                "stdout": "",
                "stderr": str(e)
            }

    def _cleanup_temp_files(self):
        """Limpa arquivos temporários criados durante o processamento"""
        # Limpar arquivos temporários específicos do processamento
        if hasattr(self, 'temp_files'):
            for temp_file in self.temp_files:
                try:
                    if temp_file.exists():
                        temp_file.unlink()
                        logger.info(f"🗑️  Arquivo temporário removido: {temp_file}")
                except Exception as e:
                    logger.warning(f"⚠️  Erro ao remover arquivo temporário {temp_file}: {e}")
            self.temp_files = []
        
        # 🚀 OTIMIZAÇÃO: Limpar fotos otimizadas temporárias
        try:
            temp_opt_dir = self.storage_dir / "temp"
            if temp_opt_dir.exists():
                import shutil
                for opt_dir in temp_opt_dir.glob("opt_*"):
                    if opt_dir.is_dir():
                        shutil.rmtree(opt_dir)
                        logger.info(f"🗑️  Diretório de otimização removido: {opt_dir}")
        except Exception as e:
            logger.warning(f"⚠️  Erro ao limpar fotos otimizadas: {e}")
        
        # Limpar diretório temporário do FFmpeg
        if hasattr(self, 'temp_dir') and self.temp_dir.exists():
            try:
                import shutil
                # Listar arquivos temporários antes de remover
                temp_files = list(self.temp_dir.glob("*"))
                if temp_files:
                    logger.info(f"🧹 Removendo {len(temp_files)} arquivos temporários do FFmpeg")
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
                    logger.info("✅ Limpeza de arquivos temporários do FFmpeg concluída")
                else:
                    logger.debug("📁 Nenhum arquivo temporário do FFmpeg encontrado")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao limpar arquivos temporários do FFmpeg: {e}")

def process_video_job(config_path: Path, storage_dir: Path, use_moviepy: bool = True) -> Dict[str, Any]:
    """Função principal para processar um job de vídeo"""
    try:
        # Carregar configuração
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        job_id = config['job_id']
        template_id = config['template']['id']
        
        logger.info(f"🎬 Processando vídeo {job_id} com template {template_id}")
        
        # Usar o VideoProcessor integrado ao invés do script externo
        processor = VideoProcessor(storage_dir, use_moviepy=use_moviepy)
        result = processor.create_video(config_path)
        
        if result["success"]:
            return result
        else:
            return {"success": False, "error": result.get("error", "Erro desconhecido")}
            
    except Exception as e:
        logger.error(f"❌ Erro ao processar vídeo: {e}")
        return {"success": False, "error": str(e)}


def process_video_job_with_moviepy(config_path: Path, storage_dir: Path) -> Dict[str, Any]:
    """Função específica para processar um job de vídeo usando MoviePy"""
    return process_video_job(config_path, storage_dir, use_moviepy=True)


def process_video_job_with_ffmpeg(config_path: Path, storage_dir: Path) -> Dict[str, Any]:
    """Função específica para processar um job de vídeo usando FFmpeg"""
    return process_video_job(config_path, storage_dir, use_moviepy=False)
