# Image2Video - Sistema Completo com MinIO

Este projeto agora está totalmente integrado com o MinIO como sistema de armazenamento principal, oferecendo melhor escalabilidade, performance e gerenciamento de arquivos.

## 🚀 Configuração Rápida

### 1. Configuração Automática (Recomendado)

Execute o script de configuração completa:

```bash
./setup_complete_minio.sh
```

Este script irá:
- ✅ Instalar todas as dependências
- ✅ Configurar o ambiente MinIO
- ✅ Migrar dados existentes
- ✅ Configurar frontend e backend
- ✅ Executar testes de validação

### 2. Configuração Manual

#### Pré-requisitos

1. **MinIO Server** rodando em `127.0.0.1:6000`
2. **Bucket** `ghfimagevideo` criado
3. **Credenciais**: `admin` / `admin123`

#### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python test_minio.py  # Testar conexão
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

## 🏗️ Arquitetura do Sistema

### Componentes Principais

1. **Backend (FastAPI)**
   - Upload direto para MinIO
   - Processamento de vídeos
   - API REST completa

2. **Frontend (React + TypeScript)**
   - Interface de upload
   - Visualização de imagens do MinIO
   - Gerenciamento de jobs

3. **MinIO Storage**
   - Armazenamento de imagens
   - Armazenamento de vídeos processados
   - URLs pré-assinadas

4. **Scripts de Processamento**
   - Geração de vídeos simples
   - Geração de vídeos com templates
   - Migração de dados

### Estrutura de Dados no MinIO

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

## 📁 Arquivos e Scripts

### Scripts Principais

- `setup_complete_minio.sh` - Configuração completa do sistema
- `scripts/migrate_to_minio.py` - Migração de dados existentes
- `scripts/simple_video_generator.py` - Gerador de vídeos simples
- `scripts/generate_video.py` - Gerador de vídeos com templates
- `scripts/test_template.py` - Testador de templates

### Backend

- `backend/main.py` - API principal com endpoints MinIO
- `backend/minio_client.py` - Cliente MinIO configurável
- `backend/video_processor.py` - Processador de vídeos com MinIO
- `backend/test_minio.py` - Testes de conexão MinIO

### Frontend

- `frontend/src/components/PhotoUploader.tsx` - Upload com MinIO
- `frontend/src/lib/api.ts` - API client com suporte MinIO

## 🔧 Configuração Detalhada

### Variáveis de Ambiente

Crie um arquivo `.env` no diretório `backend/`:

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

# Database
DATABASE_URL=mysql+pymysql://user:password@localhost/image2video

# Redis (for Celery)
REDIS_URL=redis://localhost:6379/0
```

### MinIO Server

#### Docker (Recomendado)

```bash
docker run -d \
  --name minio \
  -p 6000:9000 \
  -p 6001:9001 \
  -e "MINIO_ROOT_USER=admin" \
  -e "MINIO_ROOT_PASSWORD=admin123" \
  -v minio_data:/data \
  minio/minio server /data --console-address ":9001"
```

#### Binário

```bash
wget https://dl.min.io/server/minio/release/linux-amd64/minio
chmod +x minio
./minio server /data --console-address ":6001"
```

## 🚀 Uso do Sistema

### 1. Iniciar Serviços

```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate
python main.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### 2. Acessar Aplicação

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8080
- **MinIO Console**: http://localhost:6001 (admin/admin123)

### 3. Upload de Fotos

1. Acesse o frontend
2. Arraste fotos para a área de upload
3. As fotos são enviadas diretamente para o MinIO
4. Visualize as imagens carregadas do MinIO

### 4. Processamento de Vídeos

```bash
# Gerar vídeo simples
python scripts/simple_video_generator.py <job_id>

# Gerar vídeo com template
python scripts/generate_video.py <job_id> <template_id>

# Testar template
python scripts/test_template.py <job_id>
```

## 🔍 Monitoramento e Debug

### Logs do Backend

```bash
cd backend
source venv/bin/activate
python main.py
```

### Testar Conexão MinIO

```bash
cd backend
source venv/bin/activate
python test_minio.py
```

### Verificar Arquivos no MinIO

1. Acesse http://localhost:6001
2. Login: admin / admin123
3. Navegue pelo bucket `ghfimagevideo`

### API Endpoints

