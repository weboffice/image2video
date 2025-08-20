from pydantic import BaseModel
from typing import List, Dict, Any

# Modelos para templates
class SceneEffect(BaseModel):
    id: str
    type: str
    duration: float
    parameters: Dict[str, Any]

class Scene(BaseModel):
    id: str
    name: str
    type: str
    duration: float
    max_photos: int
    effects: List[SceneEffect]
    order: int

class Template(BaseModel):
    id: str
    name: str
    description: str
    thumbnail: str
    scenes: List[Scene]
    total_duration: float
    max_photos: int
    background_music: str = "source_bg.mp3"  # Música padrão

# Templates disponíveis
TEMPLATES = {
    "grid-showcase-template": {
        "id": "grid-showcase-template",
        "name": "Grid Showcase",
        "description": "Mostra as primeiras 6 fotos em layout 16:9 com efeitos de movimento e transições suaves",
        "thumbnail": "/templates/grid-showcase-preview.jpg",
        "scenes": [
            {
                "id": "scene-1-grid-showcase",
                "name": "Grid Showcase",
                "type": "grid",
                "duration": 8.0,
                "max_photos": 6,
                "effects": [
                    {
                        "id": "grid-layout",
                        "type": "fade",
                        "duration": 2.0,
                        "parameters": {
                            "grid_columns": 3,
                            "grid_rows": 2,
                            "spacing": 15,
                            "fade_in": True,
                            "aspect_ratio": "16:9",
                            "layout": "grid"
                        }
                    },
                    {
                        "id": "wind-effect",
                        "type": "slide",
                        "duration": 3.0,
                        "parameters": {
                            "direction": "horizontal",
                            "intensity": 0.1,
                            "easing": "ease-in-out",
                            "wave_effect": True
                        }
                    },
                    {
                        "id": "grid-reveal",
                        "type": "fade",
                        "duration": 2.0,
                        "parameters": {
                            "reveal_type": "grid",
                            "grid_animation": True,
                            "stagger_delay": 0.2
                        }
                    }
                ],
                "order": 1
            },
            {
                "id": "scene-2-individual-showcase",
                "name": "Individual Showcase",
                "type": "zoom",
                "duration": 4.0,
                "max_photos": 6,
                "effects": [
                    {
                        "id": "individual-zoom",
                        "type": "zoom",
                        "duration": 4.0,
                        "parameters": {
                            "zoom_start": 1.0,
                            "zoom_end": 1.3,
                            "zoom_center": "center",
                            "easing": "ease-in-out"
                        }
                    },
                    {
                        "id": "smooth-transition",
                        "type": "fade",
                        "duration": 1.0,
                        "parameters": {
                            "fade_in": True,
                            "fade_out": True,
                            "cross_fade": True
                        }
                    }
                ],
                "order": 2
            }
        ],
        "total_duration": 0.0,
        "max_photos": 6,
        "background_music": "source_bg.mp3"
    },
    
    "cinematic-showcase-template": {
        "id": "cinematic-showcase-template",
        "name": "Cinematic Showcase",
        "description": "Template cinematográfico premium com múltiplas cenas, zoom lento, transições suaves e efeitos dramáticos",
        "thumbnail": "/templates/cinematic-showcase-preview.jpg",
        "scenes": [
            {
                "id": "scene-1-dramatic-opening",
                "name": "Dramatic Opening",
                "type": "fade",
                "duration": 5.0,
                "max_photos": 2,
                "effects": [
                    {
                        "id": "black-fade-in",
                        "type": "fade",
                        "duration": 2.5,
                        "parameters": {
                            "fade_in": True,
                            "fade_type": "black_fade",
                            "easing": "ease-in-out",
                            "dramatic_effect": True,
                            "cinematic_style": True
                        }
                    },
                    {
                        "id": "hero-zoom",
                        "type": "zoom",
                        "duration": 2.5,
                        "parameters": {
                            "zoom_start": 1.5,
                            "zoom_end": 1.0,
                            "zoom_center": "center",
                            "easing": "ease-out",
                            "slow_motion": True,
                            "hero_effect": True
                        }
                    },
                    {
                        "id": "vignette-effect",
                        "type": "vignette",
                        "duration": 5.0,
                        "parameters": {
                            "intensity": 0.3,
                            "radius": 0.8,
                            "softness": 0.2,
                            "cinematic_look": True
                        }
                    }
                ],
                "order": 1
            },
            {
                "id": "scene-2-elegant-grid",
                "name": "Elegant Grid",
                "type": "grid",
                "duration": 8.0,
                "max_photos": 9,
                "effects": [
                    {
                        "id": "masonry-grid",
                        "type": "fade",
                        "duration": 3.0,
                        "parameters": {
                            "grid_columns": 3,
                            "grid_rows": 3,
                            "spacing": 30,
                            "fade_in": True,
                            "stagger_delay": 0.1,
                            "easing": "ease-in-out",
                            "masonry_layout": True,
                            "elegant_animation": True
                        }
                    },
                    {
                        "id": "floating-parallax",
                        "type": "pan",
                        "duration": 5.0,
                        "parameters": {
                            "pan_start": {"x": 0, "y": 0},
                            "pan_end": {"x": 0.08, "y": -0.06},
                            "easing": "ease-in-out",
                            "parallax_effect": True,
                            "floating_motion": True,
                            "subtle_movement": True
                        }
                    },
                    {
                        "id": "pulse-glow",
                        "type": "glow",
                        "duration": 8.0,
                        "parameters": {
                            "intensity": 0.15,
                            "color": "#ffffff",
                            "pulse_rate": 2.0,
                            "soft_glow": True
                        }
                    }
                ],
                "order": 2
            },
            {
                "id": "scene-3-cinematic-zoom-sequence",
                "name": "Cinematic Zoom Sequence",
                "type": "zoom",
                "duration": 12.0,
                "max_photos": 6,
                "effects": [
                    {
                        "id": "slow-cinematic-zoom",
                        "type": "zoom",
                        "duration": 8.0,
                        "parameters": {
                            "zoom_start": 1.0,
                            "zoom_end": 2.0,
                            "zoom_center": "center",
                            "easing": "ease-in-out",
                            "slow_motion": True,
                            "cinematic_effect": True,
                            "smooth_transition": True
                        }
                    },
                    {
                        "id": "dramatic-pan",
                        "type": "pan",
                        "duration": 8.0,
                        "parameters": {
                            "pan_start": {"x": 0, "y": 0},
                            "pan_end": {"x": 0.2, "y": 0.15},
                            "easing": "ease-in-out",
                            "dramatic_movement": True,
                            "cinematic_style": True
                        }
                    },
                    {
                        "id": "depth-of-field",
                        "type": "blur",
                        "duration": 12.0,
                        "parameters": {
                            "blur_start": 0,
                            "blur_end": 0.3,
                            "focus_center": "center",
                            "depth_effect": True
                        }
                    },
                    {
                        "id": "cinematic-transition",
                        "type": "fade",
                        "duration": 4.0,
                        "parameters": {
                            "fade_in": True,
                            "fade_out": True,
                            "cross_fade": True,
                            "cinematic_style": True,
                            "smooth_easing": True
                        }
                    }
                ],
                "order": 3
            },
            {
                "id": "scene-4-ken-burns-masterpiece",
                "name": "Ken Burns Masterpiece",
                "type": "ken_burns",
                "duration": 10.0,
                "max_photos": 5,
                "effects": [
                    {
                        "id": "ken-burns-zoom",
                        "type": "zoom",
                        "duration": 10.0,
                        "parameters": {
                            "zoom_start": 1.0,
                            "zoom_end": 2.5,
                            "zoom_center": "random",
                            "easing": "ease-in-out",
                            "ken_burns_style": True,
                            "slow_motion": True,
                            "masterpiece_effect": True
                        }
                    },
                    {
                        "id": "ken-burns-pan",
                        "type": "pan",
                        "duration": 10.0,
                        "parameters": {
                            "pan_start": {"x": 0, "y": 0},
                            "pan_end": {"x": 0.25, "y": 0.2},
                            "easing": "ease-in-out",
                            "ken_burns_movement": True,
                            "smooth_trajectory": True
                        }
                    },
                    {
                        "id": "film-grain",
                        "type": "grain",
                        "duration": 10.0,
                        "parameters": {
                            "intensity": 0.1,
                            "grain_size": 0.5,
                            "film_look": True,
                            "vintage_effect": True
                        }
                    }
                ],
                "order": 4
            },
            {
                "id": "scene-5-dynamic-showcase",
                "name": "Dynamic Showcase",
                "type": "showcase",
                "duration": 8.0,
                "max_photos": 4,
                "effects": [
                    {
                        "id": "dynamic-zoom",
                        "type": "zoom",
                        "duration": 4.0,
                        "parameters": {
                            "zoom_start": 1.8,
                            "zoom_end": 1.0,
                            "zoom_center": "center",
                            "easing": "ease-out",
                            "dynamic_effect": True,
                            "smooth_reveal": True
                        }
                    },
                    {
                        "id": "color-grading",
                        "type": "color",
                        "duration": 8.0,
                        "parameters": {
                            "contrast": 1.2,
                            "saturation": 1.1,
                            "warmth": 0.1,
                            "cinematic_look": True
                        }
                    },
                    {
                        "id": "elegant-fade-out",
                        "type": "fade",
                        "duration": 4.0,
                        "parameters": {
                            "fade_out": True,
                            "elegant_style": True,
                            "easing": "ease-in-out",
                            "smooth_ending": True
                        }
                    }
                ],
                "order": 5
            },
            {
                "id": "scene-6-finale",
                "name": "Epic Finale",
                "type": "finale",
                "duration": 6.0,
                "max_photos": 3,
                "effects": [
                    {
                        "id": "epic-zoom",
                        "type": "zoom",
                        "duration": 4.0,
                        "parameters": {
                            "zoom_start": 1.2,
                            "zoom_end": 1.0,
                            "zoom_center": "center",
                            "easing": "ease-out",
                            "epic_effect": True,
                            "grand_finale": True
                        }
                    },
                    {
                        "id": "golden-hour",
                        "type": "lighting",
                        "duration": 6.0,
                        "parameters": {
                            "lighting_type": "golden_hour",
                            "intensity": 0.8,
                            "warm_tone": True,
                            "cinematic_lighting": True
                        }
                    },
                    {
                        "id": "epic-fade",
                        "type": "fade",
                        "duration": 2.0,
                        "parameters": {
                            "fade_out": True,
                            "epic_style": True,
                            "easing": "ease-in-out",
                            "memorable_ending": True
                        }
                    }
                ],
                "order": 6
            }
        ],
        "total_duration": 49.0,
        "max_photos": 9,
        "background_music": "source_bg.mp3"
    },
    
    "thumbnail-zoom-template": {
        "id": "thumbnail-zoom-template",
        "name": "Thumbnail + Zoom",
        "description": "Mostra thumbnails primeiro, depois zoom em cada foto por 6 segundos",
        "thumbnail": "/templates/thumbnail-zoom-preview.jpg",
        "scenes": [
            {
                "id": "scene-1-thumbnails",
                "name": "Thumbnails Overview",
                "type": "thumbnail",
                "duration": 3,
                "max_photos": 10,
                "effects": [
                    {
                        "id": "thumbnails-grid",
                        "type": "fade",
                        "duration": 1,
                        "parameters": {
                            "grid_columns": 3,
                            "grid_rows": 4,
                            "spacing": 20,
                            "fade_in": True
                        }
                    }
                ],
                "order": 1
            },
            {
                "id": "scene-2-zoom-sequence",
                "name": "Zoom Sequence",
                "type": "zoom",
                "duration": 6,
                "max_photos": 10,
                "effects": [
                    {
                        "id": "zoom-effect",
                        "type": "zoom",
                        "duration": 6,
                        "parameters": {
                            "zoom_start": 1,
                            "zoom_end": 1.5,
                            "zoom_center": "center",
                            "easing": "ease-in-out"
                        }
                    },
                    {
                        "id": "pan-effect",
                        "type": "pan",
                        "duration": 6,
                        "parameters": {
                            "pan_start": {
                                "x": 0,
                                "y": 0
                            },
                            "pan_end": {
                                "x": 0.1,
                                "y": 0.1
                            },
                            "easing": "ease-in-out"
                        }
                    }
                ],
                "order": 2
            }
        ],
        "total_duration": 0,
        "max_photos": 10,
        "background_music": "source_bg.mp3"
    }
}
