#!/bin/bash

# Script de gerenciamento do ambiente de desenvolvimento Image2Video
# Menu interativo para iniciar, parar e verificar status

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
    echo "║                    IMAGE2VIDEO DEV MANAGER                   ║"
    echo "║              Gerenciador de Desenvolvimento                  ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
}

# Função para mostrar o menu principal
show_menu() {
    echo -e "${BLUE}📋 Escolha uma opção:${NC}"
    echo ""
    echo -e "${GREEN}1)${NC} 🚀 Iniciar ambiente de desenvolvimento"
    echo -e "${RED}2)${NC} 🛑 Parar ambiente de desenvolvimento"
    echo -e "${YELLOW}3)${NC} 📊 Verificar status dos serviços"
    echo -e "${PURPLE}4)${NC} 📝 Ver logs em tempo real"
    echo -e "${CYAN}5)${NC} 🔧 Comandos úteis"
    echo -e "${BLUE}6)${NC} ℹ️  Informações do projeto"
    echo -e "${RED}0)${NC} 🚪 Sair"
    echo ""
    echo -n -e "${YELLOW}Digite sua escolha [0-6]: ${NC}"
}

# Função para iniciar o ambiente
start_environment() {
    show_header
    echo -e "${GREEN}🚀 Iniciando ambiente de desenvolvimento...${NC}"
    echo ""
    /home/image2video/source/image2video/start-dev.sh
    echo ""
    echo -e "${YELLOW}Pressione Enter para continuar...${NC}"
    read
}

# Função para parar o ambiente
stop_environment() {
    show_header
    echo -e "${RED}🛑 Parando ambiente de desenvolvimento...${NC}"
    echo ""
    /home/image2video/source/image2video/stop-dev.sh
    echo ""
    echo -e "${YELLOW}Pressione Enter para continuar...${NC}"
    read
}

# Função para verificar status
check_status() {
    show_header
    echo -e "${BLUE}📊 Verificando status dos serviços...${NC}"
    echo ""
    /home/image2video/source/image2video/status-dev.sh
    echo ""
    echo -e "${YELLOW}Pressione Enter para continuar...${NC}"
    read
}

# Função para mostrar logs em tempo real
show_logs() {
    show_header
    echo -e "${PURPLE}📝 Logs em tempo real${NC}"
    echo ""
    echo -e "${BLUE}Escolha qual log visualizar:${NC}"
    echo ""
    echo -e "${GREEN}1)${NC} Backend log"
    echo -e "${GREEN}2)${NC} Frontend log"
    echo -e "${GREEN}3)${NC} Ambos os logs (split screen)"
    echo -e "${RED}0)${NC} Voltar ao menu principal"
    echo ""
    echo -n -e "${YELLOW}Digite sua escolha [0-3]: ${NC}"
    
    read log_choice
    
    case $log_choice in
        1)
            if [ -f "/home/image2video/backend.log" ]; then
                echo -e "${GREEN}Monitorando backend log (Ctrl+C para sair)...${NC}"
                echo ""
                tail -f /home/image2video/backend.log
            else
                echo -e "${RED}❌ Log do backend não encontrado${NC}"
                echo -e "${YELLOW}Pressione Enter para continuar...${NC}"
                read
            fi
            ;;
        2)
            if [ -f "/home/image2video/source/image2video/logs/frontend.log" ]; then
                echo -e "${GREEN}Monitorando frontend log (Ctrl+C para sair)...${NC}"
                echo ""
                tail -f /home/image2video/source/image2video/logs/frontend.log
            else
                echo -e "${RED}❌ Log do frontend não encontrado${NC}"
                echo -e "${YELLOW}Pressione Enter para continuar...${NC}"
                read
            fi
            ;;
        3)
            if [ -f "/home/image2video/source/image2video/logs/backend.log" ] && [ -f "/home/image2video/source/image2video/logs/frontend.log" ]; then
                echo -e "${GREEN}Monitorando ambos os logs (Ctrl+C para sair)...${NC}"
                echo ""
                # Usar multitail se disponível, senão usar tail simples
                if command -v multitail &> /dev/null; then
                    multitail /home/image2video/source/image2video/logs/backend.log /home/image2video/source/image2video/logs/frontend.log
                else
                    echo -e "${YELLOW}Instalando multitail para melhor visualização...${NC}"
                    sudo apt-get update && sudo apt-get install -y multitail 2>/dev/null || {
                        echo -e "${YELLOW}Usando tail simples (instale multitail para melhor experiência)${NC}"
                        tail -f /home/image2video/source/image2video/logs/backend.log /home/image2video/source/image2video/logs/frontend.log
                    }
                fi
            else
                echo -e "${RED}❌ Um ou ambos os logs não foram encontrados${NC}"
                echo -e "${YELLOW}Pressione Enter para continuar...${NC}"
                read
            fi
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

