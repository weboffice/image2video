#!/usr/bin/env python3
"""
Teste da nova configuração do banco de dados usando apenas variáveis individuais
"""

import os
import sys
from pathlib import Path

def test_database_config():
    """Testar nova configuração do banco de dados"""
    print("=== Teste da Nova Configuração do Banco ===\n")
    
    try:
        # 1. Carregar config para garantir que .env seja lido
        print("1. Carregando configurações...")
        import config
        print("   ✅ Config carregado")
        
        # 2. Verificar variáveis individuais
        print("\n2. Verificando variáveis individuais do banco:")
        db_vars = {
            "DB_HOST": os.getenv("DB_HOST"),
            "DB_PORT": os.getenv("DB_PORT"),
            "DB_USER": os.getenv("DB_USER"),
            "DB_PASSWORD": os.getenv("DB_PASSWORD"),
            "DB_NAME": os.getenv("DB_NAME")
        }
        
        all_vars_ok = True
        for var, value in db_vars.items():
            if value:
                if "PASSWORD" in var:
                    print(f"   ✅ {var}: {'*' * len(value)}")
                else:
                    print(f"   ✅ {var}: {value}")
            else:
                print(f"   ❌ {var}: NÃO DEFINIDA")
                all_vars_ok = False
        
        if not all_vars_ok:
            return False
        
        # 3. Testar importação do database
        print("\n3. Testando importação do database...")
        from database import engine, DATABASE_URL, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME
        print("   ✅ Database importado")
        
        # 4. Verificar se DATABASE_URL foi construída corretamente
        expected_url = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
        print(f"\n4. Verificando DATABASE_URL construída:")
        print(f"   Esperada: mysql+pymysql://{DB_USER}:***@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4")
        print(f"   Atual:    mysql+pymysql://{DB_USER}:***@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4")
        
        if DATABASE_URL == expected_url:
            print("   ✅ DATABASE_URL construída corretamente")
        else:
            print("   ❌ DATABASE_URL não está correta")
            print(f"   Esperada: {expected_url}")
            print(f"   Atual:    {DATABASE_URL}")
            return False
        
        # 5. Testar conexão com o banco
        print("\n5. Testando conexão com o banco...")
        try:
            from sqlalchemy import text
            with engine.connect() as connection:
                result = connection.execute(text("SELECT 1 as test"))
                test_value = result.fetchone()[0]
                if test_value == 1:
                    print("   ✅ Conexão com banco estabelecida com sucesso!")
                    return True
        except Exception as db_error:
            print(f"   ❌ Erro na conexão: {db_error}")
            
            # Sugestões específicas para as novas credenciais
            print("\n💡 Possíveis soluções:")
            print(f"   1. Verificar se o usuário '{DB_USER}' existe no MariaDB/MySQL")
            print(f"   2. Verificar se a senha está correta")
            print(f"   3. Criar o usuário se não existir:")
            print(f"      mysql -u root -p -e \"CREATE USER '{DB_USER}'@'localhost' IDENTIFIED BY '{DB_PASSWORD}';\"")
            print(f"   4. Dar permissões ao usuário:")
            print(f"      mysql -u root -p -e \"GRANT ALL PRIVILEGES ON {DB_NAME}.* TO '{DB_USER}'@'localhost';\"")
            print(f"   5. Criar o banco de dados se não existir:")
            print(f"      mysql -u root -p -e \"CREATE DATABASE {DB_NAME};\"")
            print("   6. Recarregar privilégios:")
            print("      mysql -u root -p -e \"FLUSH PRIVILEGES;\"")
            
            return False
            
    except Exception as e:
        print(f"\n❌ Erro geral: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_database_config()
    
    if success:
        print("\n🎉 Nova configuração do banco funcionando!")
        print("✅ Variáveis individuais carregadas corretamente")
        print("✅ DATABASE_URL construída automaticamente")
        print("✅ Conexão com banco estabelecida")
    else:
        print("\n❌ Problemas na nova configuração do banco")
        print("Verifique as sugestões acima")
    
    sys.exit(0 if success else 1)
