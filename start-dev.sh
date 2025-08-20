#!/bin/bash

# Script para iniciar o desenvolvimento local do Image2Video
# Para processos existentes e inicia backend e frontend

echo "🚀 Iniciando ambiente de desenvolvimento Image2Video"
echo "=================================================="

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

# Função para parar processos existentes
stop_existing_processes() {
    echo -e "${YELLOW}🛑 Parando processos existentes...${NC}"
    
    # Parar processos na porta 8080 (backend)
    BACKEND_PID=$(lsof -ti:8080)
    if [ ! -z "$BACKEND_PID" ]; then
        echo -e "${RED}   Parando backend (PID: $BACKEND_PID)${NC}"
        kill -9 $BACKEND_PID 2>/dev/null
        sleep 2
    fi
    
    # Parar processos na porta 5173 (frontend)
    FRONTEND_PID=$(lsof -ti:5173)
    if [ ! -z "$FRONTEND_PID" ]; then
        echo -e "${RED}   Parando frontend (PID: $FRONTEND_PID)${NC}"
        kill -9 $FRONTEND_PID 2>/dev/null
        sleep 2
    fi
    
    # Parar processos do Node.js relacionados ao Vite
    pkill -f "vite" 2>/dev/null
    
    # Parar processos Python do FastAPI
    pkill -f "main.py" 2>/dev/null
    pkill -f "uvicorn" 2>/dev/null
    
    echo -e "${GREEN}✅ Processos existentes parados${NC}"
}

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

# Função para iniciar o backend
start_backend() {
    echo -e "${BLUE}🐍 Iniciando backend...${NC}"
    
    cd "$BACKEND_DIR"
    
    # Verificar se o ambiente virtual existe
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}   Criando ambiente virtual...${NC}"
        python3 -m venv venv
    fi
    
    # Ativar ambiente virtual e instalar dependências se necessário
    source venv/bin/activate
    
    # Verificar se requirements.txt existe e instalar dependências
    if [ -f "requirements.txt" ]; then
        echo -e "${YELLOW}   Verificando dependências...${NC}"
        pip install -r requirements.txt > /dev/null 2>&1
    fi
    
    # Iniciar o backend em background
    echo -e "${GREEN}   Iniciando servidor FastAPI na porta 8080...${NC}"
    nohup python main.py > "$SCRIPT_DIR/backend.log" 2>&1 &
    BACKEND_PID=$!
    
    # Aguardar um pouco para o backend inicializar
    sleep 3
    
    # Verificar se o backend está rodando
    if ps -p $BACKEND_PID > /dev/null; then
        echo -e "${GREEN}✅ Backend iniciado com sucesso (PID: $BACKEND_PID)${NC}"
        echo -e "${GREEN}   URL: http://localhost:8080${NC}"
    else
        echo -e "${RED}❌ Falha ao iniciar o backend${NC}"
        echo -e "${YELLOW}   Verifique o log: tail -f $SCRIPT_DIR/backend.log${NC}"
        exit 1
    fi
}

# Função para iniciar o frontend
start_frontend() {
    echo -e "${BLUE}⚛️  Iniciando frontend...${NC}"
    
    cd "$FRONTEND_DIR"
    
    # Verificar se node_modules existe
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}   Instalando dependências do frontend...${NC}"
        npm install
    fi
    
    # Iniciar o frontend em background
    echo -e "${GREEN}   Iniciando servidor Vite na porta 5173...${NC}"
    nohup npm run dev > "$SCRIPT_DIR/frontend.log" 2>&1 &
    FRONTEND_PID=$!
    
    # Aguardar um pouco para o frontend inicializar
    sleep 5
    
    # Verificar se o frontend está rodando
    if ps -p $FRONTEND_PID > /dev/null; then
        echo -e "${GREEN}✅ Frontend iniciado com sucesso (PID: $FRONTEND_PID)${NC}"
        echo -e "${GREEN}   URL: http://localhost:5173${NC}"
    else
        echo -e "${RED}❌ Falha ao iniciar o frontend${NC}"
        echo -e "${YELLOW}   Verifique o log: tail -f $SCRIPT_DIR/frontend.log${NC}"
        exit 1
    fi
}

# Função para mostrar status final
show_status() {
    echo ""
    echo "=================================================="
    echo -e "${GREEN}🎉 Ambiente de desenvolvimento iniciado!${NC}"
    echo "=================================================="
    echo ""
    echo -e "${BLUE}📋 URLs disponíveis:${NC}"
    echo -e "   Frontend: ${GREEN}http://localhost:5173${NC}"
    echo -e "   Backend API: ${GREEN}http://localhost:8080${NC}"
    echo -e "   API Docs: ${GREEN}http://localhost:8080/docs${NC}"
    echo ""
    echo -e "${BLUE}📝 Logs:${NC}"
    echo -e "   Backend: ${YELLOW}tail -f $SCRIPT_DIR/backend.log${NC}"
    echo -e "   Frontend: ${YELLOW}tail -f $SCRIPT_DIR/frontend.log${NC}"
    echo ""
    echo -e "${BLUE}🛑 Para parar os serviços:${NC}"
    echo -e "   ${YELLOW}/home/image2video/stop-dev.sh${NC}"
    echo ""
    echo -e "${BLUE}🔄 Para reiniciar:${NC}"
    echo -e "   ${YELLOW}/home/image2video/start-dev.sh${NC}"
    echo ""
}

# Executar funções principais
main() {
    stop_existing_processes
    check_directories
    start_backend
    start_frontend
    show_status
}

# Verificar se o script está sendo executado diretamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
