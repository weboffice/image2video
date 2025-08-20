#!/bin/bash

# Script de gerenciamento do ambiente de produção Image2Video
# Menu interativo para build, iniciar, parar e verificar status de produção

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Função para mostrar o cabeçalho
show_header() {
    clear
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                IMAGE2VIDEO PRODUCTION MANAGER               ║"
    echo "║              Gerenciador de Produção                        ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
}

# Função para mostrar o menu principal
show_menu() {
    echo -e "${BLUE}📋 Escolha uma opção:${NC}"
    echo ""
    echo -e "${PURPLE}1)${NC} 🏗️  Fazer build de produção"
    echo -e "${GREEN}2)${NC} 🚀 Iniciar ambiente de produção"
    echo -e "${RED}3)${NC} 🛑 Parar ambiente de produção"
    echo -e "${YELLOW}4)${NC} 📊 Verificar status de produção"
    echo -e "${PURPLE}5)${NC} 📝 Ver logs de produção"
    echo -e "${CYAN}6)${NC} 🔧 Comandos úteis de produção"
    echo -e "${BLUE}7)${NC} ℹ️  Informações de produção"
    echo -e "${YELLOW}8)${NC} 🔄 Alternar para desenvolvimento"
    echo -e "${RED}0)${NC} 🚪 Sair"
    echo ""
    echo -n -e "${YELLOW}Digite sua escolha [0-8]: ${NC}"
}

# Função para fazer build
build_production() {
    show_header
    echo -e "${PURPLE}🏗️  Fazendo build de produção...${NC}"
    echo ""
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    "$SCRIPT_DIR/build-prod.sh"
    echo ""
    echo -e "${YELLOW}Pressione Enter para continuar...${NC}"
    read
}

# Função para iniciar o ambiente
start_production() {
    show_header
    echo -e "${GREEN}🚀 Iniciando ambiente de produção...${NC}"
    echo ""
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    "$SCRIPT_DIR/start-prod.sh"
    echo ""
    echo -e "${YELLOW}Pressione Enter para continuar...${NC}"
    read
}

# Função para parar o ambiente
stop_production() {
    show_header
    echo -e "${RED}🛑 Parando ambiente de produção...${NC}"
    echo ""
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    "$SCRIPT_DIR/stop-prod.sh"
    echo ""
    echo -e "${YELLOW}Pressione Enter para continuar...${NC}"
    read
}

# Função para verificar status
check_production_status() {
    show_header
    echo -e "${BLUE}📊 Verificando status de produção...${NC}"
    echo ""
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    "$SCRIPT_DIR/status-prod.sh"
    echo ""
    echo -e "${YELLOW}Pressione Enter para continuar...${NC}"
    read
}

