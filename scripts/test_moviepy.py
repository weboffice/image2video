#!/usr/bin/env python3
"""
Script de demonstração do MoviePy Editor
Mostra como usar o MoviePy como alternativa ao FFmpeg
"""

import sys
import json
from pathlib import Path

# Adicionar o diretório backend ao path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from video_processor import process_video_job_with_moviepy, process_video_job
from moviepy_editor import MoviePyEditor


def compare_processors(job_id: str):
    """Compara MoviePy (principal) vs FFmpeg (alternativo) para o mesmo job"""
    
    backend_dir = Path(__file__).parent.parent / "backend"
    storage_dir = backend_dir / "storage"
    config_path = storage_dir / "videos" / job_id / f"{job_id}_config.json"
    
    if not config_path.exists():
        print(f"❌ Configuração não encontrada: {config_path}")
        return
    
    print(f"🔍 Comparando processadores para job: {job_id}")
    print("=" * 60)
    
    # Carregar configuração original
    with open(config_path, 'r') as f:
        original_config = json.load(f)
    
    # Teste 1: MoviePy (principal)
    print("\n🎭 Testando com MoviePy (Principal)...")
    
    moviepy_config = original_config.copy()
    moviepy_config['job_id'] = f"{job_id}_MOVIEPY_TEST"
    moviepy_config['status'] = 'pending'
    moviepy_config['progress'] = 0
    
    moviepy_dir = storage_dir / "videos" / f"{job_id}_MOVIEPY_TEST"
    moviepy_dir.mkdir(exist_ok=True)
    moviepy_config_path = moviepy_dir / f"{job_id}_MOVIEPY_TEST_config.json"
    
    with open(moviepy_config_path, 'w') as f:
        json.dump(moviepy_config, f, indent=2)
    
    moviepy_result = process_video_job(moviepy_config_path, storage_dir)  # Usa MoviePy por padrão agora
    
    if moviepy_result['success']:
        moviepy_path = Path(moviepy_result['output_path'])
        moviepy_size = moviepy_path.stat().st_size / (1024 * 1024) if moviepy_path.exists() else 0
        print(f"✅ MoviePy: {moviepy_size:.1f} MB")
    else:
        print(f"❌ MoviePy: {moviepy_result.get('error', 'Erro desconhecido')}")
    
    # Teste 2: FFmpeg (alternativo)
    print("\n🎬 Testando com FFmpeg (Alternativo)...")
    
    ffmpeg_config = original_config.copy()
    ffmpeg_config['job_id'] = f"{job_id}_FFMPEG_TEST"
    ffmpeg_config['status'] = 'pending'
    ffmpeg_config['progress'] = 0
    
    ffmpeg_dir = storage_dir / "videos" / f"{job_id}_FFMPEG_TEST"
    ffmpeg_dir.mkdir(exist_ok=True)
    ffmpeg_config_path = ffmpeg_dir / f"{job_id}_FFMPEG_TEST_config.json"
    
    with open(ffmpeg_config_path, 'w') as f:
        json.dump(ffmpeg_config, f, indent=2)
    
    ffmpeg_result = process_video_job(ffmpeg_config_path, storage_dir, use_moviepy=False)
    
    if ffmpeg_result['success']:
        ffmpeg_path = Path(ffmpeg_result['output_path'])
        ffmpeg_size = ffmpeg_path.stat().st_size / (1024 * 1024) if ffmpeg_path.exists() else 0
        print(f"✅ FFmpeg: {ffmpeg_size:.1f} MB")
    else:
        print(f"❌ FFmpeg: {ffmpeg_result.get('error', 'Erro desconhecido')}")
    
    # Resumo
    print("\n📊 Resumo da Comparação:")
    print("-" * 40)
    
    if ffmpeg_result['success'] and moviepy_result['success']:
        print(f"MoviePy: {moviepy_size:.1f} MB (Principal)")
        print(f"FFmpeg:  {ffmpeg_size:.1f} MB (Alternativo)")
        
        if ffmpeg_size > 0 and moviepy_size > 0:
            ratio = moviepy_size / ffmpeg_size
            print(f"Razão:   {ratio:.2f}x")
    
    print("\n🎯 Recomendações:")
    print("• MoviePy (Principal): Mais flexível para efeitos complexos, código Python puro")
    print("• FFmpeg (Alternativo): Melhor performance, arquivos menores, mais opções de codec")


def test_moviepy_features():
    """Testa funcionalidades específicas do MoviePy"""
    
    print("🧪 Testando funcionalidades do MoviePy...")
    print("=" * 50)
    
    backend_dir = Path(__file__).parent.parent / "backend"
    storage_dir = backend_dir / "storage"
    
    # Inicializar editor
    editor = MoviePyEditor(storage_dir)
    
    print(f"✅ MoviePyEditor inicializado")
    print(f"📁 Storage: {editor.storage_dir}")
    print(f"🎵 Assets: {editor.assets_dir}")
    print(f"📐 Resolução padrão: {editor.default_resolution}")
    print(f"🎞️ FPS padrão: {editor.default_fps}")
    print(f"🔊 Volume do áudio: {editor.background_audio_volume}")
    
    # Testar métodos utilitários
    resolutions = ['720p', '1080p', '4k']
    for res in resolutions:
        width, height = editor._get_resolution_dimensions(res)
        print(f"📏 {res}: {width}x{height}")
    
    # Verificar áudio de fundo
    audio_path = editor.assets_dir / "source_bg_clean.mp3"
    if audio_path.exists():
        print(f"🎵 Áudio de fundo disponível: {audio_path}")
    else:
        print("🔇 Áudio de fundo não encontrado")


def main():
    """Função principal"""
    
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python test_moviepy.py compare <job_id>  # Comparar FFmpeg vs MoviePy")
        print("  python test_moviepy.py features          # Testar funcionalidades")
        print("\nExemplos:")
        print("  python test_moviepy.py compare 3857F430")
        print("  python test_moviepy.py features")
        return
    
    command = sys.argv[1]
    
    if command == "compare":
        if len(sys.argv) < 3:
            print("❌ Job ID necessário para comparação")
            return
        
        job_id = sys.argv[2]
        compare_processors(job_id)
        
    elif command == "features":
        test_moviepy_features()
        
    else:
        print(f"❌ Comando desconhecido: {command}")
        print("Use 'compare' ou 'features'")


if __name__ == "__main__":
    main()
