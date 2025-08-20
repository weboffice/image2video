#!/bin/bash

# Script para verificar o status do ambiente de produção do Image2Video

echo "📊 Status do ambiente de PRODUÇÃO Image2Video"
echo "=============================================="

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Portas de produção
BACKEND_PORT=8080
FRONTEND_PORT=3000

# Diretórios (relativos)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$SCRIPT_DIR/../../build"

# Função para verificar se uma porta está em uso
check_port() {
    local port=$1
    local service_name=$2
    
    PID=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$PID" ]; then
        PROCESS_NAME=$(ps -p $PID -o comm= 2>/dev/null)
        PROCESS_CMD=$(ps -p $PID -o args= 2>/dev/null | cut -c1-50)
        echo -e "${GREEN}✅ $service_name está rodando${NC}"
        echo -e "   Porta: $port | PID: $PID | Processo: $PROCESS_NAME"
        echo -e "   Comando: $PROCESS_CMD"
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
    
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "$url" 2>/dev/null)
    if [ "$HTTP_STATUS" = "200" ] || [ "$HTTP_STATUS" = "404" ] || [ "$HTTP_STATUS" = "302" ]; then
        echo -e "${GREEN}✅ $service_name respondendo HTTP (Status: $HTTP_STATUS)${NC}"
        echo -e "   URL: $url"
        return 0
    else
        echo -e "${RED}❌ $service_name não responde HTTP${NC}"
        echo -e "   URL: $url (Status: ${HTTP_STATUS:-timeout})"
        return 1
    fi
}

# Função para verificar build de produção
check_production_build() {
    echo -e "${BLUE}🏗️  Status do build de produção:${NC}"
    
    if [ -d "$BUILD_DIR" ]; then
        BUILD_SIZE=$(du -sh "$BUILD_DIR" | cut -f1)
        BUILD_DATE=$(stat -c %y "$BUILD_DIR" | cut -d' ' -f1,2 | cut -d'.' -f1)
        echo -e "${GREEN}   ✅ Build existe: $BUILD_SIZE (criado em $BUILD_DATE)${NC}"
        
        # Verificar componentes do build
        if [ -d "$BUILD_DIR/backend" ]; then
            echo -e "${GREEN}   ✅ Backend build presente${NC}"
            if [ -f "$BUILD_DIR/backend/start-production.sh" ]; then
                echo -e "${GREEN}   ✅ Script de produção do backend presente${NC}"
            else
                echo -e "${RED}   ❌ Script de produção do backend ausente${NC}"
            fi
        else
            echo -e "${RED}   ❌ Backend build ausente${NC}"
        fi
        
        if [ -d "$BUILD_DIR/frontend" ] && [ -f "$BUILD_DIR/frontend/index.html" ]; then
            FRONTEND_SIZE=$(du -sh "$BUILD_DIR/frontend" | cut -f1)
            echo -e "${GREEN}   ✅ Frontend build presente ($FRONTEND_SIZE)${NC}"
        else
            echo -e "${RED}   ❌ Frontend build ausente${NC}"
        fi
        
        if [ -f "$BUILD_DIR/serve-frontend.sh" ]; then
            echo -e "${GREEN}   ✅ Script do servidor frontend presente${NC}"
        else
            echo -e "${RED}   ❌ Script do servidor frontend ausente${NC}"
        fi
        
    else
        echo -e "${RED}   ❌ Build de produção não encontrado${NC}"
        echo -e "${YELLOW}   Execute: /home/image2video/build-prod.sh${NC}"
    fi
}

