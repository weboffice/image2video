#!/usr/bin/env python3
"""
Script para migrar configurações existentes do MinIO/storage para o banco de dados
"""

import sys
import os
import json
from pathlib import Path

# Adicionar o diretório backend ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from video_config_db import create_video_config, get_video_config
from config import STORAGE_DIR
from minio_client import get_minio_client

def migrate_local_configs():
    """Migrar configurações dos arquivos locais para o banco"""
    
    print("🔍 Procurando configurações locais...")
    
    videos_dir = STORAGE_DIR / "videos"
    if not videos_dir.exists():
        print("📁 Diretório de vídeos não encontrado")
        return 0
    
    migrated_count = 0
    
    # Procurar por arquivos de configuração em subdiretórios
    for job_dir in videos_dir.iterdir():
        if job_dir.is_dir():
            config_file = job_dir / f"{job_dir.name}_config.json"
            if config_file.exists():
                try:
                    print(f"📄 Encontrado: {config_file}")
                    
                    with open(config_file, 'r') as f:
                        config_data = json.load(f)
                    
                    job_id = config_data.get("job_id", job_dir.name)
                    template_id = config_data.get("template", {}).get("id", "unknown")
                    
                    # Verificar se já existe no banco
                    existing = get_video_config(job_id)
                    if existing:
                        print(f"⚠️  Configuração {job_id} já existe no banco - pulando")
                        continue
                    
                    # Migrar para o banco
                    db_config = create_video_config(
                        job_id=job_id,
                        template_id=template_id,
                        config_data=config_data
                    )
                    
                    # Atualizar status e progresso se disponível
                    status = config_data.get("status", "created")
                    progress = config_data.get("progress", 0)
                    output_path = config_data.get("output_path")
                    error_message = config_data.get("error")
                    
                    if status != "created" or progress != 0 or output_path or error_message:
                        from video_config_db import update_video_config
                        update_video_config(
                            job_id=job_id,
                            status=status,
                            progress=progress,
                            output_path=output_path,
                            error_message=error_message
                        )
                    
                    print(f"✅ Migrado: {job_id} ({template_id})")
                    migrated_count += 1
                    
                except Exception as e:
                    print(f"❌ Erro ao migrar {config_file}: {e}")
    
    return migrated_count

def migrate_minio_configs():
    """Migrar configurações do MinIO para o banco"""
    
    print("🔍 Procurando configurações no MinIO...")
    
    try:
        minio_client = get_minio_client()
        
        # Listar arquivos de configuração no MinIO
        configs = minio_client.list_files("configs/")
        
        if not configs:
            print("📁 Nenhuma configuração encontrada no MinIO")
            return 0
        
        migrated_count = 0
        
        for config_key in configs:
            if config_key.endswith("_config.json"):
                try:
                    print(f"📄 Encontrado no MinIO: {config_key}")
                    
                    # Baixar configuração
                    temp_path = STORAGE_DIR / "temp_minio_config.json"
                    if minio_client.download_file(config_key, temp_path):
                        with open(temp_path, 'r') as f:
                            config_data = json.load(f)
                        
                        # Limpar arquivo temporário
                        temp_path.unlink()
                        
                        job_id = config_data.get("job_id")
                        if not job_id:
                            # Extrair job_id do nome do arquivo
                            job_id = config_key.replace("configs/", "").replace("_config.json", "")
                        
                        template_id = config_data.get("template", {}).get("id", "unknown")
                        
                        # Verificar se já existe no banco
                        existing = get_video_config(job_id)
                        if existing:
                            print(f"⚠️  Configuração {job_id} já existe no banco - pulando")
                            continue
                        
                        # Migrar para o banco
                        db_config = create_video_config(
                            job_id=job_id,
                            template_id=template_id,
                            config_data=config_data
                        )
                        
                        # Atualizar status e progresso se disponível
                        status = config_data.get("status", "created")
                        progress = config_data.get("progress", 0)
                        output_path = config_data.get("output_path")
                        error_message = config_data.get("error")
                        
                        if status != "created" or progress != 0 or output_path or error_message:
                            from video_config_db import update_video_config
                            update_video_config(
                                job_id=job_id,
                                status=status,
                                progress=progress,
                                output_path=output_path,
                                error_message=error_message
                            )
                        
                        print(f"✅ Migrado do MinIO: {job_id} ({template_id})")
                        migrated_count += 1
                    else:
                        print(f"❌ Falha ao baixar {config_key}")
                        
                except Exception as e:
                    print(f"❌ Erro ao migrar {config_key}: {e}")
        
        return migrated_count
        
    except Exception as e:
        print(f"❌ Erro ao acessar MinIO: {e}")
        return 0

def main():
    """Executar migração completa"""
    
    print("🚀 Iniciando migração de configurações para o banco de dados")
    print("=" * 60)
    
    # Migrar configurações locais
    local_count = migrate_local_configs()
    print(f"\n📊 Configurações locais migradas: {local_count}")
    
    # Migrar configurações do MinIO
    minio_count = migrate_minio_configs()
    print(f"📊 Configurações do MinIO migradas: {minio_count}")
    
    total_count = local_count + minio_count
    print(f"\n🎉 Total de configurações migradas: {total_count}")
    
    if total_count > 0:
        print("\n✅ Migração concluída com sucesso!")
        print("💡 Agora você pode remover os arquivos de configuração antigos")
    else:
        print("\n📝 Nenhuma configuração encontrada para migrar")

if __name__ == "__main__":
    main()
