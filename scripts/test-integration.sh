#!/bin/bash

# Script para testar a integração frontend-backend
echo "🧪 Testando integração frontend-backend..."

# Verificar se o backend está rodando
echo "📡 Verificando backend..."
if curl -s http://localhost:8080/health > /dev/null; then
    echo "✅ Backend está rodando na porta 8080"
else
    echo "❌ Backend não está rodando. Inicie com: cd backend && python main.py"
    exit 1
fi

# Verificar se o frontend está rodando
echo "🎨 Verificando frontend..."
if curl -s http://localhost:5173 > /dev/null; then
    echo "✅ Frontend está rodando na porta 5173"
else
    echo "❌ Frontend não está rodando. Inicie com: cd frontend && npm run dev"
    exit 1
fi

# Testar endpoint de health check
echo "🏥 Testando health check..."
HEALTH_RESPONSE=$(curl -s http://localhost:8080/health)
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo "✅ Health check OK: $HEALTH_RESPONSE"
else
    echo "❌ Health check falhou: $HEALTH_RESPONSE"
fi

# Testar criação de job
echo "📝 Testando criação de job..."
JOB_RESPONSE=$(curl -s -X POST http://localhost:8080/api/jobs \
  -H "Content-Type: application/json" \
  -d '{"template_id": "test"}')

if echo "$JOB_RESPONSE" | grep -q "code"; then
    JOB_CODE=$(echo "$JOB_RESPONSE" | grep -o '"code":"[^"]*"' | cut -d'"' -f4)
    echo "✅ Job criado com sucesso: $JOB_CODE"
    
    # Testar obtenção de status do job
    echo "📊 Testando status do job..."
    STATUS_RESPONSE=$(curl -s http://localhost:8080/api/jobs/$JOB_CODE)
    if echo "$STATUS_RESPONSE" | grep -q "status"; then
        echo "✅ Status do job OK: $STATUS_RESPONSE"
    else
        echo "❌ Status do job falhou: $STATUS_RESPONSE"
    fi
else
    echo "❌ Criação de job falhou: $JOB_RESPONSE"
fi

# Testar proxy do frontend
echo "🔄 Testando proxy do frontend..."
PROXY_RESPONSE=$(curl -s http://localhost:5173/api/health)
if echo "$PROXY_RESPONSE" | grep -q "healthy"; then
    echo "✅ Proxy do frontend OK: $PROXY_RESPONSE"
else
    echo "❌ Proxy do frontend falhou: $PROXY_RESPONSE"
fi

echo ""
echo "🎉 Teste de integração concluído!"
echo ""
echo "📋 Resumo:"
echo "  - Backend: http://localhost:8080"
echo "  - Frontend: http://localhost:5173"
echo "  - API Docs: http://localhost:8080/docs"
echo ""
echo "🚀 Para iniciar ambos os serviços: npm run dev"
