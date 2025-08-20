#!/bin/bash

# Script para parar o ambiente de desenvolvimento do Image2Video

echo "🛑 Parando ambiente de desenvolvimento Image2Video"
echo "================================================="

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para parar processos por porta
stop_by_port() {
    local port=$1
    local service_name=$2
    
    PID=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$PID" ]; then
        echo -e "${YELLOW}   Parando $service_name (porta $port, PID: $PID)${NC}"
        kill -15 $PID 2>/dev/null
        sleep 2
        
        # Se ainda estiver rodando, forçar parada
        if ps -p $PID > /dev/null 2>&1; then
            echo -e "${RED}   Forçando parada do $service_name${NC}"
            kill -9 $PID 2>/dev/null
        fi
        
        echo -e "${GREEN}✅ $service_name parado${NC}"
    else
        echo -e "${BLUE}   $service_name não estava rodando na porta $port${NC}"
    fi
}

# Função principal para parar todos os serviços
stop_services() {
    echo -e "${BLUE}🔍 Procurando processos ativos...${NC}"
    
    # Parar backend (porta 8080)
    stop_by_port 8080 "Backend (FastAPI)"
    
    # Parar frontend (porta 5173)
    stop_by_port 5173 "Frontend (Vite)"
    
    # Parar processos específicos por nome
    echo -e "${YELLOW}🧹 Limpando processos relacionados...${NC}"
    
    # Parar processos do Vite
    VITE_PIDS=$(pgrep -f "vite" 2>/dev/null)
    if [ ! -z "$VITE_PIDS" ]; then
        echo -e "${YELLOW}   Parando processos Vite${NC}"
        pkill -15 -f "vite" 2>/dev/null
        sleep 2
        pkill -9 -f "vite" 2>/dev/null
    fi
    
    # Parar processos do FastAPI/uvicorn
    FASTAPI_PIDS=$(pgrep -f "main.py\|uvicorn" 2>/dev/null)
    if [ ! -z "$FASTAPI_PIDS" ]; then
        echo -e "${YELLOW}   Parando processos FastAPI${NC}"
        pkill -15 -f "main.py" 2>/dev/null
        pkill -15 -f "uvicorn" 2>/dev/null
        sleep 2
        pkill -9 -f "main.py" 2>/dev/null
        pkill -9 -f "uvicorn" 2>/dev/null
    fi
    
    # Parar processos Node.js relacionados ao projeto
    NODE_PIDS=$(pgrep -f "node.*vite\|npm.*dev" 2>/dev/null)
    if [ ! -z "$NODE_PIDS" ]; then
        echo -e "${YELLOW}   Parando processos Node.js relacionados${NC}"
        pkill -15 -f "node.*vite" 2>/dev/null
        pkill -15 -f "npm.*dev" 2>/dev/null
        sleep 2
        pkill -9 -f "node.*vite" 2>/dev/null
        pkill -9 -f "npm.*dev" 2>/dev/null
    fi
}

# Função para limpar logs
clean_logs() {
    echo -e "${BLUE}🧹 Limpando logs...${NC}"
    
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    if [ -f "$SCRIPT_DIR/backend.log" ]; then
        rm -f "$SCRIPT_DIR/backend.log"
        echo -e "${GREEN}   Log do backend removido${NC}"
    fi
    
    if [ -f "$SCRIPT_DIR/frontend.log" ]; then
        rm -f "$SCRIPT_DIR/frontend.log"
        echo -e "${GREEN}   Log do frontend removido${NC}"
    fi
}

# Função para verificar se ainda há processos rodando
check_remaining_processes() {
    echo -e "${BLUE}🔍 Verificando processos restantes...${NC}"
    
    # Verificar porta 8080
    if lsof -ti:8080 > /dev/null 2>&1; then
        echo -e "${RED}⚠️  Ainda há processos na porta 8080${NC}"
    fi
    
    # Verificar porta 5173
    if lsof -ti:5173 > /dev/null 2>&1; then
        echo -e "${RED}⚠️  Ainda há processos na porta 5173${NC}"
    fi
    
    # Verificar processos relacionados
    REMAINING=$(pgrep -f "vite\|main.py\|uvicorn" 2>/dev/null)
    if [ ! -z "$REMAINING" ]; then
        echo -e "${RED}⚠️  Processos relacionados ainda ativos: $REMAINING${NC}"
        echo -e "${YELLOW}   Use 'kill -9 $REMAINING' se necessário${NC}"
    else
        echo -e "${GREEN}✅ Nenhum processo relacionado encontrado${NC}"
    fi
}

# Função para mostrar status final
show_final_status() {
    echo ""
    echo "================================================="
    echo -e "${GREEN}✅ Ambiente de desenvolvimento parado!${NC}"
    echo "================================================="
    echo ""
    echo -e "${BLUE}🚀 Para iniciar novamente:${NC}"
    echo -e "   ${GREEN}/home/image2video/start-dev.sh${NC}"
    echo ""
    echo -e "${BLUE}📊 Para verificar portas:${NC}"
    echo -e "   ${YELLOW}lsof -i:8080,5173${NC}"
    echo ""
}

# Executar funções principais
main() {
    stop_services
    clean_logs
    check_remaining_processes
    show_final_status
}

# Verificar se o script está sendo executado diretamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