# Função para mostrar logs em tempo real
show_production_logs() {
    show_header
    echo -e "${PURPLE}📝 Logs de produção em tempo real${NC}"
    echo ""
    echo -e "${BLUE}Escolha qual log visualizar:${NC}"
    echo ""
    echo -e "${GREEN}1)${NC} Backend log (produção)"
    echo -e "${GREEN}2)${NC} Frontend log (produção)"
    echo -e "${GREEN}3)${NC} Ambos os logs (split screen)"
    echo -e "${YELLOW}4)${NC} Logs arquivados"
    echo -e "${RED}0)${NC} Voltar ao menu principal"
    echo ""
    echo -n -e "${YELLOW}Digite sua escolha [0-4]: ${NC}"
    
    read log_choice
    
    case $log_choice in
        1)
            SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
            if [ -f "$SCRIPT_DIR/backend-prod.log" ]; then
                echo -e "${GREEN}Monitorando backend log de produção (Ctrl+C para sair)...${NC}"
                echo ""
                tail -f "$SCRIPT_DIR/backend-prod.log"
            else
                echo -e "${RED}❌ Log do backend de produção não encontrado${NC}"
                echo -e "${YELLOW}Pressione Enter para continuar...${NC}"
                read
            fi
            ;;
        2)
            SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
            if [ -f "$SCRIPT_DIR/frontend-prod.log" ]; then
                echo -e "${GREEN}Monitorando frontend log de produção (Ctrl+C para sair)...${NC}"
                echo ""
                tail -f "$SCRIPT_DIR/frontend-prod.log"
            else
                echo -e "${RED}❌ Log do frontend de produção não encontrado${NC}"
                echo -e "${YELLOW}Pressione Enter para continuar...${NC}"
                read
            fi
            ;;
        3)
            SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
            if [ -f "$SCRIPT_DIR/backend-prod.log" ] && [ -f "$SCRIPT_DIR/frontend-prod.log" ]; then
                echo -e "${GREEN}Monitorando ambos os logs de produção (Ctrl+C para sair)...${NC}"
                echo ""
                if command -v multitail &> /dev/null; then
                    multitail "$SCRIPT_DIR/backend-prod.log" "$SCRIPT_DIR/frontend-prod.log"
                else
                    echo -e "${YELLOW}Usando tail simples (instale multitail para melhor experiência)${NC}"
                    tail -f "$SCRIPT_DIR/backend-prod.log" "$SCRIPT_DIR/frontend-prod.log"
                fi
            else
                echo -e "${RED}❌ Um ou ambos os logs de produção não foram encontrados${NC}"
                echo -e "${YELLOW}Pressione Enter para continuar...${NC}"
                read
            fi
            ;;
        4)
            show_archived_logs
            ;;
        0)
            return
            ;;
        *)
            echo -e "${RED}❌ Opção inválida${NC}"
            echo -e "${YELLOW}Pressione Enter para continuar...${NC}"
            read
            ;;
    esac
}

# Função para mostrar logs arquivados
show_archived_logs() {
    echo -e "${BLUE}📁 Logs arquivados de produção:${NC}"
    echo ""
    
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    if [ -d "$SCRIPT_DIR/logs/archive" ]; then
        echo -e "${GREEN}Backend logs:${NC}"
        ls -la "$SCRIPT_DIR/logs/archive"/backend-prod_*.log 2>/dev/null | while read line; do
            echo "   $line"
        done
        
        echo ""
        echo -e "${GREEN}Frontend logs:${NC}"
        ls -la "$SCRIPT_DIR/logs/archive"/frontend-prod_*.log 2>/dev/null | while read line; do
            echo "   $line"
        done
        
        echo ""
        echo -e "${YELLOW}Para ver um log específico:${NC}"
        echo -e "${YELLOW}   less $SCRIPT_DIR/logs/archive/[nome_do_arquivo]${NC}"
    else
        echo -e "${YELLOW}Nenhum log arquivado encontrado${NC}"
    fi
    
    echo ""
    echo -e "${YELLOW}Pressione Enter para continuar...${NC}"
    read
}

