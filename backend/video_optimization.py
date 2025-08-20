"""
Utilitários para otimização de performance na geração de vídeos
"""

import os
import tempfile
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
from PIL import Image, ImageOps
import logging

logger = logging.getLogger(__name__)

# Configurações de otimização
OPTIMIZATION_SETTINGS = {
    "fast": {
        "max_photo_size": (1280, 720),  # 720p
        "jpeg_quality": 85,
        "resize_algorithm": Image.LANCZOS,
        "ffmpeg_preset": "fast",
        "ffmpeg_crf": 23,
        "moviepy_fps": 24
    },
    "balanced": {
        "max_photo_size": (1920, 1080),  # 1080p
        "jpeg_quality": 90,
        "resize_algorithm": Image.LANCZOS,
        "ffmpeg_preset": "medium",
        "ffmpeg_crf": 20,
        "moviepy_fps": 30
    },
    "high_quality": {
        "max_photo_size": (3840, 2160),  # 4K
        "jpeg_quality": 95,
        "resize_algorithm": Image.LANCZOS,
        "ffmpeg_preset": "slow",
        "ffmpeg_crf": 18,
        "moviepy_fps": 30
    }
}

def get_optimization_preset(preset: str = "fast") -> Dict[str, Any]:
    """Obter configurações de otimização por preset"""
    return OPTIMIZATION_SETTINGS.get(preset, OPTIMIZATION_SETTINGS["fast"])

def calculate_target_size(original_size: Tuple[int, int], max_size: Tuple[int, int]) -> Tuple[int, int]:
    """
    Calcula o tamanho alvo mantendo proporção
    
    Args:
        original_size: (width, height) original
        max_size: (max_width, max_height) máximo permitido
    
    Returns:
        (width, height) otimizado
    """
    orig_width, orig_height = original_size
    max_width, max_height = max_size
    
    # Se já está dentro dos limites, não redimensionar
    if orig_width <= max_width and orig_height <= max_height:
        return original_size
    
    # Calcular proporção
    width_ratio = max_width / orig_width
    height_ratio = max_height / orig_height
    
    # Usar a menor proporção para manter aspect ratio
    ratio = min(width_ratio, height_ratio)
    
    new_width = int(orig_width * ratio)
    new_height = int(orig_height * ratio)
    
    # Garantir que seja par (necessário para alguns codecs)
    new_width = new_width if new_width % 2 == 0 else new_width - 1
    new_height = new_height if new_height % 2 == 0 else new_height - 1
    
    return (new_width, new_height)

def resize_image_optimized(
    input_path: str, 
    output_path: str, 
    max_size: Tuple[int, int] = (1280, 720),
    quality: int = 85,
    algorithm: int = Image.LANCZOS
) -> bool:
    """
    Redimensiona uma imagem de forma otimizada
    
    Args:
        input_path: Caminho da imagem original
        output_path: Caminho para salvar a imagem otimizada
        max_size: Tamanho máximo (width, height)
        quality: Qualidade JPEG (1-100)
        algorithm: Algoritmo de redimensionamento
    
    Returns:
        True se sucesso, False caso contrário
    """
    try:
        with Image.open(input_path) as img:
            # Corrigir orientação EXIF
            img = ImageOps.exif_transpose(img)
            
            # Converter para RGB se necessário
            if img.mode in ('RGBA', 'LA', 'P'):
                # Criar fundo branco para transparências
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Calcular novo tamanho
            original_size = img.size
            target_size = calculate_target_size(original_size, max_size)
            
            # Redimensionar se necessário
            if target_size != original_size:
                img = img.resize(target_size, algorithm)
                logger.info(f"📏 Redimensionado: {original_size} → {target_size}")
            
            # Salvar com otimizações
            img.save(
                output_path,
                'JPEG',
                quality=quality,
                optimize=True,
                progressive=True
            )
            
            # Verificar tamanho do arquivo
            original_size_mb = os.path.getsize(input_path) / (1024 * 1024)
            optimized_size_mb = os.path.getsize(output_path) / (1024 * 1024)
            reduction = ((original_size_mb - optimized_size_mb) / original_size_mb) * 100
            
            logger.info(f"💾 Tamanho: {original_size_mb:.1f}MB → {optimized_size_mb:.1f}MB ({reduction:.1f}% redução)")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Erro ao otimizar imagem {input_path}: {e}")
        return False

