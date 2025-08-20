#!/bin/bash

# Script para fazer build de produção do Image2Video

echo "🏗️  Build de Produção - Image2Video"
echo "=================================="

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Diretórios do projeto (relativos)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
BUILD_DIR="$SCRIPT_DIR/../../build"

# Função para verificar se os diretórios existem
check_directories() {
    echo -e "${BLUE}📁 Verificando estrutura do projeto...${NC}"
    
    if [ ! -d "$PROJECT_DIR" ]; then
        echo -e "${RED}❌ Diretório do projeto não encontrado: $PROJECT_DIR${NC}"
        exit 1
    fi
    
    if [ ! -d "$BACKEND_DIR" ]; then
        echo -e "${RED}❌ Diretório do backend não encontrado: $BACKEND_DIR${NC}"
        exit 1
    fi
    
    if [ ! -d "$FRONTEND_DIR" ]; then
        echo -e "${RED}❌ Diretório do frontend não encontrado: $FRONTEND_DIR${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Estrutura do projeto verificada${NC}"
}

# Função para criar diretório de build
create_build_directory() {
    echo -e "${BLUE}📁 Preparando diretório de build...${NC}"
    
    # Remover build anterior se existir
    if [ -d "$BUILD_DIR" ]; then
        echo -e "${YELLOW}   Removendo build anterior...${NC}"
        rm -rf "$BUILD_DIR"
    fi
    
    # Criar novo diretório de build
    mkdir -p "$BUILD_DIR"
    mkdir -p "$BUILD_DIR/backend"
    mkdir -p "$BUILD_DIR/frontend"
    
    echo -e "${GREEN}✅ Diretório de build criado: $BUILD_DIR${NC}"
}

# Função para fazer build do backend
build_backend() {
    echo -e "${BLUE}🐍 Fazendo build do backend...${NC}"
    
    cd "$BACKEND_DIR"
    
    # Verificar se o ambiente virtual existe
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}   Criando ambiente virtual...${NC}"
        python3 -m venv venv
    fi
    
    # Ativar ambiente virtual
    source venv/bin/activate
    
    # Instalar/atualizar dependências
    echo -e "${YELLOW}   Instalando dependências...${NC}"
    pip install -r requirements.txt > /dev/null 2>&1
    
    # Copiar arquivos do backend para build
    echo -e "${YELLOW}   Copiando arquivos do backend...${NC}"
    cp -r . "$BUILD_DIR/backend/"
    
    # Remover arquivos desnecessários do build
    rm -rf "$BUILD_DIR/backend/__pycache__"
    find "$BUILD_DIR/backend" -name "*.pyc" -delete
    find "$BUILD_DIR/backend" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    
    # Criar script de inicialização para produção
    cat > "$BUILD_DIR/backend/start-production.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python main.py
EOF
    chmod +x "$BUILD_DIR/backend/start-production.sh"
    
    echo -e "${GREEN}✅ Build do backend concluído${NC}"
}

