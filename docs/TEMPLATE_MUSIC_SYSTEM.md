# Sistema de Música por Template

Este documento descreve o sistema de música específica por template implementado na aplicação Image2Video.

## Visão Geral

Cada template agora pode ter sua própria música de fundo específica, permitindo uma experiência mais personalizada e adequada ao estilo visual de cada template.

## Configuração

### Estrutura do Template

Cada template no arquivo `backend/templates.py` agora inclui o campo `background_music`:

```python
{
    "id": "template-id",
    "name": "Template Name",
    "description": "Template description",
    # ... outros campos ...
    "background_music": "nome_do_arquivo.mp3"
}
```

### Músicas Disponíveis

As seguintes músicas estão configuradas por template:

| Template | Música | Descrição |
|----------|--------|-----------|
| `grid-showcase-template` | `upbeat_showcase.mp3` | Música animada para showcase de fotos |
| `cinematic-showcase-template` | `cinematic_epic.mp3` | Música épica cinematográfica |
| `thumbnail-zoom-template` | `smooth_transitions.mp3` | Música suave para transições |
| *Outros templates* | `source_bg_clean.mp3` | Música padrão (fallback) |

## Implementação Técnica

### MoviePy Editor

O `MoviePyEditor` foi modificado para:

1. **Receber o template**: O método `_add_background_audio()` agora recebe o template como parâmetro
2. **Selecionar música**: Usa `template.get('background_music')` para determinar qual arquivo usar
3. **Fallback inteligente**: Se a música específica não existir, usa a música padrão automaticamente

```python
def _add_background_audio(self, video_clip: VideoFileClip, job_id: str, template: Dict = None) -> VideoFileClip:
    # Usar música específica do template se disponível
    if template and template.get('background_music'):
        audio_filename = template['background_music']
    else:
        audio_filename = "source_bg_clean.mp3"  # Fallback padrão
```

### FFmpeg Processor

O `VideoProcessor` (FFmpeg) também foi atualizado com a mesma lógica:

1. **Detecção de música**: Verifica se o template tem música específica
2. **Fallback robusto**: Se a música não existir, usa a padrão automaticamente
3. **Logs informativos**: Mostra qual música está sendo usada nos logs

## Adicionando Novas Músicas

### 1. Adicionar Arquivo de Áudio

Coloque o arquivo `.mp3` no diretório `backend/assets/`:

```bash
cp nova_musica.mp3 backend/assets/
```

### 2. Configurar no Template

Edite `backend/templates.py` e adicione/modifique o campo `background_music`:

```python
"template-id": {
    # ... outros campos ...
    "background_music": "nova_musica.mp3"
}
```

### 3. Reiniciar o Backend

Reinicie o backend para carregar as novas configurações.

## Logs e Debugging

O sistema gera logs informativos para facilitar o debugging:

- `🎵 Adicionando áudio de fundo específico do template: /path/to/music.mp3`
- `🎵 Usando música padrão como fallback: /path/to/default.mp3`
- `🔇 Nenhuma música disponível`

## Compatibilidade

- ✅ **Backward Compatible**: Templates sem `background_music` usam a música padrão
- ✅ **Fallback Robusto**: Se uma música específica não existir, usa a padrão automaticamente
- ✅ **Suporte Completo**: Funciona tanto com MoviePy quanto com FFmpeg

## Benefícios

1. **Experiência Personalizada**: Cada template tem música adequada ao seu estilo
2. **Flexibilidade**: Fácil adição de novas músicas e templates
3. **Robustez**: Sistema de fallback previne erros
4. **Manutenibilidade**: Configuração centralizada e clara

## Exemplo de Uso

```bash
# Criar vídeo com template grid-showcase (usa upbeat_showcase.mp3)
curl -X POST http://localhost:8080/api/videos/create \
  -H "Content-Type: application/json" \
  -d '{
    "templateId": "grid-showcase-template",
    "photos": [...],
    "backgroundAudio": true
  }'

# Criar vídeo com template cinematográfico (usa cinematic_epic.mp3)
curl -X POST http://localhost:8080/api/videos/create \
  -H "Content-Type: application/json" \
  -d '{
    "templateId": "cinematic-showcase-template",
    "photos": [...],
    "backgroundAudio": true
  }'
```

## Estrutura de Arquivos

```
backend/
├── assets/
│   ├── source_bg_clean.mp3      # Música padrão
│   ├── upbeat_showcase.mp3      # Grid Showcase
│   ├── cinematic_epic.mp3       # Cinematic Showcase
│   └── smooth_transitions.mp3   # Thumbnail Zoom
├── templates.py                 # Configuração dos templates
├── moviepy_editor.py           # Processador MoviePy
└── video_processor.py          # Processador FFmpeg
```
