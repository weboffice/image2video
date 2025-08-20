#!/bin/bash

# Script para iniciar o ambiente de produção do Image2Video
# Para processos existentes e inicia backend e frontend em modo produção

echo "🚀 Iniciando ambiente de PRODUÇÃO Image2Video"
echo "=============================================="

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Diretórios do projeto (relativos)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$SCRIPT_DIR/../../build"
BACKEND_DIR="$BUILD_DIR/backend"
FRONTEND_DIR="$BUILD_DIR/frontend"

# Portas de produção
BACKEND_PORT=8080
FRONTEND_PORT=3000

# Função para parar processos existentes
stop_existing_processes() {
    echo -e "${YELLOW}🛑 Parando processos existentes...${NC}"
    
    # Parar processos na porta do backend
    BACKEND_PID=$(lsof -ti:$BACKEND_PORT)
    if [ ! -z "$BACKEND_PID" ]; then
        echo -e "${RED}   Parando backend (PID: $BACKEND_PID)${NC}"
        kill -9 $BACKEND_PID 2>/dev/null
        sleep 2
    fi
    
    # Parar processos na porta do frontend
    FRONTEND_PID=$(lsof -ti:$FRONTEND_PORT)
    if [ ! -z "$FRONTEND_PID" ]; then
        echo -e "${RED}   Parando frontend (PID: $FRONTEND_PID)${NC}"
        kill -9 $FRONTEND_PID 2>/dev/null
        sleep 2
    fi
    
    # Parar processos relacionados ao projeto
    pkill -f "main.py" 2>/dev/null
    pkill -f "uvicorn" 2>/dev/null
    pkill -f "http.server.*$FRONTEND_PORT" 2>/dev/null
    pkill -f "serve.*$FRONTEND_PORT" 2>/dev/null
    
    echo -e "${GREEN}✅ Processos existentes parados${NC}"
}

# Função para verificar se o build existe
check_build() {
    echo -e "${BLUE}📁 Verificando build de produção...${NC}"
    
    if [ ! -d "$BUILD_DIR" ]; then
        echo -e "${RED}❌ Build de produção não encontrado: $BUILD_DIR${NC}"
        echo -e "${YELLOW}   Execute primeiro: /home/image2video/build-prod.sh${NC}"
        exit 1
    fi
    
    if [ ! -d "$BACKEND_DIR" ]; then
        echo -e "${RED}❌ Backend de produção não encontrado: $BACKEND_DIR${NC}"
        echo -e "${YELLOW}   Execute primeiro: /home/image2video/build-prod.sh${NC}"
        exit 1
    fi
    
    if [ ! -d "$FRONTEND_DIR" ]; then
        echo -e "${RED}❌ Frontend de produção não encontrado: $FRONTEND_DIR${NC}"
        echo -e "${YELLOW}   Execute primeiro: /home/image2video/build-prod.sh${NC}"
        exit 1
    fi
    
    if [ ! -f "$FRONTEND_DIR/index.html" ]; then
        echo -e "${RED}❌ Build do frontend não encontrado${NC}"
        echo -e "${YELLOW}   Execute primeiro: /home/image2video/build-prod.sh${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Build de produção verificado${NC}"
}

# Função para iniciar o backend
start_backend() {
    echo -e "${BLUE}🐍 Iniciando backend de produção...${NC}"
    
    cd "$BACKEND_DIR"
    
    # Verificar se o ambiente virtual existe
    if [ ! -d "venv" ]; then
        echo -e "${RED}❌ Ambiente virtual não encontrado${NC}"
        echo -e "${YELLOW}   Execute primeiro: /home/image2video/build-prod.sh${NC}"
        exit 1
    fi
    
    # Verificar se o script de inicialização existe
    if [ ! -f "start-production.sh" ]; then
        echo -e "${RED}❌ Script de produção não encontrado${NC}"
        echo -e "${YELLOW}   Execute primeiro: /home/image2video/build-prod.sh${NC}"
        exit 1
    fi
    
    # Iniciar o backend em background
    echo -e "${GREEN}   Iniciando servidor FastAPI na porta $BACKEND_PORT...${NC}"
    nohup ./start-production.sh > "$SCRIPT_DIR/backend-prod.log" 2>&1 &
    BACKEND_PID=$!
    
    # Aguardar um pouco para o backend inicializar
    sleep 5
    
    # Verificar se o backend está rodando
    if ps -p $BACKEND_PID > /dev/null; then
        # Verificar se está respondendo HTTP
        if curl -s --connect-timeout 5 "http://localhost:$BACKEND_PORT" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Backend iniciado com sucesso (PID: $BACKEND_PID)${NC}"
            echo -e "${GREEN}   URL: http://localhost:$BACKEND_PORT${NC}"
        else
            echo -e "${YELLOW}⚠️  Backend iniciado mas não responde HTTP ainda${NC}"
            echo -e "${YELLOW}   Aguarde alguns segundos e verifique o log${NC}"
        fi
    else
        echo -e "${RED}❌ Falha ao iniciar o backend${NC}"
        echo -e "${YELLOW}   Verifique o log: tail -f $SCRIPT_DIR/backend-prod.log${NC}"
        exit 1
    fi
}

