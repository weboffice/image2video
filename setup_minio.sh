#!/bin/bash

echo "🚀 Configurando ambiente MinIO para o projeto Image2Video"

# Verificar se o Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 não encontrado. Por favor, instale o Python 3.8+"
    exit 1
fi

# Verificar se o pip está instalado
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 não encontrado. Por favor, instale o pip"
    exit 1
fi

echo "✅ Python e pip encontrados"

# Instalar dependências do backend
echo "📦 Instalando dependências do backend..."
cd backend

# Criar ambiente virtual se não existir
if [ ! -d "venv" ]; then
    echo "🔧 Criando ambiente virtual..."
    python3 -m venv venv
fi

# Ativar ambiente virtual
echo "🔧 Ativando ambiente virtual..."
source venv/bin/activate

# Instalar dependências
echo "📦 Instalando dependências..."
pip install -r requirements.txt

echo "✅ Dependências instaladas"

# Testar conexão com MinIO
echo "🔍 Testando conexão com MinIO..."
python test_minio.py

if [ $? -eq 0 ]; then
    echo "✅ Conexão com MinIO estabelecida com sucesso!"
else
    echo "❌ Falha na conexão com MinIO"
    echo "📋 Verifique se o MinIO está rodando em 127.0.0.1:6000"
    echo "📋 Verifique se as credenciais estão corretas (admin/admin123)"
    echo "📋 Verifique se o bucket 'ghfimagevideo' existe"
fi

# Voltar para o diretório raiz
cd ..

echo "🎉 Configuração concluída!"
echo ""
echo "📋 Para iniciar o backend:"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   python main.py"
echo ""
echo "📋 Para iniciar o frontend:"
echo "   cd frontend"
echo "   npm install"
echo "   npm run dev"
