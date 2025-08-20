export interface Scene {
  id: string;
  name: string;
  type: 'thumbnail' | 'zoom' | 'transition' | 'grid';
  duration: number; // em segundos
  maxPhotos: number;
  effects: SceneEffect[];
  order: number;
}

export interface SceneEffect {
  id: string;
  type: 'zoom' | 'pan' | 'fade' | 'slide' | 'grid' | 'wind' | 'reveal';
  duration: number;
  parameters: Record<string, any>;
}

export interface Template {
  id: string;
  name: string;
  description: string;
  thumbnail: string;
  scenes: Scene[];
  totalDuration: number;
  maxPhotos: number;
  max_photos?: number; // Backend retorna snake_case
}

export interface VideoConfig {
  templateId: string;
  photos: PhotoConfig[];
  outputFormat: 'mp4' | 'mov' | 'avi';
  resolution: '720p' | '1080p' | '4k';
  fps: 24 | 30 | 60;
  backgroundAudio?: boolean; // Opcional, padrão true
  useMoviePy?: boolean; // Opcional, padrão true (MoviePy como principal)
}

export interface PhotoConfig {
  id: string;
  filePath: string;
  order: number;
  sceneAssignments: SceneAssignment[];
}

export interface SceneAssignment {
  sceneId: string;
  startTime: number;
  duration: number;
  effects: SceneEffect[];
}

// Novos tipos para efeitos específicos
export interface GridEffectParameters {
  gridColumns: number;
  gridRows: number;
  spacing: number;
  aspectRatio: '16:9' | '4:3' | '1:1';
  layout: 'grid' | 'masonry';
  fadeIn: boolean;
}

export interface WindEffectParameters {
  direction: 'horizontal' | 'vertical' | 'diagonal';
  intensity: number;
  easing: string;
  waveEffect: boolean;
}

export interface RevealEffectParameters {
  revealType: 'grid' | 'fade' | 'slide';
  gridAnimation: boolean;
  staggerDelay: number;
}