# Função para verificar logs de produção
check_production_logs() {
    echo -e "${BLUE}📝 Status dos logs de produção:${NC}"
    
    # Log atual do backend
    if [ -f "$SCRIPT_DIR/backend-prod.log" ]; then
        BACKEND_SIZE=$(du -h "$SCRIPT_DIR/backend-prod.log" | cut -f1)
        BACKEND_LINES=$(wc -l < "$SCRIPT_DIR/backend-prod.log")
        BACKEND_MODIFIED=$(stat -c %y "$SCRIPT_DIR/backend-prod.log" | cut -d'.' -f1)
        echo -e "${GREEN}   Backend log atual: ${NC}$BACKEND_SIZE ($BACKEND_LINES linhas)"
        echo -e "${GREEN}   Última modificação: ${NC}$BACKEND_MODIFIED"
        
        # Verificar erros recentes
        RECENT_ERRORS=$(tail -100 "$SCRIPT_DIR/backend-prod.log" | grep -i "error\|exception\|failed" | wc -l)
        if [ $RECENT_ERRORS -gt 0 ]; then
            echo -e "${RED}   ⚠️  $RECENT_ERRORS erros nas últimas 100 linhas${NC}"
        else
            echo -e "${GREEN}   ✅ Nenhum erro recente encontrado${NC}"
        fi
    else
        echo -e "${YELLOW}   Backend log atual: não encontrado${NC}"
    fi
    
    # Log atual do frontend
    if [ -f "$SCRIPT_DIR/frontend-prod.log" ]; then
        FRONTEND_SIZE=$(du -h "$SCRIPT_DIR/frontend-prod.log" | cut -f1)
        FRONTEND_LINES=$(wc -l < "$SCRIPT_DIR/frontend-prod.log")
        FRONTEND_MODIFIED=$(stat -c %y "$SCRIPT_DIR/frontend-prod.log" | cut -d'.' -f1)
        echo -e "${GREEN}   Frontend log atual: ${NC}$FRONTEND_SIZE ($FRONTEND_LINES linhas)"
        echo -e "${GREEN}   Última modificação: ${NC}$FRONTEND_MODIFIED"
    else
        echo -e "${YELLOW}   Frontend log atual: não encontrado${NC}"
    fi
    
    # Logs arquivados
    if [ -d "$SCRIPT_DIR/logs/archive" ]; then
        ARCHIVED_BACKEND=$(ls "$SCRIPT_DIR/logs/archive"/backend-prod_*.log 2>/dev/null | wc -l)
        ARCHIVED_FRONTEND=$(ls "$SCRIPT_DIR/logs/archive"/frontend-prod_*.log 2>/dev/null | wc -l)
        echo -e "${BLUE}   Logs arquivados: ${NC}$ARCHIVED_BACKEND backend, $ARCHIVED_FRONTEND frontend"
    fi
}

# Função para verificar recursos do sistema
check_system_resources() {
    echo -e "${BLUE}💻 Recursos do sistema (produção):${NC}"
    
    # CPU
    CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    echo -e "   CPU: ${CPU_USAGE}% em uso"
    
    # Memória
    MEMORY_INFO=$(free -h | grep "Mem:")
    MEMORY_USED=$(echo $MEMORY_INFO | awk '{print $3}')
    MEMORY_TOTAL=$(echo $MEMORY_INFO | awk '{print $2}')
    MEMORY_PERCENT=$(free | grep "Mem:" | awk '{printf "%.1f", $3/$2 * 100.0}')
    echo -e "   Memória: $MEMORY_USED de $MEMORY_TOTAL (${MEMORY_PERCENT}%)"
    
    # Espaço em disco
    DISK_USAGE=$(df -h /home | tail -1 | awk '{print $5}')
    DISK_AVAILABLE=$(df -h /home | tail -1 | awk '{print $4}')
    echo -e "   Disco /home: $DISK_USAGE usado ($DISK_AVAILABLE disponível)"
    
    # Load average
    LOAD_AVG=$(uptime | awk -F'load average:' '{print $2}')
    echo -e "   Load average:$LOAD_AVG"
}

# Função para verificar conectividade de rede
check_network_connectivity() {
    echo -e "${BLUE}🌐 Conectividade de rede:${NC}"
    
    # Verificar se consegue resolver DNS
    if nslookup google.com > /dev/null 2>&1; then
        echo -e "${GREEN}   ✅ DNS funcionando${NC}"
    else
        echo -e "${RED}   ❌ Problemas com DNS${NC}"
    fi
    
    # Verificar conectividade externa
    if curl -s --connect-timeout 5 https://google.com > /dev/null 2>&1; then
        echo -e "${GREEN}   ✅ Conectividade externa OK${NC}"
    else
        echo -e "${RED}   ❌ Problemas de conectividade externa${NC}"
    fi
    
    # Verificar portas locais
    OPEN_PORTS=$(netstat -tuln 2>/dev/null | grep -E ":($BACKEND_PORT|$FRONTEND_PORT)" | wc -l)
    echo -e "   Portas de produção abertas: $OPEN_PORTS/2"
}