# Função para mostrar comandos úteis
show_useful_commands() {
    show_header
    echo -e "${CYAN}🔧 Comandos úteis de produção do Image2Video${NC}"
    echo ""
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    echo -e "${BLUE}📋 Scripts de produção:${NC}"
    echo -e "   ${PURPLE}$SCRIPT_DIR/build-prod.sh${NC}     - Fazer build de produção"
    echo -e "   ${GREEN}$SCRIPT_DIR/start-prod.sh${NC}     - Iniciar produção"
    echo -e "   ${RED}$SCRIPT_DIR/stop-prod.sh${NC}      - Parar produção"
    echo -e "   ${YELLOW}$SCRIPT_DIR/status-prod.sh${NC}    - Status de produção"
    echo -e "   ${PURPLE}$SCRIPT_DIR/prod-manager.sh${NC}   - Este menu"
    echo ""
    echo -e "${BLUE}🌐 URLs de produção:${NC}"
    echo -e "   ${GREEN}Frontend:${NC}  http://localhost:3000"
    echo -e "   ${GREEN}Backend:${NC}   http://localhost:8080"
    echo -e "   ${GREEN}API Docs:${NC}  http://localhost:8080/docs"
    echo ""
    echo -e "${BLUE}📝 Comandos de log de produção:${NC}"
    echo -e "   ${YELLOW}tail -f $SCRIPT_DIR/backend-prod.log${NC}   - Log do backend"
    echo -e "   ${YELLOW}tail -f $SCRIPT_DIR/frontend-prod.log${NC}  - Log do frontend"
    echo -e "   ${YELLOW}ls $SCRIPT_DIR/logs/archive/${NC}           - Logs arquivados"
    echo ""
    echo -e "${BLUE}🔍 Comandos de debug de produção:${NC}"
    echo -e "   ${YELLOW}lsof -i:8080${NC}                           - Verificar porta backend"
    echo -e "   ${YELLOW}lsof -i:3000${NC}                           - Verificar porta frontend"
    echo -e "   ${YELLOW}ps aux | grep 'main.py'${NC}                - Processos backend"
    echo -e "   ${YELLOW}ps aux | grep 'http.server'${NC}            - Processos frontend"
    echo ""
    echo -e "${BLUE}📁 Diretórios de produção:${NC}"
    echo -e "   ${CYAN}Build:${NC}    $SCRIPT_DIR/../../build/"
    echo -e "   ${CYAN}Backend:${NC}  $SCRIPT_DIR/../../build/backend/"
    echo -e "   ${CYAN}Frontend:${NC} $SCRIPT_DIR/../../build/frontend/"
    echo -e "   ${CYAN}Logs:${NC}     $SCRIPT_DIR/logs/archive/"
    echo ""
    echo -e "${BLUE}🏗️  Comandos de build:${NC}"
    echo -e "   ${YELLOW}cd $SCRIPT_DIR/frontend && npm run build${NC}"
    echo -e "   ${YELLOW}du -sh $SCRIPT_DIR/../../build${NC}          - Tamanho do build"
    echo -e "   ${YELLOW}find $SCRIPT_DIR/../../build -name '*.log'${NC} - Encontrar logs"
    echo ""
    echo -e "${YELLOW}Pressione Enter para continuar...${NC}"
    read
}

# Função para mostrar informações de produção
show_production_info() {
    show_header
    echo -e "${CYAN}ℹ️  Informações de Produção - Image2Video${NC}"
    echo ""
    echo -e "${BLUE}📋 Diferenças da produção:${NC}"
    echo "   • Frontend servido como arquivos estáticos"
    echo "   • Backend otimizado para produção"
    echo "   • Logs separados e arquivamento automático"
    echo "   • Portas diferentes (3000 frontend, 8080 backend)"
    echo ""
    echo -e "${BLUE}🏗️  Processo de build:${NC}"
    echo "   1. Frontend: npm run build (gera dist/)"
    echo "   2. Backend: copia arquivos + ambiente virtual"
    echo "   3. Cria scripts de inicialização"
    echo "   4. Configura servidor web (Apache/Nginx)"
    echo ""
    echo -e "${BLUE}🚀 Portas de produção:${NC}"
    echo -e "   ${GREEN}Frontend:${NC} 3000 (HTTP server estático)"
    echo -e "   ${GREEN}Backend:${NC}  8080 (FastAPI/Uvicorn)"
    echo ""
    echo -e "${BLUE}📁 Estrutura de produção:${NC}"
    echo "   build/"
    echo "   ├── backend/              # Backend com venv"
    echo "   │   ├── main.py          # FastAPI app"
    echo "   │   ├── venv/            # Ambiente virtual"
    echo "   │   └── start-production.sh"
    echo "   ├── frontend/            # Build estático"
    echo "   │   ├── index.html       # App React buildado"
    echo "   │   ├── assets/          # CSS, JS, imagens"
    echo "   │   ├── .htaccess        # Config Apache"
    echo "   │   └── nginx.conf       # Config Nginx"
    echo "   └── serve-frontend.sh    # Servidor HTTP"
    echo ""
    echo -e "${BLUE}🔧 Configurações de servidor web:${NC}"
    echo -e "   ${YELLOW}Apache:${NC} Use o arquivo .htaccess incluído"
    echo -e "   ${YELLOW}Nginx:${NC}  Use a configuração nginx.conf incluída"
    echo -e "   ${YELLOW}Python:${NC} Servidor HTTP simples (desenvolvimento)"
    echo ""
    echo -e "${BLUE}📝 Logs de produção:${NC}"
    echo -e "   ${YELLOW}Atuais:${NC} backend-prod.log, frontend-prod.log"
    echo -e "   ${YELLOW}Arquivados:${NC} logs/archive/ (mantém últimos 10)"
    echo ""
    echo -e "${BLUE}⚠️  Considerações de produção real:${NC}"
    echo "   • Configure SSL/HTTPS"
    echo "   • Use servidor web profissional (Nginx/Apache)"
    echo "   • Configure firewall e segurança"
    echo "   • Implemente backup e monitoramento"
    echo "   • Configure variáveis de ambiente adequadas"
    echo "   • Use gerenciador de processos (PM2, systemd)"
    echo ""
    echo -e "${YELLOW}Pressione Enter para continuar...${NC}"
    read
}