def optimize_photos_for_video(
    photo_paths: list,
    preset: str = "fast",
    temp_dir: Optional[Path] = None
) -> list:
    """
    Otimiza uma lista de fotos para geração de vídeo
    
    Args:
        photo_paths: Lista de caminhos das fotos
        preset: Preset de otimização ("fast", "balanced", "high_quality")
        temp_dir: Diretório temporário (opcional)
    
    Returns:
        Lista de caminhos das fotos otimizadas
    """
    if not photo_paths:
        return []
    
    settings = get_optimization_preset(preset)
    max_size = settings["max_photo_size"]
    quality = settings["jpeg_quality"]
    algorithm = settings["resize_algorithm"]
    
    # Criar diretório temporário se não fornecido
    if temp_dir is None:
        temp_dir = Path(tempfile.mkdtemp(prefix="video_opt_"))
    else:
        temp_dir.mkdir(parents=True, exist_ok=True)
    
    optimized_paths = []
    
    logger.info(f"🚀 Otimizando {len(photo_paths)} fotos com preset '{preset}'")
    logger.info(f"📐 Tamanho máximo: {max_size}, Qualidade: {quality}")
    
    for i, photo_path in enumerate(photo_paths):
        try:
            # Nome do arquivo otimizado
            original_name = Path(photo_path).stem
            optimized_path = temp_dir / f"opt_{i:03d}_{original_name}.jpg"
            
            # Otimizar imagem
            success = resize_image_optimized(
                photo_path,
                str(optimized_path),
                max_size,
                quality,
                algorithm
            )
            
            if success:
                optimized_paths.append(str(optimized_path))
            else:
                # Se falhou, usar original
                logger.warning(f"⚠️  Usando foto original: {photo_path}")
                optimized_paths.append(photo_path)
                
        except Exception as e:
            logger.error(f"❌ Erro ao processar {photo_path}: {e}")
            optimized_paths.append(photo_path)
    
    logger.info(f"✅ Otimização concluída: {len(optimized_paths)} fotos processadas")
    return optimized_paths

def get_ffmpeg_optimization_args(preset: str = "fast") -> list:
    """Obter argumentos otimizados do FFmpeg"""
    settings = get_optimization_preset(preset)
    
    return [
        '-preset', settings["ffmpeg_preset"],
        '-crf', str(settings["ffmpeg_crf"]),
        '-movflags', '+faststart',  # Otimização para streaming
        '-pix_fmt', 'yuv420p',      # Compatibilidade máxima
        '-tune', 'film',            # Otimizado para conteúdo fotográfico
        '-threads', '0'             # Usar todos os cores disponíveis
    ]

def get_moviepy_optimization_settings(preset: str = "fast") -> Dict[str, Any]:
    """Obter configurações otimizadas do MoviePy"""
    settings = get_optimization_preset(preset)
    
    return {
        'fps': settings["moviepy_fps"],
        'codec': 'libx264',
        'preset': settings["ffmpeg_preset"],
        'ffmpeg_params': [
            '-crf', str(settings["ffmpeg_crf"]),
            '-movflags', '+faststart',
            '-pix_fmt', 'yuv420p',
            '-tune', 'film'
        ]
    }

def cleanup_optimized_photos(photo_paths: list):
    """Limpar fotos otimizadas temporárias"""
    cleaned = 0
    for photo_path in photo_paths:
        try:
            path = Path(photo_path)
            if path.exists() and "opt_" in path.name:
                path.unlink()
                cleaned += 1
        except Exception as e:
            logger.warning(f"⚠️  Não foi possível limpar {photo_path}: {e}")
    
    if cleaned > 0:
        logger.info(f"🧹 Limpeza concluída: {cleaned} arquivos temporários removidos")
