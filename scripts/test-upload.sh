#!/bin/bash

echo "🧪 Testando upload completo..."

# 1. Criar um job
echo "📝 Criando job..."
JOB_RESPONSE=$(curl -s -X POST http://localhost:8080/api/jobs \
  -H "Content-Type: application/json" \
  -d '{}')

JOB_CODE=$(echo "$JOB_RESPONSE" | grep -o '"code":"[^"]*"' | cut -d'"' -f4)
echo "✅ Job criado: $JOB_CODE"

# 2. Criar uma imagem de teste
echo "🖼️ Criando imagem de teste..."
convert -size 100x100 xc:red test_image.jpg 2>/dev/null || {
  echo "⚠️ ImageMagick não disponível, criando arquivo de teste..."
  echo "fake image data" > test_image.jpg
}

# 3. Obter URL de upload
echo "🔗 Obtendo URL de upload..."
UPLOAD_URL_RESPONSE=$(curl -s -X POST http://localhost:8080/api/upload-url \
  -H "Content-Type: application/json" \
  -d "{\"filename\": \"test_image.jpg\", \"content_type\": \"image/jpeg\", \"job_code\": \"$JOB_CODE\"}")

UPLOAD_URL=$(echo "$UPLOAD_URL_RESPONSE" | grep -o '"upload_url":"[^"]*"' | cut -d'"' -f4)
OBJECT_KEY=$(echo "$UPLOAD_URL_RESPONSE" | grep -o '"object_key":"[^"]*"' | cut -d'"' -f4)

echo "✅ URL de upload: $UPLOAD_URL"
echo "✅ Object key: $OBJECT_KEY"

# 4. Fazer upload do arquivo
echo "📤 Fazendo upload..."
UPLOAD_RESPONSE=$(curl -s -X PUT "$UPLOAD_URL" \
  -H "Content-Type: image/jpeg" \
  --data-binary @test_image.jpg)

echo "✅ Upload response: $UPLOAD_RESPONSE"

# 5. Verificar se o arquivo foi salvo
echo "📁 Verificando storage..."
if [ -f "storage/$OBJECT_KEY" ]; then
  echo "✅ Arquivo salvo em: storage/$OBJECT_KEY"
  ls -la "storage/$OBJECT_KEY"
else
  echo "❌ Arquivo não encontrado em: storage/$OBJECT_KEY"
  echo "📂 Estrutura do storage:"
  find storage/ -type f 2>/dev/null || echo "Nenhum arquivo encontrado"
fi

# 6. Verificar status do job
echo "📊 Verificando status do job..."
JOB_STATUS=$(curl -s "http://localhost:8080/api/jobs/$JOB_CODE")
echo "✅ Status do job: $JOB_STATUS"

# 7. Limpar arquivo de teste
rm -f test_image.jpg

echo ""
echo "🎉 Teste de upload concluído!"
echo "📋 Resumo:"
echo "  - Job: $JOB_CODE"
echo "  - Arquivo: $OBJECT_KEY"
echo "  - Status: $(echo "$JOB_STATUS" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)"
