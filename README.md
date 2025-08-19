# Image2Video - Sistema de Conversão de Imagens para Vídeo

Este projeto integra um frontend React com um backend FastAPI para conversão de imagens em vídeo.

## 🚀 Início Rápido

### Pré-requisitos

- Node.js 18+
- Python 3.8+
- pip

### Instalação

1. **Instalar todas as dependências:**
```bash
npm run install:all
```

2. **Configurar variáveis de ambiente:**
```bash
# Copiar arquivo de exemplo
cp frontend/env.example frontend/.env
```

3. **Iniciar desenvolvimento:**
```bash
npm run dev
```

Isso iniciará:
- Backend na porta 8000 (http://localhost:8000)
- Frontend na porta 5173 (http://localhost:5173)

## 📁 Estrutura do Projeto

```
├── frontend/          # Aplicação React + Vite
│   ├── src/
│   │   ├── lib/api.ts        # Configuração da API
│   │   ├── hooks/useApi.ts   # Hooks React Query
│   │   ├── types/api.ts      # Tipos TypeScript
│   │   └── components/       # Componentes React
│   └── vite.config.ts        # Configuração do Vite com proxy
├── backend/           # API FastAPI
│   ├── main.py       # Servidor principal
│   ├── models.py     # Modelos do banco
│   └── database.py   # Configuração do banco
└── storage/          # Arquivos enviados
```

## 🔧 Configuração

### Frontend

O frontend está configurado com:

- **Proxy do Vite**: Redireciona `/api` e `/files` para o backend
- **React Query**: Para gerenciamento de estado e cache
- **TypeScript**: Tipos seguros para a API
- **Hooks personalizados**: Para operações da API

### Backend

O backend está configurado com:

- **CORS**: Permitindo requisições do frontend
- **FastAPI**: API REST moderna
- **SQLAlchemy**: ORM para banco de dados
- **Upload de arquivos**: Sistema de upload seguro

## 📡 API Endpoints

### Jobs
- `POST /api/jobs` - Criar novo job
- `GET /api/jobs/{job_code}` - Obter status do job
- `POST /api/jobs/{job_code}/start` - Iniciar processamento

### Upload
- `POST /api/upload-url` - Obter URL de upload
- `PUT /api/upload/{object_key}` - Fazer upload de arquivo

### Sistema
- `GET /health` - Health check
- `GET /` - Status da API

## 🎯 Como Usar

### 1. Criar um Job

```typescript
import { useCreateJob } from '@/hooks/useApi';

const MyComponent = () => {
  const createJob = useCreateJob();
  
  const handleCreate = () => {
    createJob.mutate({ template_id: 'optional' });
  };
  
  return <button onClick={handleCreate}>Criar Job</button>;
};
```

### 2. Fazer Upload de Arquivo

```typescript
import { useUploadURL, useUploadFile } from '@/hooks/useApi';

const UploadComponent = () => {
  const uploadURL = useUploadURL();
  const uploadFile = useUploadFile();
  
  const handleUpload = async (file: File, jobCode: string) => {
    // 1. Obter URL de upload
    const urlResponse = await uploadURL.mutateAsync({
      filename: file.name,
      content_type: file.type,
      job_code: jobCode
    });
    
    // 2. Fazer upload
    await uploadFile.mutateAsync({
      uploadUrl: urlResponse.upload_url,
      file: file
    });
  };
};
```

### 3. Monitorar Status

```typescript
import { useJobStatus } from '@/hooks/useApi';

const JobStatus = ({ jobCode }: { jobCode: string }) => {
  const { data: job, isLoading } = useJobStatus(jobCode);
  
  if (isLoading) return <div>Carregando...</div>;
  
  return (
    <div>
      Status: {job?.status}
      Progresso: {job?.progress}%
    </div>
  );
};
```

## 🔍 Debugging

### Verificar Status da API

O componente `ApiStatus` mostra se a API está online:

```typescript
import { ApiStatus } from '@/components/ApiStatus';

// No seu componente
<ApiStatus />
```

### Logs do Backend

```bash
# Ver logs em tempo real
cd backend && python main.py
```

### Logs do Frontend

```bash
# Ver logs do Vite
cd frontend && npm run dev
```

## 🚨 Solução de Problemas

### CORS Errors

Se você ver erros de CORS, verifique:

1. O backend está rodando na porta 8000
2. O frontend está rodando na porta 5173
3. As origens estão configuradas no `backend/main.py`

### Proxy não funciona

Verifique se o proxy está configurado no `frontend/vite.config.ts`:

```typescript
proxy: {
  "/api": {
    target: "http://localhost:8000",
    changeOrigin: true,
  },
}
```

### Upload falha

1. Verifique se o diretório `storage/` existe
2. Verifique permissões de escrita
3. Verifique se o `job_code` é válido

## 📝 Desenvolvimento

### Adicionar novo endpoint

1. Adicione o endpoint no `backend/main.py`
2. Adicione o tipo no `frontend/src/types/api.ts`
3. Adicione a função no `frontend/src/lib/api.ts`
4. Crie um hook no `frontend/src/hooks/useApi.ts`

### Estrutura de um novo hook

```typescript
export const useNewFeature = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data) => api.newFeature(data),
    onSuccess: (data) => {
      toast.success('Sucesso!');
      queryClient.invalidateQueries({ queryKey: ['relevant-data'] });
    },
    onError: (error) => {
      toast.error(`Erro: ${error.message}`);
    },
  });
};
```

## 🎉 Próximos Passos

- [ ] Implementar autenticação
- [ ] Adicionar testes
- [ ] Configurar CI/CD
- [ ] Deploy em produção
- [ ] Documentação da API (Swagger)
