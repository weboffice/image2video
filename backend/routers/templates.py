from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

# Imports resilientes
try:
    from ..templates import TEMPLATES
except ImportError:
    from templates import TEMPLATES

router = APIRouter(prefix="/api/templates", tags=["templates"])

@router.get("")
async def get_templates():
    """Retorna todos os templates disponíveis"""
    return {
        "templates": list(TEMPLATES.values())
    }

@router.get("/{template_id}")
async def get_template(template_id: str):
    """Retorna um template específico"""
    if template_id not in TEMPLATES:
        raise HTTPException(status_code=404, detail="Template não encontrado")
    return TEMPLATES[template_id]