# Função para mostrar comandos úteis
show_useful_commands() {
    show_header
    echo -e "${CYAN}🔧 Comandos úteis do Image2Video${NC}"
    echo ""
    echo -e "${BLUE}📋 Scripts de gerenciamento:${NC}"
    echo -e "   ${GREEN}/home/image2video/source/image2video/start-dev.sh${NC}     - Iniciar ambiente"
    echo -e "   ${RED}/home/image2video/source/image2video/stop-dev.sh${NC}      - Parar ambiente"
    echo -e "   ${YELLOW}/home/image2video/source/image2video/status-dev.sh${NC}    - Verificar status"
    echo -e "   ${PURPLE}/home/image2video/source/image2video/dev-manager.sh${NC}   - Este menu"
    echo ""
    echo -e "${BLUE}🌐 URLs do projeto:${NC}"
    echo -e "   ${GREEN}Frontend:${NC}  http://localhost:5173"
    echo -e "   ${GREEN}Backend:${NC}   http://localhost:8080"
    echo -e "   ${GREEN}API Docs:${NC}  http://localhost:8080/docs"
    echo ""
    echo -e "${BLUE}📝 Comandos de log:${NC}"
    echo -e "   ${YELLOW}tail -f /home/image2video/source/image2video/logs/backend.log${NC}   - Log do backend"
    echo -e "   ${YELLOW}tail -f /home/image2video/source/image2video/logs/frontend.log${NC}  - Log do frontend"
    echo ""
    echo -e "${BLUE}🔍 Comandos de debug:${NC}"
    echo -e "   ${YELLOW}lsof -i:8080${NC}                           - Verificar porta backend"
    echo -e "   ${YELLOW}lsof -i:5173${NC}                           - Verificar porta frontend"
    echo -e "   ${YELLOW}ps aux | grep python${NC}                   - Processos Python"
    echo -e "   ${YELLOW}ps aux | grep node${NC}                     - Processos Node.js"
    echo ""
    echo -e "${BLUE}📁 Diretórios importantes:${NC}"
    echo -e "   ${CYAN}Projeto:${NC}  /home/image2video/source/image2video/"
    echo -e "   ${CYAN}Backend:${NC}  /home/image2video/source/image2video/backend/"
    echo -e "   ${CYAN}Frontend:${NC} /home/image2video/source/image2video/frontend/"
    echo ""
    echo -e "${YELLOW}Pressione Enter para continuar...${NC}"
    read
}

# Função para mostrar informações do projeto
show_project_info() {
    show_header
    echo -e "${CYAN}ℹ️  Informações do Projeto Image2Video${NC}"
    echo ""
    echo -e "${BLUE}📋 Descrição:${NC}"
    echo "   Sistema de conversão de imagens para vídeo"
    echo "   Frontend React + Backend FastAPI"
    echo ""
    echo -e "${BLUE}🛠️  Tecnologias:${NC}"
    echo -e "   ${GREEN}Frontend:${NC} React, Vite, TypeScript, Tailwind CSS"
    echo -e "   ${GREEN}Backend:${NC}  FastAPI, Python, SQLAlchemy, MinIO"
    echo -e "   ${GREEN}Banco:${NC}    SQLite/MySQL"
    echo -e "   ${GREEN}Storage:${NC}  MinIO (S3-compatible)"
    echo ""
    echo -e "${BLUE}🚀 Portas padrão:${NC}"
    echo -e "   ${GREEN}Frontend:${NC} 5173 (Vite dev server)"
    echo -e "   ${GREEN}Backend:${NC}  8080 (FastAPI/Uvicorn)"
    echo -e "   ${GREEN}MinIO:${NC}    6000 (API) / 6001 (Console)"
    echo ""
    echo -e "${BLUE}📁 Estrutura:${NC}"
    echo "   ├── frontend/     # React + Vite"
    echo "   ├── backend/      # FastAPI"
    echo "   ├── storage/      # Arquivos locais"
    echo "   └── scripts/      # Scripts utilitários"
    echo ""
    echo -e "${BLUE}🔧 Configuração:${NC}"
    echo -e "   ${YELLOW}Backend .env:${NC} /home/image2video/source/image2video/backend/.env"
    echo -e "   ${YELLOW}Frontend .env:${NC} /home/image2video/source/image2video/frontend/.env"
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
                start_environment
                ;;
            2)
                stop_environment
                ;;
            3)
                check_status
                ;;
            4)
                show_logs
                ;;
            5)
                show_useful_commands
                ;;
            6)
                show_project_info
                ;;
            0)
                show_header
                echo -e "${GREEN}👋 Obrigado por usar o Image2Video Dev Manager!${NC}"
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
        case $1 in
            start|1)
                /home/image2video/source/image2video/start-dev.sh
                ;;
            stop|2)
                /home/image2video/source/image2video/stop-dev.sh
                ;;
            status|3)
                /home/image2video/source/image2video/status-dev.sh
                ;;
            *)
                echo -e "${RED}❌ Argumento inválido: $1${NC}"
                echo -e "${YELLOW}Uso: $0 [start|stop|status]${NC}"
                exit 1
                ;;
        esac
    else
        # Modo interativo
        main_menu
    fi
fi
