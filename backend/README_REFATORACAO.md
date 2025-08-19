# Refatoração do Backend - Estrutura Modular

## Visão Geral

O arquivo `main.py` foi refatorado para uma estrutura modular, dividindo as funcionalidades em routers especializados. Isso melhora a organização, manutenibilidade e escalabilidade do código.

## Nova Estrutura de Arquivos

```
backend/
├── main.py                 # Arquivo principal (agora simplificado)
├── config.py              # Configurações centralizadas
├── templates.py           # Templates de vídeo
├── routers/               # Pacote de routers
│   ├── __init__.py
│   ├── jobs.py            # Endpoints de jobs
│   ├── upload.py          # Endpoints de upload
│   ├── files.py           # Endpoints de arquivos
│   ├── templates.py       # Endpoints de templates
│   └── videos.py          # Endpoints de vídeos
├── database.py            # Configuração do banco
├── models.py              # Modelos do banco
├── minio_client.py        # Cliente MinIO
└── video_processor.py     # Processamento de vídeo
```

## Detalhes da Refatoração

### 1. `main.py` (Simplificado)
- **Antes**: 922 linhas com todos os endpoints
- **Depois**: ~70 linhas com configuração básica
- **Responsabilidades**:
  - Configuração do FastAPI
  - Configuração de CORS
  - Montagem de routers
  - Endpoints básicos (/, /health)

### 2. `config.py` (Novo)
- Centraliza configurações de armazenamento
- Define `STORAGE_DIR` e `PUBLIC_API_BASE`
- Garante criação de diretórios necessários

### 3. `templates.py` (Novo)
- Move todos os modelos de templates do `main.py`
- Define `SceneEffect`, `Scene`, `Template`
- Contém templates disponíveis (`DEFAULT_TEMPLATE`, `GRID_SHOWCASE_TEMPLATE`)

### 4. Routers Especializados

#### `routers/jobs.py`
- **Endpoints**: `/api/jobs/*`
- **Funcionalidades**:
  - Criação de jobs
  - Geração de URLs de upload
  - Status de jobs
  - Início de processamento
  - Stream de status

#### `routers/upload.py`
- **Endpoints**: `/api/upload/*`
- **Funcionalidades**:
  - Upload de arquivos para MinIO
  - Atualização de status no banco

#### `routers/files.py`
- **Endpoints**: `/api/files/*`, `/api/photos/*`
- **Funcionalidades**:
  - Servir arquivos do MinIO
  - Informações de arquivos
  - Informações de fotos específicas

#### `routers/templates.py`
- **Endpoints**: `/api/templates/*`
- **Funcionalidades**:
  - Listar templates disponíveis
  - Obter template específico

#### `routers/videos.py`
- **Endpoints**: `/api/videos/*`
- **Funcionalidades**:
  - Criação de vídeos
  - Status de processamento
  - Download de vídeos
  - Gerenciamento de jobs de vídeo

## Benefícios da Refatoração

### 1. Organização
- Cada router tem responsabilidades específicas
- Código mais fácil de navegar e entender
- Separação clara de funcionalidades

### 2. Manutenibilidade
- Mudanças em uma funcionalidade afetam apenas o router correspondente
- Facilita debugging e testes
- Reduz conflitos de merge

### 3. Escalabilidade
- Fácil adicionar novos routers
- Possibilidade de desabilitar routers específicos
- Melhor gerenciamento de dependências

### 4. Reutilização
- Routers podem ser importados em outros projetos
- Configurações centralizadas
- Modelos compartilhados

## Como Usar

### Execução Normal
```bash
cd backend
python main.py
```

### Importação em Outros Projetos
```python
from backend.main import app
from backend.routers import jobs, videos
```

### Adicionar Novo Router
1. Criar arquivo em `routers/novo_router.py`
2. Definir router com `APIRouter(prefix="/api/novo", tags=["novo"])`
3. Incluir em `main.py` com `app.include_router(novo_router.router)`

## Compatibilidade

- ✅ Todos os endpoints existentes mantidos
- ✅ Mesmas funcionalidades preservadas
- ✅ Compatível com frontend existente
- ✅ Configurações de MinIO mantidas

## Testes

Para verificar se a refatoração está funcionando:

```bash
# Testar importação dos routers
python -c "from routers import jobs, upload, files, templates, videos; print('✅ Routers OK')"

# Testar importação do app principal
python -c "from main import app; print('✅ App OK')"

# Testar inicialização
python -c "import uvicorn; from main import app; print('✅ Pronto para iniciar')"
```

## Próximos Passos

1. **Testes Unitários**: Criar testes para cada router
2. **Documentação da API**: Usar FastAPI docs automáticos
3. **Validação**: Adicionar mais validações com Pydantic
4. **Logging**: Implementar logging estruturado
5. **Monitoramento**: Adicionar métricas e health checks
