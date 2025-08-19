#!/usr/bin/env python3
"""
Script para testar a conexão com o MinIO
"""

import os
from pathlib import Path
from minio_client import minio_client

def test_minio_connection():
    """Testa a conexão com o MinIO"""
    print("🔍 Testando conexão com MinIO...")
    
    try:
        # Testar se o bucket existe
        bucket_exists = minio_client.client.bucket_exists(minio_client.bucket_name)
        print(f"✅ Bucket '{minio_client.bucket_name}' existe: {bucket_exists}")
        
        if not bucket_exists:
            print("📦 Criando bucket...")
            minio_client.client.make_bucket(minio_client.bucket_name)
            print(f"✅ Bucket '{minio_client.bucket_name}' criado com sucesso")
        
        # Testar upload de um arquivo pequeno
        test_data = b"Hello MinIO!"
        test_object = "test/hello.txt"
        
        print(f"📤 Fazendo upload de teste: {test_object}")
        success = minio_client.upload_data(test_object, test_data, "text/plain")
        
        if success:
            print("✅ Upload de teste bem-sucedido")
            
            # Testar se o arquivo existe
            exists = minio_client.file_exists(test_object)
            print(f"✅ Arquivo existe: {exists}")
            
            # Testar obter informações do arquivo
            info = minio_client.get_file_info(test_object)
            print(f"✅ Informações do arquivo: {info}")
            
            # Testar gerar URL
            url = minio_client.get_file_url(test_object)
            print(f"✅ URL gerada: {url}")
            
            # Limpar arquivo de teste
            minio_client.delete_file(test_object)
            print("✅ Arquivo de teste removido")
            
        else:
            print("❌ Falha no upload de teste")
            
    except Exception as e:
        print(f"❌ Erro ao testar MinIO: {e}")
        return False
    
    print("🎉 Todos os testes passaram!")
    return True

if __name__ == "__main__":
    # Configurar variáveis de ambiente para teste
    os.environ.setdefault("MINIO_ENDPOINT", "127.0.0.1:6000")
    os.environ.setdefault("MINIO_ACCESS_KEY", "admin")
    os.environ.setdefault("MINIO_SECRET_KEY", "admin123")
    os.environ.setdefault("MINIO_BUCKET", "ghfimagevideo")
    os.environ.setdefault("MINIO_SECURE", "false")
    os.environ.setdefault("MINIO_REGION", "us-east-1")
    
    success = test_minio_connection()
    exit(0 if success else 1)
