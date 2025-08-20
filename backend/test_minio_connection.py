#!/usr/bin/env python3
"""
Script para testar conectividade e permissões do MinIO
"""

import os
import sys
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_minio_connection():
    """Testar conectividade completa com MinIO"""
    print("🔍 Testando conectividade MinIO...")
    print("=" * 50)
    
    # Mostrar configurações atuais
    print("📋 Configurações atuais:")
    print(f"  MINIO_ENDPOINT: {os.getenv('MINIO_ENDPOINT', 'NÃO DEFINIDO')}")
    print(f"  MINIO_BUCKET: {os.getenv('MINIO_BUCKET', 'NÃO DEFINIDO')}")
    print(f"  MINIO_SECURE: {os.getenv('MINIO_SECURE', 'NÃO DEFINIDO')}")
    print(f"  MINIO_REGION: {os.getenv('MINIO_REGION', 'NÃO DEFINIDO')}")
    access_key = os.getenv('MINIO_ACCESS_KEY', 'NÃO DEFINIDO')
    if access_key != 'NÃO DEFINIDO':
        print(f"  MINIO_ACCESS_KEY: {access_key[:4]}***")
    else:
        print(f"  MINIO_ACCESS_KEY: {access_key}")
    print()
    
    try:
        from minio_client import get_minio_client
        
        print("🚀 Inicializando cliente MinIO...")
        client = get_minio_client()
        print("✅ Cliente MinIO inicializado com sucesso!")
        print()
        
        # Teste 1: Listar buckets
        print("📋 Teste 1: Listando buckets...")
        try:
            buckets = list(client.client.list_buckets())
            print(f"✅ Encontrados {len(buckets)} buckets:")
            for bucket in buckets:
                print(f"  - {bucket.name} (criado: {bucket.creation_date})")
        except Exception as e:
            print(f"❌ Erro ao listar buckets: {e}")
            return False
        print()
        
        # Teste 2: Verificar bucket específico
        print(f"🪣 Teste 2: Verificando bucket '{client.bucket_name}'...")
        try:
            exists = client.client.bucket_exists(client.bucket_name)
            if exists:
                print(f"✅ Bucket '{client.bucket_name}' existe!")
            else:
                print(f"⚠️  Bucket '{client.bucket_name}' não existe.")
        except Exception as e:
            print(f"❌ Erro ao verificar bucket: {e}")
            return False
        print()
        
        # Teste 3: Upload de teste
        print("📤 Teste 3: Upload de arquivo de teste...")
        test_object = "test/connectivity_test.txt"
        test_data = b"Teste de conectividade MinIO - " + str(os.getpid()).encode()
        
        try:
            success = client.upload_data(test_object, test_data, "text/plain")
            if success:
                print(f"✅ Upload de teste realizado com sucesso!")
            else:
                print(f"❌ Falha no upload de teste")
                return False
        except Exception as e:
            print(f"❌ Erro no upload de teste: {e}")
            return False
        print()
        
        # Teste 4: Verificar se arquivo existe
        print("🔍 Teste 4: Verificando existência do arquivo...")
        try:
            exists = client.file_exists(test_object)
            if exists:
                print(f"✅ Arquivo de teste encontrado!")
            else:
                print(f"❌ Arquivo de teste não encontrado")
                return False
        except Exception as e:
            print(f"❌ Erro ao verificar arquivo: {e}")
            return False
        print()
        
        # Teste 5: Obter informações do arquivo
        print("ℹ️  Teste 5: Obtendo informações do arquivo...")
        try:
            info = client.get_file_info(test_object)
            if info:
                print(f"✅ Informações obtidas:")
                print(f"  - Tamanho: {info['size']} bytes")
                print(f"  - Tipo: {info['content_type']}")
                print(f"  - Modificado: {info['last_modified']}")
            else:
                print(f"❌ Não foi possível obter informações")
                return False
        except Exception as e:
            print(f"❌ Erro ao obter informações: {e}")
            return False
        print()
        
        # Teste 6: Gerar URL pré-assinada
        print("🔗 Teste 6: Gerando URL pré-assinada...")
        try:
            url = client.get_file_url(test_object, expires=300)  # 5 minutos
            if url:
                print(f"✅ URL gerada com sucesso!")
                print(f"  URL: {url[:50]}...")
            else:
                print(f"❌ Não foi possível gerar URL")
                return False
        except Exception as e:
            print(f"❌ Erro ao gerar URL: {e}")
            return False
        print()
        
        # Teste 7: Deletar arquivo de teste
        print("🗑️  Teste 7: Deletando arquivo de teste...")
        try:
            success = client.delete_file(test_object)
            if success:
                print(f"✅ Arquivo de teste deletado com sucesso!")
            else:
                print(f"❌ Falha ao deletar arquivo de teste")
                return False
        except Exception as e:
            print(f"❌ Erro ao deletar arquivo: {e}")
            return False
        print()
        
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Conectividade MinIO está funcionando corretamente!")
        return True
        
    except Exception as e:
        print(f"❌ ERRO CRÍTICO: {e}")
        print("\n💡 Possíveis soluções:")
        print("1. Verifique se as variáveis de ambiente estão corretas")
        print("2. Confirme se o servidor MinIO está acessível")
        print("3. Valide as credenciais de acesso")
        print("4. Verifique se MINIO_SECURE está configurado corretamente")
        return False

def suggest_fixes():
    """Sugerir correções baseadas na configuração atual"""
    print("\n🔧 SUGESTÕES DE CORREÇÃO:")
    print("=" * 50)
    
    endpoint = os.getenv('MINIO_ENDPOINT', '')
    secure = os.getenv('MINIO_SECURE', 'false').lower() == 'true'
    
    if 'https://' in endpoint or endpoint.endswith('.com') or endpoint.endswith('.br'):
        if not secure:
            print("⚠️  POSSÍVEL PROBLEMA DETECTADO:")
            print(f"   Endpoint '{endpoint}' parece ser HTTPS, mas MINIO_SECURE=false")
            print("   Tente alterar para: MINIO_SECURE=true")
            print()
    
    if endpoint.startswith('http://') or endpoint.startswith('https://'):
        print("⚠️  POSSÍVEL PROBLEMA DETECTADO:")
        print(f"   Endpoint não deve incluir protocolo: {endpoint}")
        print(f"   Tente usar apenas: {endpoint.replace('https://', '').replace('http://', '')}")
        print()
    
    print("📝 Configuração recomendada para seu caso:")
    print("MINIO_ENDPOINT=cdn.preparaconcursos.com.br")
    print("MINIO_ACCESS_KEY=admin")
    print("MINIO_SECRET_KEY=SenhaFort3!")
    print("MINIO_BUCKET=ghfimagevideo")
    print("MINIO_SECURE=true  # Tente com true se o endpoint usa HTTPS")
    print("MINIO_REGION=us-east-1")

if __name__ == "__main__":
    success = test_minio_connection()
    
    if not success:
        suggest_fixes()
        sys.exit(1)
    else:
        print("\n🚀 Sistema pronto para uso!")
        sys.exit(0)
