#!/usr/bin/env python3
"""
Script para migrar dados existentes para o MinIO.
Uso: python scripts/migrate_to_minio.py
"""

import sys
import os
from pathlib import Path
import json
from typing import List, Dict, Any

# Adicionar o diretório backend ao path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

# Imports para MinIO
try:
    from backend.minio_client import minio_client
except ImportError:
    from minio_client import minio_client

class MinioMigrator:
    def __init__(self):
        self.storage_dir = Path(__file__).parent.parent / "backend" / "storage"
        self.uploads_dir = self.storage_dir / "uploads"
        self.videos_dir = self.storage_dir / "videos"
        
    def migrate_uploads(self) -> Dict[str, Any]:
        """Migra arquivos de upload para o MinIO"""
        print("🔄 Migrando arquivos de upload...")
        
        migrated = 0
        failed = 0
        skipped = 0
        
        if not self.uploads_dir.exists():
            print("⚠️  Diretório de uploads não encontrado")
            return {"migrated": 0, "failed": 0, "skipped": 0}
        
        # Percorrer todos os diretórios de job
        for job_dir in self.uploads_dir.iterdir():
            if job_dir.is_dir():
                print(f"📁 Processando job: {job_dir.name}")
                
                for file_path in job_dir.iterdir():
                    if file_path.is_file() and file_path.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                        # Construir object key
                        relative_path = file_path.relative_to(self.storage_dir)
                        object_key = str(relative_path)
                        
                        # Verificar se já existe no MinIO
                        if minio_client.file_exists(object_key):
                            print(f"   ⏭️  Já existe no MinIO: {object_key}")
                            skipped += 1
                            continue
                        
                        # Fazer upload para MinIO
                        try:
                            success = minio_client.upload_file(object_key, file_path, "image/jpeg")
                            if success:
                                print(f"   ✅ Migrado: {object_key}")
                                migrated += 1
                            else:
                                print(f"   ❌ Falha: {object_key}")
                                failed += 1
                        except Exception as e:
                            print(f"   ❌ Erro: {object_key} - {e}")
                            failed += 1
        
        print(f"📊 Uploads: {migrated} migrados, {failed} falharam, {skipped} pulados")
        return {"migrated": migrated, "failed": failed, "skipped": skipped}
    
    def migrate_videos(self) -> Dict[str, Any]:
        """Migra vídeos processados para o MinIO"""
        print("🔄 Migrando vídeos processados...")
        
        migrated = 0
        failed = 0
        skipped = 0
        
        if not self.videos_dir.exists():
            print("⚠️  Diretório de vídeos não encontrado")
            return {"migrated": 0, "failed": 0, "skipped": 0}
        
        # Procurar por arquivos de vídeo
        for video_file in self.videos_dir.glob("*.mp4"):
            # Construir object key
            object_key = f"videos/{video_file.name}"
            
            # Verificar se já existe no MinIO
            if minio_client.file_exists(object_key):
                print(f"   ⏭️  Já existe no MinIO: {object_key}")
                skipped += 1
                continue
            
            # Fazer upload para MinIO
            try:
                success = minio_client.upload_file(object_key, video_file, "video/mp4")
                if success:
                    print(f"   ✅ Migrado: {object_key}")
                    migrated += 1
                else:
                    print(f"   ❌ Falha: {object_key}")
                    failed += 1
            except Exception as e:
                print(f"   ❌ Erro: {object_key} - {e}")
                failed += 1
        
        print(f"📊 Vídeos: {migrated} migrados, {failed} falharam, {skipped} pulados")
        return {"migrated": migrated, "failed": failed, "skipped": skipped}
    
    def migrate_configs(self) -> Dict[str, Any]:
        """Migra configurações JSON para o MinIO"""
        print("🔄 Migrando configurações JSON...")
        
        migrated = 0
        failed = 0
        skipped = 0
        
        if not self.videos_dir.exists():
            print("⚠️  Diretório de vídeos não encontrado")
            return {"migrated": 0, "failed": 0, "skipped": 0}
        
        # Procurar por arquivos de configuração
        for config_file in self.videos_dir.glob("*_config.json"):
            # Construir object key
            object_key = f"configs/{config_file.name}"
            
            # Verificar se já existe no MinIO
            if minio_client.file_exists(object_key):
                print(f"   ⏭️  Já existe no MinIO: {object_key}")
                skipped += 1
                continue
            
            # Fazer upload para MinIO
            try:
                success = minio_client.upload_file(object_key, config_file, "application/json")
                if success:
                    print(f"   ✅ Migrado: {object_key}")
                    migrated += 1
                else:
                    print(f"   ❌ Falha: {object_key}")
                    failed += 1
            except Exception as e:
                print(f"   ❌ Erro: {object_key} - {e}")
                failed += 1
        
        print(f"📊 Configurações: {migrated} migradas, {failed} falharam, {skipped} puladas")
        return {"migrated": migrated, "failed": failed, "skipped": skipped}
    
    def update_configs(self) -> Dict[str, Any]:
        """Atualiza configurações para usar MinIO"""
        print("🔄 Atualizando configurações...")
        
        updated = 0
        failed = 0
        
        if not self.videos_dir.exists():
            print("⚠️  Diretório de vídeos não encontrado")
            return {"updated": 0, "failed": 0}
        
        # Procurar por arquivos de configuração
        for config_file in self.videos_dir.glob("*_config.json"):
            try:
                # Carregar configuração
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                modified = False
                
                # Atualizar caminhos de fotos para MinIO
                if 'photos' in config:
                    for photo in config['photos']:
                        if 'filePath' in photo:
                            # Verificar se o arquivo existe no MinIO
                            if minio_client.file_exists(photo['filePath']):
                                # Manter o caminho como está (já está no formato correto)
                                pass
                            else:
                                print(f"   ⚠️  Foto não encontrada no MinIO: {photo['filePath']}")
                
                # Atualizar caminho do vídeo se existir
                if 'output_path' in config and config['output_path']:
                    video_name = Path(config['output_path']).name
                    video_object_key = f"videos/{video_name}"
                    
                    if minio_client.file_exists(video_object_key):
                        config['output_path'] = f"minio://{video_object_key}"
                        modified = True
                        print(f"   ✅ Vídeo atualizado para MinIO: {video_object_key}")
                
                # Salvar configuração se foi modificada
                if modified:
                    with open(config_file, 'w') as f:
                        json.dump(config, f, indent=2)
                    updated += 1
                    print(f"   📝 Configuração atualizada: {config_file.name}")
                
            except Exception as e:
                print(f"   ❌ Erro ao atualizar {config_file.name}: {e}")
                failed += 1
        
        print(f"📊 Configurações: {updated} atualizadas, {failed} falharam")
        return {"updated": updated, "failed": failed}
    
    def run_migration(self):
        """Executa a migração completa"""
        print("🚀 Iniciando migração para MinIO...")
        print("=" * 50)
        
        # Testar conexão com MinIO
        try:
            if not minio_client.client.bucket_exists(minio_client.bucket_name):
                print("❌ Bucket não encontrado. Criando...")
                minio_client.client.make_bucket(minio_client.bucket_name)
                print("✅ Bucket criado com sucesso")
        except Exception as e:
            print(f"❌ Erro ao conectar com MinIO: {e}")
            return
        
        # Migrar uploads
        uploads_result = self.migrate_uploads()
        
        # Migrar vídeos
        videos_result = self.migrate_videos()
        
        # Migrar configurações
        configs_migrate_result = self.migrate_configs()
        
        # Atualizar configurações
        configs_result = self.update_configs()
        
        # Resumo final
        print("=" * 50)
        print("📊 RESUMO DA MIGRAÇÃO")
        print("=" * 50)
        print(f"📤 Uploads: {uploads_result['migrated']} migrados, {uploads_result['failed']} falharam")
        print(f"🎬 Vídeos: {videos_result['migrated']} migrados, {videos_result['failed']} falharam")
        print(f"📄 Configurações: {configs_migrate_result['migrated']} migradas, {configs_migrate_result['failed']} falharam")
        print(f"⚙️  Configurações: {configs_result['updated']} atualizadas")
        print("=" * 50)
        
        total_migrated = uploads_result['migrated'] + videos_result['migrated'] + configs_migrate_result['migrated']
        total_failed = uploads_result['failed'] + videos_result['failed'] + configs_migrate_result['failed']
        
        if total_failed == 0:
            print("🎉 Migração concluída com sucesso!")
        else:
            print(f"⚠️  Migração concluída com {total_failed} falhas")

def main():
    migrator = MinioMigrator()
    migrator.run_migration()

if __name__ == "__main__":
    main()