# Função para alternar para desenvolvimento
switch_to_development() {
    show_header
    echo -e "${YELLOW}🔄 Alternando para ambiente de desenvolvimento...${NC}"
    echo ""
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    echo -e "${BLUE}Parando ambiente de produção...${NC}"
    "$SCRIPT_DIR/stop-prod.sh"
    echo ""
    echo -e "${GREEN}Iniciando ambiente de desenvolvimento...${NC}"
    "$SCRIPT_DIR/start-dev.sh"
    echo ""
    echo -e "${GREEN}✅ Alternado para ambiente de desenvolvimento!${NC}"
    echo ""
    echo -e "${BLUE}Para gerenciar desenvolvimento:${NC}"
    echo -e "   ${GREEN}$SCRIPT_DIR/dev-manager.sh${NC}"
    echo ""
    echo -e "${YELLOW}Pressione Enter para continuar...${NC}"
    read
}

# Função principal do menu
main_menu() {
    while true; do
        show_header
        show_menu
        
        read choice
        
        case $choice in
            1)
                build_production
                ;;
            2)
                start_production
                ;;
            3)
                stop_production
                ;;
            4)
                check_production_status
                ;;
            5)
                show_production_logs
                ;;
            6)
                show_useful_commands
                ;;
            7)
                show_production_info
                ;;
            8)
                switch_to_development
                ;;
            0)
                show_header
                echo -e "${GREEN}👋 Obrigado por usar o Image2Video Production Manager!${NC}"
                echo ""
                exit 0
                ;;
            *)
                show_header
                echo -e "${RED}❌ Opção inválida. Tente novamente.${NC}"
                echo ""
                echo -e "${YELLOW}Pressione Enter para continuar...${NC}"
                read
                ;;
        esac
    done
}

# Verificar se o script está sendo executado diretamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    # Verificar se está sendo executado com argumentos para modo não-interativo
    if [ $# -gt 0 ]; then
        SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        case $1 in
            build|1)
                "$SCRIPT_DIR/build-prod.sh"
                ;;
            start|2)
                "$SCRIPT_DIR/start-prod.sh"
                ;;
            stop|3)
                "$SCRIPT_DIR/stop-prod.sh"
                ;;
            status|4)
                "$SCRIPT_DIR/status-prod.sh"
                ;;
            *)
                echo -e "${RED}❌ Argumento inválido: $1${NC}"
                echo -e "${YELLOW}Uso: $0 [build|start|stop|status]${NC}"
                exit 1
                ;;
        esac
    else
        # Modo interativo
        main_menu
    fi
fi