# Função para fazer build do frontend
build_frontend() {
    echo -e "${BLUE}⚛️  Fazendo build do frontend...${NC}"
    
    cd "$FRONTEND_DIR"
    
    # Verificar se node_modules existe
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}   Instalando dependências do frontend...${NC}"
        npm install
    fi
    
    # Fazer build de produção
    echo -e "${YELLOW}   Executando build de produção...${NC}"
    npm run build
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Falha no build do frontend${NC}"
        exit 1
    fi
    
    # Copiar build para diretório de produção
    echo -e "${YELLOW}   Copiando build do frontend...${NC}"
    if [ -d "dist" ]; then
        cp -r dist/* "$BUILD_DIR/frontend/"
        
        # Criar arquivo de configuração do servidor web
        cat > "$BUILD_DIR/frontend/.htaccess" << 'EOF'
# Configuração para Apache
RewriteEngine On
RewriteRule ^(?!.*\.).*$ /index.html [L]

# Cache para assets estáticos
<FilesMatch "\.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$">
    ExpiresActive On
    ExpiresDefault "access plus 1 year"
</FilesMatch>

# Compressão
<IfModule mod_deflate.c>
    AddOutputFilterByType DEFLATE text/plain
    AddOutputFilterByType DEFLATE text/html
    AddOutputFilterByType DEFLATE text/xml
    AddOutputFilterByType DEFLATE text/css
    AddOutputFilterByType DEFLATE application/xml
    AddOutputFilterByType DEFLATE application/xhtml+xml
    AddOutputFilterByType DEFLATE application/rss+xml
    AddOutputFilterByType DEFLATE application/javascript
    AddOutputFilterByType DEFLATE application/x-javascript
</IfModule>
EOF
        
        # Criar configuração para Nginx
        cat > "$BUILD_DIR/frontend/nginx.conf" << 'EOF'
server {
    listen 80;
    server_name localhost;
    root /path/to/frontend;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Handle client-side routing
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy API requests to backend
    location /api/ {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Proxy file requests to backend
    location /files/ {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
        
        echo -e "${GREEN}✅ Build do frontend concluído${NC}"
    else
        echo -e "${RED}❌ Diretório 'dist' não encontrado após build${NC}"
        exit 1
    fi
}

# Função para criar scripts de produção
create_production_scripts() {
    echo -e "${BLUE}📝 Criando scripts de produção...${NC}"
    
    # Script para servir frontend com servidor simples
    cat > "$BUILD_DIR/serve-frontend.sh" << 'EOF'
#!/bin/bash
# Script para servir o frontend em produção usando servidor HTTP simples

PORT=${1:-3000}
cd "$(dirname "$0")/frontend"

echo "🌐 Servindo frontend na porta $PORT"
echo "   URL: http://localhost:$PORT"
echo "   Pressione Ctrl+C para parar"

# Tentar usar diferentes servidores HTTP
if command -v python3 &> /dev/null; then
    python3 -m http.server $PORT
elif command -v python &> /dev/null; then
    python -m SimpleHTTPServer $PORT
elif command -v node &> /dev/null && npm list -g serve &> /dev/null; then
    npx serve -p $PORT
else
    echo "❌ Nenhum servidor HTTP encontrado"
    echo "   Instale Python ou Node.js com 'serve'"
    exit 1
fi
EOF
    chmod +x "$BUILD_DIR/serve-frontend.sh"
    
    # Script de inicialização completa
    cat > "$BUILD_DIR/start-production.sh" << 'EOF'
#!/bin/bash
# Script para iniciar toda a aplicação em produção

echo "🚀 Iniciando Image2Video em Produção"
echo "===================================="

# Iniciar backend em background
echo "🐍 Iniciando backend..."
cd backend
nohup ./start-production.sh > ../backend-prod.log 2>&1 &
BACKEND_PID=$!
cd ..

# Aguardar backend inicializar
sleep 3

# Verificar se backend está rodando
if ps -p $BACKEND_PID > /dev/null; then
    echo "✅ Backend iniciado (PID: $BACKEND_PID)"
else
    echo "❌ Falha ao iniciar backend"
    exit 1
fi

# Iniciar frontend
echo "⚛️  Iniciando frontend..."
./serve-frontend.sh 3000 &
FRONTEND_PID=$!

echo ""
echo "🎉 Aplicação iniciada em produção!"
echo "================================="
echo "Frontend: http://localhost:3000"
echo "Backend:  http://localhost:8080"
echo ""
echo "PIDs: Backend=$BACKEND_PID, Frontend=$FRONTEND_PID"
echo "Logs: backend-prod.log"
EOF
    chmod +x "$BUILD_DIR/start-production.sh"
    
    # README para produção
    cat > "$BUILD_DIR/README-PRODUCTION.md" << 'EOF'
# Image2Video - Build de Produção

Este diretório contém o build de produção do Image2Video.

## 🚀 Como usar

### Inicialização rápida:
```bash
./start-production.sh
```

### Inicialização manual:

1. **Backend:**
```bash
cd backend
./start-production.sh
```

2. **Frontend (em outro terminal):**
```bash
./serve-frontend.sh 3000
```

## 🌐 URLs

- Frontend: http://localhost:3000
- Backend: http://localhost:8080
- API Docs: http://localhost:8080/docs

## 📁 Estrutura

```
build/
├── backend/              # Backend Python
│   ├── main.py          # Aplicação FastAPI
│   ├── venv/            # Ambiente virtual
│   └── start-production.sh
├── frontend/            # Frontend buildado
│   ├── index.html       # Aplicação React
│   ├── assets/          # CSS, JS, imagens
│   ├── .htaccess        # Config Apache
│   └── nginx.conf       # Config Nginx
├── start-production.sh  # Iniciar tudo
└── serve-frontend.sh    # Servir apenas frontend
```

## 🔧 Configuração de Servidor Web

### Apache
Copie o arquivo `.htaccess` para o diretório web.

### Nginx
Use a configuração em `nginx.conf` como base.

## 📝 Logs

- Backend: `backend-prod.log`
- Frontend: logs do servidor HTTP usado

## 🛠️ Dependências

- Python 3.8+ (para backend)
- Python HTTP server ou Node.js (para frontend)
EOF
    
    echo -e "${GREEN}✅ Scripts de produção criados${NC}"
}

# Função para mostrar resumo do build
show_build_summary() {
    echo ""
    echo "=================================================="
    echo -e "${GREEN}🎉 Build de produção concluído!${NC}"
    echo "=================================================="
    echo ""
    echo -e "${BLUE}📁 Localização do build:${NC}"
    echo -e "   ${GREEN}$BUILD_DIR${NC}"
    echo ""
    echo -e "${BLUE}📋 Estrutura criada:${NC}"
    echo -e "   ${YELLOW}backend/${NC}          - Backend Python com venv"
    echo -e "   ${YELLOW}frontend/${NC}         - Frontend buildado (HTML/CSS/JS)"
    echo -e "   ${YELLOW}start-production.sh${NC} - Script para iniciar tudo"
    echo -e "   ${YELLOW}serve-frontend.sh${NC}   - Script para servir frontend"
    echo ""
    echo -e "${BLUE}🚀 Para iniciar em produção:${NC}"
    echo -e "   ${GREEN}cd $BUILD_DIR${NC}"
    echo -e "   ${GREEN}./start-production.sh${NC}"
    echo ""
    echo -e "${BLUE}📊 Tamanho do build:${NC}"
    BUILD_SIZE=$(du -sh "$BUILD_DIR" | cut -f1)
    echo -e "   ${YELLOW}$BUILD_SIZE${NC}"
    echo ""
    echo -e "${BLUE}📝 Próximos passos:${NC}"
    echo -e "   1. Testar o build: ${GREEN}cd $BUILD_DIR && ./start-production.sh${NC}"
    echo -e "   2. Configurar servidor web (Apache/Nginx)"
    echo -e "   3. Configurar variáveis de ambiente de produção"
    echo -e "   4. Configurar SSL/HTTPS"
    echo ""
}

# Executar funções principais
main() {
    check_directories
    create_build_directory
    build_backend
    build_frontend
    create_production_scripts
    show_build_summary
}

# Verificar se o script está sendo executado diretamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