# Função para verificar performance
check_performance() {
    echo -e "${BLUE}⚡ Performance dos serviços:${NC}"
    
    # Testar tempo de resposta do backend
    if curl -s --connect-timeout 5 "http://localhost:$BACKEND_PORT" > /dev/null 2>&1; then
        BACKEND_TIME=$(curl -s -w "%{time_total}" -o /dev/null "http://localhost:$BACKEND_PORT/health" 2>/dev/null || echo "N/A")
        if [ "$BACKEND_TIME" != "N/A" ]; then
            echo -e "   Backend response time: ${BACKEND_TIME}s"
        else
            echo -e "   Backend response time: N/A"
        fi
    fi
    
    # Testar tempo de resposta do frontend
    if curl -s --connect-timeout 5 "http://localhost:$FRONTEND_PORT" > /dev/null 2>&1; then
        FRONTEND_TIME=$(curl -s -w "%{time_total}" -o /dev/null "http://localhost:$FRONTEND_PORT" 2>/dev/null || echo "N/A")
        if [ "$FRONTEND_TIME" != "N/A" ]; then
            echo -e "   Frontend response time: ${FRONTEND_TIME}s"
        else
            echo -e "   Frontend response time: N/A"
        fi
    fi
}

# Função principal
main() {
    echo -e "${BLUE}🔍 Verificando serviços de produção...${NC}"
    echo ""
    
    # Verificar backend
    echo -e "${BLUE}🐍 Backend de Produção (FastAPI):${NC}"
    BACKEND_RUNNING=false
    if check_port $BACKEND_PORT "Backend de Produção"; then
        BACKEND_RUNNING=true
        check_http "http://localhost:$BACKEND_PORT" "Backend API"
    fi
    echo ""
    
    # Verificar frontend
    echo -e "${BLUE}⚛️  Frontend de Produção (HTTP Server):${NC}"
    FRONTEND_RUNNING=false
    if check_port $FRONTEND_PORT "Frontend de Produção"; then
        FRONTEND_RUNNING=true
        check_http "http://localhost:$FRONTEND_PORT" "Frontend"
    fi
    echo ""
    
    # Verificar build
    check_production_build
    echo ""
    
    # Verificar logs
    check_production_logs
    echo ""
    
    # Verificar recursos do sistema
    check_system_resources
    echo ""
    
    # Verificar conectividade
    check_network_connectivity
    echo ""
    
    # Verificar performance
    check_performance
    echo ""
    
    # Status geral
    echo "=============================================="
    if [ "$BACKEND_RUNNING" = true ] && [ "$FRONTEND_RUNNING" = true ]; then
        echo -e "${GREEN}🎉 Ambiente de PRODUÇÃO está funcionando!${NC}"
        echo ""
        echo -e "${BLUE}🌐 URLs de produção:${NC}"
        echo -e "   Frontend: ${GREEN}http://localhost:$FRONTEND_PORT${NC}"
        echo -e "   Backend API: ${GREEN}http://localhost:$BACKEND_PORT${NC}"
        echo -e "   API Docs: ${GREEN}http://localhost:$BACKEND_PORT/docs${NC}"
    elif [ "$BACKEND_RUNNING" = true ] || [ "$FRONTEND_RUNNING" = true ]; then
        echo -e "${YELLOW}⚠️  Ambiente de produção parcialmente funcionando${NC}"
        if [ "$BACKEND_RUNNING" = false ]; then
            echo -e "${RED}   Backend de produção não está rodando${NC}"
        fi
        if [ "$FRONTEND_RUNNING" = false ]; then
            echo -e "${RED}   Frontend de produção não está rodando${NC}"
        fi
    else
        echo -e "${RED}❌ Ambiente de PRODUÇÃO não está rodando${NC}"
        echo ""
        if [ ! -d "$BUILD_DIR" ]; then
            echo -e "${BLUE}🏗️  Para fazer build:${NC}"
            echo -e "   ${GREEN}$SCRIPT_DIR/build-prod.sh${NC}"
        fi
        echo -e "${BLUE}🚀 Para iniciar produção:${NC}"
        echo -e "   ${GREEN}$SCRIPT_DIR/start-prod.sh${NC}"
    fi
    
    echo ""
    echo -e "${BLUE}🛠️  Comandos úteis de produção:${NC}"
    echo -e "   Build: ${GREEN}$SCRIPT_DIR/build-prod.sh${NC}"
    echo -e "   Iniciar: ${GREEN}$SCRIPT_DIR/start-prod.sh${NC}"
    echo -e "   Parar: ${YELLOW}$SCRIPT_DIR/stop-prod.sh${NC}"
    echo -e "   Status: ${BLUE}$SCRIPT_DIR/status-prod.sh${NC}"
    echo ""
    echo -e "${BLUE}📝 Logs de produção:${NC}"
    echo -e "   Backend: ${YELLOW}tail -f $SCRIPT_DIR/backend-prod.log${NC}"
    echo -e "   Frontend: ${YELLOW}tail -f $SCRIPT_DIR/frontend-prod.log${NC}"
    echo ""
}

# Verificar se o script está sendo executado diretamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