```bash
# Health check
curl http://localhost:8080/health

# Criar job
curl -X POST http://localhost:8080/api/jobs \
  -H "Content-Type: application/json" \
  -d '{"template_id": "thumbnail-zoom-template"}'

# Status do job
curl http://localhost:8080/api/jobs/{job_code}

# Download de arquivo do MinIO
curl http://localhost:8080/api/files/{object_key}
```

## 🔄 Migração de Dados

### Migrar Dados Existentes

```bash
python scripts/migrate_to_minio.py
```

Este script irá:
- Migrar fotos existentes para o MinIO
- Migrar vídeos processados para o MinIO
- Atualizar configurações para usar MinIO

### Estrutura de Migração

```
Antes:
storage/
├── uploads/
│   └── {job_id}/
│       └── {files}
└── videos/
    └── {job_id}_video.mp4

Depois:
MinIO Bucket: ghfimagevideo/
├── uploads/
│   └── {job_id}/
│       └── {files}
└── videos/
    └── {job_id}_video.mp4
```

## 🛠️ Desenvolvimento

### Adicionar Novos Endpoints

```python
# Em backend/main.py
@app.get("/api/minio/{object_key}")
async def get_minio_file(object_key: str):
    if not minio_client.file_exists(object_key):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    
    url = minio_client.get_file_url(object_key)
    return RedirectResponse(url=url)
```

### Adicionar Novos Scripts

```python
# Em scripts/
from backend.minio_client import minio_client

# Upload
success = minio_client.upload_file(object_key, file_path, content_type)

# Download
success = minio_client.download_file(object_key, local_path)

# Verificar existência
exists = minio_client.file_exists(object_key)

# Gerar URL
url = minio_client.get_file_url(object_key)
```

## 📊 Benefícios da Migração

### Performance
- ✅ Upload direto para MinIO (sem armazenamento local)
- ✅ URLs pré-assinadas para acesso rápido
- ✅ Limpeza automática de arquivos temporários

### Escalabilidade
- ✅ MinIO pode ser distribuído horizontalmente
- ✅ Suporte a múltiplos buckets
- ✅ Replicação automática

### Gerenciamento
- ✅ Console web para monitoramento
- ✅ Políticas de retenção configuráveis
- ✅ Backup e replicação facilitados

### Compatibilidade
- ✅ API compatível com Amazon S3
- ✅ Suporte a múltiplos formatos
- ✅ Integração com ferramentas existentes

## 🐛 Troubleshooting

### Problemas Comuns

1. **Erro de Conexão MinIO**
   ```bash
   # Verificar se MinIO está rodando
   docker ps | grep minio
   
   # Testar conexão
   cd backend && python test_minio.py
   ```

2. **Upload Falhando**
   ```bash
   # Verificar bucket
   curl -I http://localhost:6000/ghfimagevideo
   
   # Verificar permissões
   # Acesse console MinIO: http://localhost:6001
   ```

3. **Imagens não aparecem**
   ```bash
   # Verificar se arquivo existe no MinIO
   python -c "from minio_client import minio_client; print(minio_client.file_exists('uploads/job/file.jpg'))"
   
   # Verificar logs do frontend
   # Abra DevTools no navegador
   ```

4. **Vídeos não processam**
   ```bash
   # Verificar se fotos estão no MinIO
   python scripts/migrate_to_minio.py
   
   # Testar processamento manual
   python scripts/simple_video_generator.py <job_id>
   ```

## 📈 Próximos Passos

### Melhorias Futuras

1. **Cache Inteligente**
   - Cache local para arquivos frequentemente acessados
   - Invalidação automática de cache

2. **Processamento Assíncrono**
   - Filas de processamento com Celery
   - Notificações de progresso em tempo real

3. **Segurança Avançada**
   - Criptografia de arquivos
   - Políticas de acesso granulares
   - Auditoria de acesso

4. **Monitoramento**
   - Métricas de uso do MinIO
   - Alertas de espaço em disco
   - Logs estruturados

## 📞 Suporte

Para problemas ou dúvidas:

1. Verifique os logs do backend
2. Teste a conexão MinIO: `python test_minio.py`
3. Verifique o console MinIO: http://localhost:6001
4. Execute a migração: `python scripts/migrate_to_minio.py`

---

**🎉 Sistema totalmente configurado para usar MinIO!**
