import os
from minio import Minio
from minio.error import S3Error
from pathlib import Path
from typing import Optional, BinaryIO
import logging
import time

logger = logging.getLogger(__name__)

class MinioClient:
    def __init__(self):
        self.endpoint = os.getenv("MINIO_ENDPOINT", "storage.dev.localhost.com.br")
        self.access_key = os.getenv("MINIO_ACCESS_KEY", "admin")
        self.secret_key = os.getenv("MINIO_SECRET_KEY", "admin123")
        self.bucket_name = os.getenv("MINIO_BUCKET", "ghfimagevideo")
        self.secure = os.getenv("MINIO_SECURE", "false").lower() == "true"
        self.region = os.getenv("MINIO_REGION", "us-east-1")
        
        # Log das configurações (sem expor credenciais)
        logger.info(f"Inicializando MinIO Client:")
        logger.info(f"  Endpoint: {self.endpoint}")
        logger.info(f"  Bucket: {self.bucket_name}")
        logger.info(f"  Secure: {self.secure}")
        logger.info(f"  Region: {self.region}")
        logger.info(f"  Access Key: {self.access_key[:4]}***")
        
        try:
            self.client = Minio(
                self.endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=self.secure,
                region=self.region
            )
            
            # Testar conectividade antes de tentar criar bucket
            self._test_connection()
            self._ensure_bucket_exists()
            
        except Exception as e:
            logger.error(f"Erro ao inicializar cliente MinIO: {e}")
            raise
    
    def _test_connection(self):
        """Testar conectividade básica com o MinIO"""
        try:
            # Tentar listar buckets como teste de conectividade
            buckets = list(self.client.list_buckets())
            logger.info(f"✅ Conectividade MinIO OK. Buckets encontrados: {len(buckets)}")
            for bucket in buckets:
                logger.info(f"  - {bucket.name} (criado em: {bucket.creation_date})")
        except S3Error as e:
            logger.error(f"❌ Erro de conectividade MinIO: {e}")
            if "AccessDenied" in str(e):
                logger.error("🔑 Verifique as credenciais de acesso (MINIO_ACCESS_KEY/MINIO_SECRET_KEY)")
            elif "InvalidRequest" in str(e):
                logger.error("🌐 Verifique o endpoint e configuração HTTPS/HTTP (MINIO_SECURE)")
            raise
        except Exception as e:
            logger.error(f"❌ Erro inesperado ao testar conectividade: {e}")
            raise
    
    def _ensure_bucket_exists(self):
        """Garantir que o bucket existe"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                logger.info(f"Bucket '{self.bucket_name}' não existe. Tentando criar...")
                self.client.make_bucket(self.bucket_name, location=self.region)
                logger.info(f"✅ Bucket '{self.bucket_name}' criado com sucesso")
            else:
                logger.info(f"✅ Bucket '{self.bucket_name}' já existe")
        except S3Error as e:
            logger.error(f"❌ Erro ao verificar/criar bucket '{self.bucket_name}': {e}")
            if "AccessDenied" in str(e):
                logger.error("🔑 Sem permissão para criar/verificar bucket. Verifique as credenciais e permissões.")
                logger.error("💡 Dica: O usuário precisa ter permissões de 's3:CreateBucket' e 's3:ListBucket'")
            elif "BucketAlreadyOwnedByYou" in str(e):
                logger.warning("⚠️  Bucket já existe e pertence a você. Continuando...")
                return  # Não é um erro crítico
            raise
    
    def upload_file(self, object_name: str, file_path: Path, content_type: Optional[str] = None) -> bool:
        """Fazer upload de um arquivo para o MinIO"""
        try:
            self.client.fput_object(
                self.bucket_name,
                object_name,
                str(file_path),
                content_type=content_type
            )
            logger.info(f"Arquivo '{object_name}' enviado com sucesso")
            return True
        except S3Error as e:
            logger.error(f"Erro ao fazer upload do arquivo '{object_name}': {e}")
            return False
    
    def upload_data(self, object_name: str, data: bytes, content_type: Optional[str] = None) -> bool:
        """Fazer upload de dados em bytes para o MinIO"""
        try:
            from io import BytesIO
            data_stream = BytesIO(data)
            self.client.put_object(
                self.bucket_name,
                object_name,
                data_stream,
                length=len(data),
                content_type=content_type
            )
            logger.info(f"Dados '{object_name}' enviados com sucesso")
            return True
        except S3Error as e:
            logger.error(f"Erro ao fazer upload dos dados '{object_name}': {e}")
            return False
    
    def download_file(self, object_name: str, file_path: Path) -> bool:
        """Baixar um arquivo do MinIO"""
        try:
            self.client.fget_object(self.bucket_name, object_name, str(file_path))
            logger.info(f"Arquivo '{object_name}' baixado com sucesso")
            return True
        except S3Error as e:
            logger.error(f"Erro ao baixar arquivo '{object_name}': {e}")
            return False
    
    def get_file_url(self, object_name: str, expires: int = 3600) -> Optional[str]:
        """Gerar URL pré-assinada para download"""
        try:
            from datetime import timedelta
            url = self.client.presigned_get_object(
                self.bucket_name,
                object_name,
                expires=timedelta(seconds=expires)
            )
            return url
        except Exception as e:
            logger.error(f"Erro ao gerar URL para '{object_name}': {e}")
            return None
    
    def delete_file(self, object_name: str) -> bool:
        """Deletar um arquivo do MinIO"""
        try:
            # Verificar se o arquivo existe antes de tentar deletar
            if not self.file_exists(object_name):
                logger.warning(f"⚠️  Arquivo '{object_name}' não existe. Nada para deletar.")
                return True  # Considerar como sucesso se o arquivo já não existe
            
            self.client.remove_object(self.bucket_name, object_name)
            logger.info(f"✅ Arquivo '{object_name}' deletado com sucesso")
            return True
        except S3Error as e:
            logger.error(f"❌ Erro ao deletar arquivo '{object_name}': {e}")
            if "AccessDenied" in str(e):
                logger.error("🔑 Sem permissão para deletar arquivo. Verifique as credenciais e permissões.")
                logger.error("💡 Dica: O usuário precisa ter permissão de 's3:DeleteObject'")
            elif "NoSuchKey" in str(e):
                logger.warning("⚠️  Arquivo não encontrado. Pode já ter sido deletado.")
                return True  # Considerar como sucesso se o arquivo não existe
            return False
        except Exception as e:
            logger.error(f"❌ Erro inesperado ao deletar arquivo '{object_name}': {e}")
            return False
    
    def file_exists(self, object_name: str) -> bool:
        """Verificar se um arquivo existe no MinIO"""
        try:
            self.client.stat_object(self.bucket_name, object_name)
            return True
        except S3Error:
            return False
    
    def get_file_info(self, object_name: str) -> Optional[dict]:
        """Obter informações de um arquivo"""
        try:
            stat = self.client.stat_object(self.bucket_name, object_name)
            return {
                "size": stat.size,
                "content_type": stat.content_type,
                "last_modified": stat.last_modified,
                "etag": stat.etag
            }
        except S3Error as e:
            logger.error(f"Erro ao obter informações do arquivo '{object_name}': {e}")
            return None

# Instância global do cliente MinIO (inicializada sob demanda)
minio_client = None

def get_minio_client():
    """Obter instância do cliente MinIO (lazy loading)"""
    global minio_client
    if minio_client is None:
        minio_client = MinioClient()
    return minio_client