# Função para iniciar o frontend
start_frontend() {
    echo -e "${BLUE}⚛️  Iniciando frontend de produção...${NC}"
    
    cd "$BUILD_DIR"
    
    # Verificar se o script de frontend existe
    if [ ! -f "serve-frontend.sh" ]; then
        echo -e "${RED}❌ Script do frontend não encontrado${NC}"
        echo -e "${YELLOW}   Execute primeiro: /home/image2video/build-prod.sh${NC}"
        exit 1
    fi
    
    # Iniciar o frontend em background
    echo -e "${GREEN}   Iniciando servidor HTTP na porta $FRONTEND_PORT...${NC}"
    nohup ./serve-frontend.sh $FRONTEND_PORT > "$SCRIPT_DIR/frontend-prod.log" 2>&1 &
    FRONTEND_PID=$!
    
    # Aguardar um pouco para o frontend inicializar
    sleep 3
    
    # Verificar se o frontend está rodando
    if ps -p $FRONTEND_PID > /dev/null; then
        # Verificar se está respondendo HTTP
        if curl -s --connect-timeout 5 "http://localhost:$FRONTEND_PORT" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Frontend iniciado com sucesso (PID: $FRONTEND_PID)${NC}"
            echo -e "${GREEN}   URL: http://localhost:$FRONTEND_PORT${NC}"
        else
            echo -e "${YELLOW}⚠️  Frontend iniciado mas não responde HTTP ainda${NC}"
            echo -e "${YELLOW}   Aguarde alguns segundos e verifique o log${NC}"
        fi
    else
        echo -e "${RED}❌ Falha ao iniciar o frontend${NC}"
        echo -e "${YELLOW}   Verifique o log: tail -f $SCRIPT_DIR/frontend-prod.log${NC}"
        exit 1
    fi
}

# Função para verificar dependências de produção
check_production_dependencies() {
    echo -e "${BLUE}🔍 Verificando dependências de produção...${NC}"
    
    # Verificar Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python3 não encontrado${NC}"
        exit 1
    fi
    
    # Verificar se tem servidor HTTP disponível
    HAS_HTTP_SERVER=false
    
    if command -v python3 &> /dev/null; then
        HAS_HTTP_SERVER=true
        HTTP_SERVER="Python3 HTTP server"
    elif command -v python &> /dev/null; then
        HAS_HTTP_SERVER=true
        HTTP_SERVER="Python HTTP server"
    elif command -v node &> /dev/null; then
        HAS_HTTP_SERVER=true
        HTTP_SERVER="Node.js"
    fi
    
    if [ "$HAS_HTTP_SERVER" = false ]; then
        echo -e "${RED}❌ Nenhum servidor HTTP encontrado${NC}"
        echo -e "${YELLOW}   Instale Python ou Node.js${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Dependências verificadas${NC}"
    echo -e "${GREEN}   Servidor HTTP: $HTTP_SERVER${NC}"
}

# Função para mostrar status final
show_status() {
    echo ""
    echo "=================================================="
    echo -e "${GREEN}🎉 Ambiente de PRODUÇÃO iniciado!${NC}"
    echo "=================================================="
    echo ""
    echo -e "${BLUE}🌐 URLs disponíveis:${NC}"
    echo -e "   Frontend: ${GREEN}http://localhost:$FRONTEND_PORT${NC}"
    echo -e "   Backend API: ${GREEN}http://localhost:$BACKEND_PORT${NC}"
    echo -e "   API Docs: ${GREEN}http://localhost:$BACKEND_PORT/docs${NC}"
    echo ""
    echo -e "${BLUE}📝 Logs de produção:${NC}"
    echo -e "   Backend: ${YELLOW}tail -f $SCRIPT_DIR/backend-prod.log${NC}"
    echo -e "   Frontend: ${YELLOW}tail -f $SCRIPT_DIR/frontend-prod.log${NC}"
    echo ""
    echo -e "${BLUE}🛑 Para parar os serviços:${NC}"
    echo -e "   ${YELLOW}$SCRIPT_DIR/stop-prod.sh${NC}"
    echo ""
    echo -e "${BLUE}📊 Para verificar status:${NC}"
    echo -e "   ${YELLOW}$SCRIPT_DIR/status-prod.sh${NC}"
    echo ""
    echo -e "${BLUE}🔄 Para fazer novo build:${NC}"
    echo -e "   ${YELLOW}$SCRIPT_DIR/build-prod.sh${NC}"
    echo ""
    echo -e "${BLUE}⚠️  Lembrete de Produção:${NC}"
    echo -e "   • Configure SSL/HTTPS para produção real"
    echo -e "   • Configure variáveis de ambiente adequadas"
    echo -e "   • Use servidor web profissional (Nginx/Apache)"
    echo -e "   • Configure backup e monitoramento"
    echo ""
}

# Executar funções principais
main() {
    stop_existing_processes
    check_build
    check_production_dependencies
    start_backend
    start_frontend
    show_status
}

# Verificar se o script está sendo executado diretamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
