# Scripts de Teste e Geração de Vídeo

Este diretório contém scripts Python para testar e gerar vídeos usando os templates do sistema.

## Scripts Disponíveis

### 1. `test_template.py` - Teste de Templates
**Uso:** `python scripts/test_template.py <job_id> [template_id]`

**Função:** Analisa um job e mostra informações detalhadas sobre o template, fotos e breakdown das cenas.

**Exemplo:**
```bash
python scripts/test_template.py 4F33315F
python scripts/test_template.py 4F33315F grid-showcase-template
```

**Saída:**
- ✅ Configuração carregada
- ✅ Template identificado
- ✅ Fotos encontradas
- ✅ Duração total calculada
- ✅ Breakdown das cenas
- ✅ Script FFmpeg gerado
- ✅ Arquivo JSON com detalhes

### 2. `simple_video_generator.py` - Gerador Simples
**Uso:** `python scripts/simple_video_generator.py <job_id> [duration_per_photo]`

**Função:** Gera um slideshow simples com todas as fotos do job.

**Exemplo:**
```bash
python scripts/simple_video_generator.py 4F33315F
python scripts/simple_video_generator.py 4F33315F 6.0
```

**Características:**
- Slideshow básico com fade entre fotos
- Duração configurável por foto (padrão: 4 segundos)
- Resolução 1920x1080
- Formato MP4

### 3. `advanced_video_generator.py` - Gerador Avançado
**Uso:** `python scripts/advanced_video_generator.py <job_id> [template_id]`

**Função:** Gera vídeo usando templates com efeitos avançados.

**Exemplo:**
```bash
python scripts/advanced_video_generator.py 4F33315F
python scripts/advanced_video_generator.py 4F33315F grid-showcase-template
```

**Características:**
- Suporte a templates complexos
- Efeitos de grade (grid)
- Efeitos de zoom
- Transições suaves
- Layout 16:9

## Templates Disponíveis

### Grid Showcase Template
- **ID:** `grid-showcase-template`
- **Descrição:** Mostra as primeiras 6 fotos em layout 16:9 com efeitos de movimento
- **Cenas:**
  1. **Grid Showcase** (8s): Layout de grade 3x2
  2. **Individual Showcase** (4s por foto): Zoom individual em cada foto

### Thumbnail + Zoom Template
- **ID:** `thumbnail-zoom-template`
- **Descrição:** Mostra thumbnails primeiro, depois zoom em cada foto
- **Cenas:**
  1. **Thumbnails Overview** (3s): Visão geral das fotos
  2. **Zoom Sequence** (6s por foto): Zoom individual

## Estrutura de Arquivos

```
scripts/
├── test_template.py              # Teste de templates
├── simple_video_generator.py     # Gerador simples
├── advanced_video_generator.py   # Gerador avançado
└── README.md                     # Este arquivo
```

## Arquivos Gerados

Os scripts geram os seguintes arquivos:

### Arquivos de Saída
- `{job_id}_simple.mp4` - Vídeo gerado pelo script simples
- `{job_id}_advanced.mp4` - Vídeo gerado pelo script avançado
- `{job_id}_test_output.mp4` - Vídeo de teste (se aplicável)

### Arquivos de Análise
- `{job_id}_config.json` - Configuração do job (já existente)
- `{job_id}_breakdown.json` - Breakdown detalhado das cenas
- `{job_id}_ffmpeg_script.sh` - Script FFmpeg gerado

## Requisitos

- Python 3.8+
- FFmpeg instalado e no PATH
- ImageMagick (opcional, para efeitos de grade avançados)

## Exemplo Completo

```bash
# 1. Testar o job
python scripts/test_template.py 4F33315F

# 2. Gerar vídeo simples
python scripts/simple_video_generator.py 4F33315F

# 3. Gerar vídeo avançado
python scripts/advanced_video_generator.py 4F33315F

# 4. Verificar resultados
ls -la backend/storage/videos/4F33315F_*.mp4
```

## Troubleshooting

### Erro: "Arquivo de configuração não encontrado"
- Verifique se o job ID está correto
- Confirme que o arquivo `{job_id}_config.json` existe em `backend/storage/videos/`

### Erro: "Nenhuma foto encontrada"
- Verifique se as fotos existem no caminho especificado
- Confirme que os caminhos no arquivo de configuração estão corretos

### Erro: "Template não encontrado"
- Verifique se o template ID está correto
- Confirme que o template está definido em `backend/main.py`

### Erro: "FFmpeg command failed"
- Verifique se o FFmpeg está instalado: `ffmpeg -version`
- Confirme que as fotos são válidas e acessíveis
- Verifique se há espaço suficiente em disco

## Logs e Debug

Os scripts geram logs detalhados durante a execução:
- ✅ Sucessos
- ⚠️ Avisos
- ❌ Erros

Para debug adicional, os scripts mostram:
- Comandos FFmpeg executados
- Caminhos dos arquivos
- Estatísticas de processamento
