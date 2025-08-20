#!/usr/bin/env python3
"""
Script para criar a tabela video_configs no banco de dados
"""

import sys
import os

# Adicionar o diretório backend ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import engine, Base
from models import VideoConfig

def create_video_config_table():
    """Cria a tabela video_configs no banco de dados"""
    
    print("🗄️  Criando tabela video_configs...")
    
    try:
        # Criar apenas a tabela VideoConfig
        VideoConfig.__table__.create(engine, checkfirst=True)
        print("✅ Tabela video_configs criada com sucesso!")
        
        # Mostrar a estrutura da tabela
        print("\n📋 Estrutura da tabela:")
        print("- id: INTEGER (Primary Key)")
        print("- job_id: VARCHAR(32) (Unique, Index)")
        print("- template_id: VARCHAR(100)")
        print("- config_data: JSON")
        print("- status: VARCHAR(32)")
        print("- progress: INTEGER")
        print("- output_path: VARCHAR(500)")
        print("- error_message: TEXT")
        print("- created_at: DATETIME")
        print("- updated_at: DATETIME")
        
    except Exception as e:
        print(f"❌ Erro ao criar tabela: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = create_video_config_table()
    if success:
        print("\n🎉 Migração concluída com sucesso!")
    else:
        print("\n💥 Falha na migração!")
        sys.exit(1)
