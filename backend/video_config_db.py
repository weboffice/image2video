"""
Utilitários para gerenciar configurações de vídeo no banco de dados
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, Dict, Any
import json
from datetime import datetime

from database import SessionLocal
from models import VideoConfig

def get_db():
    """Obter sessão do banco de dados"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_video_config(
    job_id: str,
    template_id: str,
    config_data: Dict[str, Any],
    db: Session = None
) -> VideoConfig:
    """Criar nova configuração de vídeo no banco"""
    
    if db is None:
        db = next(get_db())
        close_db = True
    else:
        close_db = False
    
    try:
        video_config = VideoConfig(
            job_id=job_id,
            template_id=template_id,
            config_data=config_data,
            status="created",
            progress=0
        )
        
        db.add(video_config)
        db.commit()
        db.refresh(video_config)
        
        return video_config
        
    except IntegrityError:
        db.rollback()
        # Se já existe, atualizar
        return update_video_config(job_id, template_id=template_id, config_data=config_data, db=db)
    finally:
        if close_db:
            db.close()

def get_video_config(job_id: str, db: Session = None) -> Optional[VideoConfig]:
    """Obter configuração de vídeo por job_id"""
    
    if db is None:
        db = next(get_db())
        close_db = True
    else:
        close_db = False
    
    try:
        return db.query(VideoConfig).filter(VideoConfig.job_id == job_id).first()
    finally:
        if close_db:
            db.close()

def update_video_config(
    job_id: str,
    status: Optional[str] = None,
    progress: Optional[int] = None,
    output_path: Optional[str] = None,
    error_message: Optional[str] = None,
    template_id: Optional[str] = None,
    config_data: Optional[Dict[str, Any]] = None,
    db: Session = None
) -> Optional[VideoConfig]:
    """Atualizar configuração de vídeo"""
    
    if db is None:
        db = next(get_db())
        close_db = True
    else:
        close_db = False
    
    try:
        video_config = db.query(VideoConfig).filter(VideoConfig.job_id == job_id).first()
        
        if not video_config:
            return None
        
        # Atualizar campos fornecidos
        if status is not None:
            video_config.status = status
        if progress is not None:
            video_config.progress = progress
        if output_path is not None:
            video_config.output_path = output_path
        if error_message is not None:
            video_config.error_message = error_message
        if template_id is not None:
            video_config.template_id = template_id
        if config_data is not None:
            video_config.config_data = config_data
        
        video_config.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(video_config)
        
        return video_config
        
    finally:
        if close_db:
            db.close()

def delete_video_config(job_id: str, db: Session = None) -> bool:
    """Deletar configuração de vídeo"""
    
    if db is None:
        db = next(get_db())
        close_db = True
    else:
        close_db = False
    
    try:
        video_config = db.query(VideoConfig).filter(VideoConfig.job_id == job_id).first()
        
        if not video_config:
            return False
        
        db.delete(video_config)
        db.commit()
        
        return True
        
    finally:
        if close_db:
            db.close()

def list_video_configs(
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = None
) -> list[VideoConfig]:
    """Listar configurações de vídeo com filtros opcionais"""
    
    if db is None:
        db = next(get_db())
        close_db = True
    else:
        close_db = False
    
    try:
        query = db.query(VideoConfig)
        
        if status:
            query = query.filter(VideoConfig.status == status)
        
        return query.offset(offset).limit(limit).all()
        
    finally:
        if close_db:
            db.close()
