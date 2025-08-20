#!/bin/bash

# Script para parar o ambiente de produção do Image2Video

echo "🛑 Parando ambiente de PRODUÇÃO Image2Video"
echo "==========================================="

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Portas de produção
BACKEND_PORT=8080
FRONTEND_PORT=3000

# Função para parar processos por porta
stop_by_port() {
    local port=$1
    local service_name=$2
    
    PID=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$PID" ]; then
        echo -e "${YELLOW}   Parando $service_name (porta $port, PID: $PID)${NC}"
        kill -15 $PID 2>/dev/null
        sleep 3
        
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

# Função principal para parar todos os serviços de produção
stop_production_services() {
    echo -e "${BLUE}🔍 Procurando processos de produção ativos...${NC}"
    
    # Parar backend (porta 8080)
    stop_by_port $BACKEND_PORT "Backend de Produção (FastAPI)"
    
    # Parar frontend (porta 3000)
    stop_by_port $FRONTEND_PORT "Frontend de Produção (HTTP Server)"
    
    # Parar processos específicos por nome
    echo -e "${YELLOW}🧹 Limpando processos relacionados à produção...${NC}"
    
    # Parar processos do FastAPI/uvicorn de produção
    FASTAPI_PIDS=$(pgrep -f "main.py\|uvicorn.*8080" 2>/dev/null)
    if [ ! -z "$FASTAPI_PIDS" ]; then
        echo -e "${YELLOW}   Parando processos FastAPI de produção${NC}"
        pkill -15 -f "main.py" 2>/dev/null
        pkill -15 -f "uvicorn.*8080" 2>/dev/null
        sleep 3
        pkill -9 -f "main.py" 2>/dev/null
        pkill -9 -f "uvicorn.*8080" 2>/dev/null
    fi
    
    # Parar servidores HTTP na porta 3000
    HTTP_PIDS=$(pgrep -f "http.server.*3000\|serve.*3000\|python.*3000" 2>/dev/null)
    if [ ! -z "$HTTP_PIDS" ]; then
        echo -e "${YELLOW}   Parando servidores HTTP de produção${NC}"
        pkill -15 -f "http.server.*3000" 2>/dev/null
        pkill -15 -f "serve.*3000" 2>/dev/null
        pkill -15 -f "python.*3000" 2>/dev/null
        sleep 3
        pkill -9 -f "http.server.*3000" 2>/dev/null
        pkill -9 -f "serve.*3000" 2>/dev/null
        pkill -9 -f "python.*3000" 2>/dev/null
    fi
    
    # Parar processos dos scripts de produção
    SCRIPT_PIDS=$(pgrep -f "start-production.sh\|serve-frontend.sh" 2>/dev/null)
    if [ ! -z "$SCRIPT_PIDS" ]; then
        echo -e "${YELLOW}   Parando scripts de produção${NC}"
        pkill -15 -f "start-production.sh" 2>/dev/null
        pkill -15 -f "serve-frontend.sh" 2>/dev/null
        sleep 2
        pkill -9 -f "start-production.sh" 2>/dev/null
        pkill -9 -f "serve-frontend.sh" 2>/dev/null
    fi
}

# Função para arquivar logs de produção
archive_production_logs() {
    echo -e "${BLUE}📁 Arquivando logs de produção...${NC}"
    
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    LOG_ARCHIVE_DIR="$SCRIPT_DIR/logs/archive"
    
    # Criar diretório de arquivo se não existir
    mkdir -p "$LOG_ARCHIVE_DIR"
    
    # Arquivar log do backend se existir
    if [ -f "$SCRIPT_DIR/backend-prod.log" ]; then
        mv "$SCRIPT_DIR/backend-prod.log" "$LOG_ARCHIVE_DIR/backend-prod_$TIMESTAMP.log"
        echo -e "${GREEN}   Log do backend arquivado: backend-prod_$TIMESTAMP.log${NC}"
    fi
    
    # Arquivar log do frontend se existir
    if [ -f "$SCRIPT_DIR/frontend-prod.log" ]; then
        mv "$SCRIPT_DIR/frontend-prod.log" "$LOG_ARCHIVE_DIR/frontend-prod_$TIMESTAMP.log"
        echo -e "${GREEN}   Log do frontend arquivado: frontend-prod_$TIMESTAMP.log${NC}"
    fi
    
    # Limpar logs antigos (manter apenas os últimos 10)
    if [ -d "$LOG_ARCHIVE_DIR" ]; then
        echo -e "${YELLOW}   Limpando logs antigos...${NC}"
        ls -t "$LOG_ARCHIVE_DIR"/backend-prod_*.log 2>/dev/null | tail -n +11 | xargs rm -f 2>/dev/null || true
        ls -t "$LOG_ARCHIVE_DIR"/frontend-prod_*.log 2>/dev/null | tail -n +11 | xargs rm -f 2>/dev/null || true
    fi
}

# Função para verificar se ainda há processos rodando
check_remaining_processes() {
    echo -e "${BLUE}🔍 Verificando processos restantes...${NC}"
    
    # Verificar porta do backend
    if lsof -ti:$BACKEND_PORT > /dev/null 2>&1; then
        echo -e "${RED}⚠️  Ainda há processos na porta $BACKEND_PORT${NC}"
        REMAINING_BACKEND=$(lsof -ti:$BACKEND_PORT)
        echo -e "${YELLOW}   PIDs: $REMAINING_BACKEND${NC}"
    fi
    
    # Verificar porta do frontend
    if lsof -ti:$FRONTEND_PORT > /dev/null 2>&1; then
        echo -e "${RED}⚠️  Ainda há processos na porta $FRONTEND_PORT${NC}"
        REMAINING_FRONTEND=$(lsof -ti:$FRONTEND_PORT)
        echo -e "${YELLOW}   PIDs: $REMAINING_FRONTEND${NC}"
    fi
    
    # Verificar processos relacionados
    REMAINING=$(pgrep -f "main.py\|uvicorn.*8080\|http.server.*3000\|serve.*3000" 2>/dev/null)
    if [ ! -z "$REMAINING" ]; then
        echo -e "${RED}⚠️  Processos de produção ainda ativos: $REMAINING${NC}"
        echo -e "${YELLOW}   Use 'kill -9 $REMAINING' se necessário${NC}"
    else
        echo -e "${GREEN}✅ Nenhum processo de produção encontrado${NC}"
    fi
}

# Função para mostrar estatísticas de uso
show_usage_stats() {
    echo -e "${BLUE}📊 Estatísticas da sessão de produção:${NC}"
    
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    # Verificar se há logs arquivados
    if [ -d "$SCRIPT_DIR/logs/archive" ]; then
        BACKEND_LOGS=$(ls "$SCRIPT_DIR/logs/archive"/backend-prod_*.log 2>/dev/null | wc -l)
        FRONTEND_LOGS=$(ls "$SCRIPT_DIR/logs/archive"/frontend-prod_*.log 2>/dev/null | wc -l)
        
        echo -e "${GREEN}   Logs arquivados: $BACKEND_LOGS backend, $FRONTEND_LOGS frontend${NC}"
        
        # Mostrar último log se existir
        LAST_BACKEND_LOG=$(ls -t "$SCRIPT_DIR/logs/archive"/backend-prod_*.log 2>/dev/null | head -1)
        if [ ! -z "$LAST_BACKEND_LOG" ]; then
            LOG_SIZE=$(du -h "$LAST_BACKEND_LOG" | cut -f1)
            echo -e "${GREEN}   Último log do backend: $LOG_SIZE${NC}"
        fi
    fi
    
    # Verificar se o build ainda existe
    if [ -d "$SCRIPT_DIR/../../build" ]; then
        BUILD_SIZE=$(du -sh "$SCRIPT_DIR/../../build" 2>/dev/null | cut -f1)
        echo -e "${GREEN}   Build de produção: $BUILD_SIZE${NC}"
    fi
}

# Função para mostrar status final
show_final_status() {
    echo ""
    echo "================================================="
    echo -e "${GREEN}✅ Ambiente de PRODUÇÃO parado!${NC}"
    echo "================================================="
    echo ""
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    echo -e "${BLUE}🚀 Para iniciar novamente:${NC}"
    echo -e "   ${GREEN}$SCRIPT_DIR/start-prod.sh${NC}"
    echo ""
    echo -e "${BLUE}🏗️  Para fazer novo build:${NC}"
    echo -e "   ${GREEN}$SCRIPT_DIR/build-prod.sh${NC}"
    echo ""
    echo -e "${BLUE}📊 Para verificar portas:${NC}"
    echo -e "   ${YELLOW}lsof -i:$BACKEND_PORT,$FRONTEND_PORT${NC}"
    echo ""
    echo -e "${BLUE}📝 Logs arquivados em:${NC}"
    echo -e "   ${YELLOW}$SCRIPT_DIR/logs/archive/${NC}"
    echo ""
    echo -e "${BLUE}🔄 Para ambiente de desenvolvimento:${NC}"
    echo -e "   ${YELLOW}$SCRIPT_DIR/start-dev.sh${NC}"
    echo ""
}

# Executar funções principais
main() {
    stop_production_services
    archive_production_logs
    check_remaining_processes
    show_usage_stats
    show_final_status
}

# Verificar se o script está sendo executado diretamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
