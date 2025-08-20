#!/bin/bash

# Script para verificar o status do ambiente de desenvolvimento do Image2Video

echo "📊 Status do ambiente de desenvolvimento Image2Video"
echo "===================================================="

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para verificar se uma porta está em uso
check_port() {
    local port=$1
    local service_name=$2
    
    PID=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$PID" ]; then
        PROCESS_NAME=$(ps -p $PID -o comm= 2>/dev/null)
        echo -e "${GREEN}✅ $service_name está rodando${NC}"
        echo -e "   Porta: $port | PID: $PID | Processo: $PROCESS_NAME"
        return 0
    else
        echo -e "${RED}❌ $service_name não está rodando${NC}"
        echo -e "   Porta: $port está livre"
        return 1
    fi
}

# Função para verificar conectividade HTTP
check_http() {
    local url=$1
    local service_name=$2
    
    if curl -s --connect-timeout 3 "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $service_name respondendo HTTP${NC}"
        echo -e "   URL: $url"
        return 0
    else
        echo -e "${RED}❌ $service_name não responde HTTP${NC}"
        echo -e "   URL: $url"
        return 1
    fi
}

# Função para verificar logs
check_logs() {
    echo -e "${BLUE}📝 Status dos logs:${NC}"
    
    if [ -f "/home/image2video/backend.log" ]; then
        BACKEND_SIZE=$(du -h /home/image2video/backend.log | cut -f1)
        BACKEND_LINES=$(wc -l < /home/image2video/backend.log)
        echo -e "${GREEN}   Backend log: ${NC}$BACKEND_SIZE ($BACKEND_LINES linhas)"
        
        # Mostrar últimas linhas se houver erros
        if grep -q "ERROR\|Exception\|Error" /home/image2video/backend.log; then
            echo -e "${RED}   ⚠️  Erros encontrados no log do backend${NC}"
        fi
    else
        echo -e "${YELLOW}   Backend log: não encontrado${NC}"
    fi
    
    if [ -f "/home/image2video/frontend.log" ]; then
        FRONTEND_SIZE=$(du -h /home/image2video/frontend.log | cut -f1)
        FRONTEND_LINES=$(wc -l < /home/image2video/frontend.log)
        echo -e "${GREEN}   Frontend log: ${NC}$FRONTEND_SIZE ($FRONTEND_LINES linhas)"
        
        # Mostrar últimas linhas se houver erros
        if grep -q "ERROR\|Error\|Failed" /home/image2video/frontend.log; then
            echo -e "${RED}   ⚠️  Erros encontrados no log do frontend${NC}"
        fi
    else
        echo -e "${YELLOW}   Frontend log: não encontrado${NC}"
    fi
}

# Função para verificar recursos do sistema
check_system_resources() {
    echo -e "${BLUE}💻 Recursos do sistema:${NC}"
    
    # CPU
    CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    echo -e "   CPU: ${CPU_USAGE}% em uso"
    
    # Memória
    MEMORY_INFO=$(free -h | grep "Mem:")
    MEMORY_USED=$(echo $MEMORY_INFO | awk '{print $3}')
    MEMORY_TOTAL=$(echo $MEMORY_INFO | awk '{print $2}')
    echo -e "   Memória: $MEMORY_USED de $MEMORY_TOTAL"
    
    # Espaço em disco
    DISK_USAGE=$(df -h /home | tail -1 | awk '{print $5}')
    echo -e "   Disco /home: $DISK_USAGE usado"
}

# Função para verificar dependências
check_dependencies() {
    echo -e "${BLUE}📦 Dependências:${NC}"
    
    # Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version 2>&1)
        echo -e "${GREEN}   ✅ $PYTHON_VERSION${NC}"
    else
        echo -e "${RED}   ❌ Python3 não encontrado${NC}"
    fi
    
    # Node.js
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version 2>&1)
        echo -e "${GREEN}   ✅ Node.js $NODE_VERSION${NC}"
    else
        echo -e "${RED}   ❌ Node.js não encontrado${NC}"
    fi
    
    # npm
    if command -v npm &> /dev/null; then
        NPM_VERSION=$(npm --version 2>&1)
        echo -e "${GREEN}   ✅ npm $NPM_VERSION${NC}"
    else
        echo -e "${RED}   ❌ npm não encontrado${NC}"
    fi
}

# Função principal
main() {
    echo -e "${BLUE}🔍 Verificando serviços...${NC}"
    echo ""
    
    # Verificar backend
    echo -e "${BLUE}🐍 Backend (FastAPI):${NC}"
    BACKEND_RUNNING=false
    if check_port 8080 "Backend"; then
        BACKEND_RUNNING=true
        check_http "http://localhost:8080" "Backend API"
    fi
    echo ""
    
    # Verificar frontend
    echo -e "${BLUE}⚛️  Frontend (Vite):${NC}"
    FRONTEND_RUNNING=false
    if check_port 5173 "Frontend"; then
        FRONTEND_RUNNING=true
        check_http "http://localhost:5173" "Frontend"
    fi
    echo ""
    
    # Verificar logs
    check_logs
    echo ""
    
    # Verificar recursos do sistema
    check_system_resources
    echo ""
    
    # Verificar dependências
    check_dependencies
    echo ""
    
    # Status geral
    echo "===================================================="
    if [ "$BACKEND_RUNNING" = true ] && [ "$FRONTEND_RUNNING" = true ]; then
        echo -e "${GREEN}🎉 Ambiente de desenvolvimento está funcionando!${NC}"
        echo ""
        echo -e "${BLUE}📋 URLs disponíveis:${NC}"
        echo -e "   Frontend: ${GREEN}http://localhost:5173${NC}"
        echo -e "   Backend API: ${GREEN}http://localhost:8080${NC}"
        echo -e "   API Docs: ${GREEN}http://localhost:8080/docs${NC}"
    elif [ "$BACKEND_RUNNING" = true ] || [ "$FRONTEND_RUNNING" = true ]; then
        echo -e "${YELLOW}⚠️  Ambiente parcialmente funcionando${NC}"
        if [ "$BACKEND_RUNNING" = false ]; then
            echo -e "${RED}   Backend não está rodando${NC}"
        fi
        if [ "$FRONTEND_RUNNING" = false ]; then
            echo -e "${RED}   Frontend não está rodando${NC}"
        fi
    else
        echo -e "${RED}❌ Ambiente de desenvolvimento não está rodando${NC}"
        echo ""
        echo -e "${BLUE}🚀 Para iniciar:${NC}"
        echo -e "   ${GREEN}/home/image2video/start-dev.sh${NC}"
    fi
    
    echo ""
    echo -e "${BLUE}🛠️  Comandos úteis:${NC}"
    echo -e "   Iniciar: ${GREEN}/home/image2video/start-dev.sh${NC}"
    echo -e "   Parar: ${YELLOW}/home/image2video/stop-dev.sh${NC}"
    echo -e "   Status: ${BLUE}/home/image2video/status-dev.sh${NC}"
    echo ""
}

# Verificar se o script está sendo executado diretamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
