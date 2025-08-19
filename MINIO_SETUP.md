# Configuração do MinIO para Image2Video

Este documento explica como configurar o MinIO para o projeto Image2Video.

## Configuração do MinIO

### 1. Instalar e Configurar MinIO

#### Opção 1: Docker (Recomendado)
```bash
# Criar container MinIO
docker run -d \
  --name minio \
  -p 6000:9000 \
  -p 6001:9001 \
  -e "MINIO_ROOT_USER=admin" \
  -e "MINIO_ROOT_PASSWORD=admin123" \
  -v minio_data:/data \
  minio/minio server /data --console-address ":9001"

# Acessar console web: http://localhost:6001
# Login: admin / admin123
```

#### Opção 2: Binário
```bash
# Baixar MinIO
wget https://dl.min.io/server/minio/release/linux-amd64/minio
chmod +x minio

# Executar MinIO
./minio server /data --console-address ":6001"
```

### 2. Configurar Bucket

1. Acesse o console web: http://localhost:6001
2. Faça login com: admin / admin123
3. Crie um bucket chamado `ghfimagevideo`
4. Configure as permissões do bucket como necessário

### 3. Configurar o Projeto

Execute o script de configuração:
```bash
./setup_minio.sh
```

Este script irá:
- Instalar as dependências Python
- Testar a conexão com o MinIO
- Configurar o ambiente

### 4. Variáveis de Ambiente

Crie um arquivo `.env` no diretório `backend/` com as seguintes configurações:

```env
# MinIO Configuration
MINIO_ENDPOINT=127.0.0.1:6000
MINIO_ACCESS_KEY=admin
MINIO_SECRET_KEY=admin123
MINIO_BUCKET=ghfimagevideo
MINIO_SECURE=false
MINIO_REGION=us-east-1

# Storage
STORAGE_DIR=./storage
PUBLIC_API_BASE=http://localhost:8080
```

## Mudanças Implementadas

### Backend

1. **Novo módulo MinIO**: `backend/minio_client.py`
   - Cliente MinIO configurável
   - Funções para upload, download, listagem
   - Geração de URLs pré-assinadas

2. **Modificações no main.py**:
   - Upload de arquivos agora vai para MinIO
   - Novo endpoint `/api/files/{object_key}` para servir arquivos
   - Endpoint `/api/files/{object_key}/info` para informações

3. **Modificações no video_processor.py**:
   - Suporte para baixar arquivos do MinIO durante processamento
   - Limpeza automática de arquivos temporários

### Frontend

1. **Modificações no PhotoUploader**:
   - Exibe imagens do MinIO quando disponíveis
   - Mantém compatibilidade com preview local

2. **Novas funções na API**:
   - `getFileURL()` para gerar URLs de arquivos do MinIO

## Testando a Configuração

### 1. Teste de Conexão
```bash
cd backend
source venv/bin/activate
python test_minio.py
```

### 2. Teste Manual
```bash
# Iniciar backend
cd backend
source venv/bin/activate
python main.py

# Em outro terminal, iniciar frontend
cd frontend
npm run dev
```

### 3. Verificar Funcionamento
1. Acesse http://localhost:5173
2. Faça upload de algumas fotos
3. Verifique se as imagens são exibidas corretamente
4. Verifique no console MinIO se os arquivos foram enviados

## Estrutura de Arquivos no MinIO

```
ghfimagevideo/
├── uploads/
│   └── {job_code}/
│       ├── {timestamp}_{uuid}_{filename}
│       └── ...
├── videos/
│   └── {job_id}_video.mp4
└── configs/
    └── {job_id}_config.json
```

## Troubleshooting

### Erro de Conexão
- Verifique se o MinIO está rodando: `docker ps` ou `ps aux | grep minio`
- Verifique as credenciais no arquivo `.env`
- Teste a conexão: `python test_minio.py`

### Erro de Upload
- Verifique se o bucket `ghfimagevideo` existe
- Verifique as permissões do bucket
- Verifique os logs do backend

### Imagens não aparecem
- Verifique se o frontend está usando a URL correta do MinIO
- Verifique se o arquivo existe no MinIO
- Verifique os logs do navegador para erros de CORS

## Benefícios da Migração para MinIO

1. **Escalabilidade**: MinIO pode ser distribuído e escalado horizontalmente
2. **Compatibilidade S3**: API compatível com Amazon S3
3. **Performance**: Otimizado para armazenamento de objetos
4. **Segurança**: Suporte a criptografia e políticas de acesso
5. **Monitoramento**: Console web para gerenciamento
6. **Backup**: Facilita backup e replicação de dados
