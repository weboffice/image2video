#!/usr/bin/env python3
"""
Script para remover os primeiros 10 segundos de cada arquivo MP3 na pasta assets.
"""

import os
import glob
from moviepy.editor import AudioFileClip

def trim_audio_files(assets_dir, trim_seconds=10):
    """
    Remove os primeiros N segundos de todos os arquivos MP3 em um diretório.
    
    Args:
        assets_dir (str): Caminho para o diretório com os arquivos MP3
        trim_seconds (int): Número de segundos para remover do início
    """
    # Encontrar todos os arquivos MP3
    mp3_files = glob.glob(os.path.join(assets_dir, "*.mp3"))
    
    if not mp3_files:
        print("❌ Nenhum arquivo MP3 encontrado na pasta assets")
        return
    
    print(f"🎵 Encontrados {len(mp3_files)} arquivos MP3")
    print(f"✂️  Removendo os primeiros {trim_seconds} segundos de cada arquivo...\n")
    
    for mp3_file in mp3_files:
        try:
            filename = os.path.basename(mp3_file)
            print(f"📁 Processando: {filename}")
            
            # Carregar o arquivo de áudio
            audio_clip = AudioFileClip(mp3_file)
            
            # Verificar se o arquivo tem pelo menos 10 segundos
            duration_seconds = audio_clip.duration
            if duration_seconds <= trim_seconds:
                print(f"⚠️  Arquivo {filename} tem apenas {duration_seconds:.1f}s - pulando")
                audio_clip.close()
                continue
            
            # Remover os primeiros 10 segundos
            trimmed_audio = audio_clip.subclip(trim_seconds)
            
            # Criar backup do arquivo original
            backup_file = mp3_file.replace('.mp3', '_original.mp3')
            os.rename(mp3_file, backup_file)
            print(f"💾 Backup criado: {os.path.basename(backup_file)}")
            
            # Salvar o arquivo cortado
            trimmed_audio.write_audiofile(mp3_file, verbose=False, logger=None)
            
            new_duration = trimmed_audio.duration
            print(f"✅ {filename}: {duration_seconds:.1f}s → {new_duration:.1f}s")
            print()
            
            # Fechar os clips para liberar recursos
            audio_clip.close()
            trimmed_audio.close()
            
        except Exception as e:
            print(f"❌ Erro ao processar {filename}: {str(e)}")
            print()

def main():
    # Caminho para a pasta assets
    script_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(script_dir, "assets")
    
    if not os.path.exists(assets_dir):
        print(f"❌ Pasta assets não encontrada: {assets_dir}")
        return
    
    print("🎬 Script para cortar arquivos MP3")
    print("=" * 50)
    
    # Executar o corte
    trim_audio_files(assets_dir, trim_seconds=10)
    
    print("🎉 Processamento concluído!")
    print("\n📝 Nota: Os arquivos originais foram salvos com sufixo '_original'")
    print("   Você pode removê-los depois de verificar que tudo está correto.")

if __name__ == "__main__":
    main()
