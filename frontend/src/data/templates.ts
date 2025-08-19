import { Template, Scene } from '@/types/template';

// Templates estáticos como fallback (serão substituídos pelos templates do backend)
export const DEFAULT_TEMPLATE: Template = {
  id: 'thumbnail-zoom-template',
  name: 'Thumbnail + Zoom',
  description: 'Mostra thumbnails primeiro, depois zoom em cada foto por 6 segundos',
  thumbnail: '/templates/thumbnail-zoom-preview.jpg',
  maxPhotos: 10,
  totalDuration: 0,
  scenes: [
    {
      id: 'scene-1-thumbnails',
      name: 'Thumbnails Overview',
      type: 'thumbnail',
      duration: 3,
      maxPhotos: 10,
      order: 1,
      effects: [
        {
          id: 'thumbnails-grid',
          type: 'fade',
          duration: 1,
          parameters: {
            gridColumns: 3,
            gridRows: 4,
            spacing: 20,
            fadeIn: true
          }
        }
      ]
    },
    {
      id: 'scene-2-zoom-sequence',
      name: 'Zoom Sequence',
      type: 'zoom',
      duration: 6,
      maxPhotos: 10,
      order: 2,
      effects: [
        {
          id: 'zoom-effect',
          type: 'zoom',
          duration: 6,
          parameters: {
            zoomStart: 1.0,
            zoomEnd: 1.5,
            zoomCenter: 'center',
            easing: 'ease-in-out'
          }
        },
        {
          id: 'pan-effect',
          type: 'pan',
          duration: 6,
          parameters: {
            panStart: { x: 0, y: 0 },
            panEnd: { x: 0.1, y: 0.1 },
            easing: 'ease-in-out'
          }
        }
      ]
    }
  ]
};

export const GRID_SHOWCASE_TEMPLATE: Template = {
  id: 'grid-showcase-template',
  name: 'Grid Showcase',
  description: 'Mostra as primeiras 6 fotos em layout 16:9 com efeitos de movimento e transições suaves',
  thumbnail: '/templates/grid-showcase-preview.jpg',
  maxPhotos: 6,
  totalDuration: 0,
  scenes: [
    {
      id: 'scene-1-grid-showcase',
      name: 'Grid Showcase',
      type: 'grid',
      duration: 8,
      maxPhotos: 6,
      order: 1,
      effects: [
        {
          id: 'grid-layout',
          type: 'fade',
          duration: 2,
          parameters: {
            gridColumns: 3,
            gridRows: 2,
            spacing: 15,
            fadeIn: true,
            aspectRatio: '16:9',
            layout: 'grid'
          }
        },
        {
          id: 'wind-effect',
          type: 'slide',
          duration: 3,
          parameters: {
            direction: 'horizontal',
            intensity: 0.1,
            easing: 'ease-in-out',
            waveEffect: true
          }
        },
        {
          id: 'grid-reveal',
          type: 'fade',
          duration: 2,
          parameters: {
            revealType: 'grid',
            gridAnimation: true,
            staggerDelay: 0.2
          }
        }
      ]
    },
    {
      id: 'scene-2-individual-showcase',
      name: 'Individual Showcase',
      type: 'zoom',
      duration: 4,
      maxPhotos: 6,
      order: 2,
      effects: [
        {
          id: 'individual-zoom',
          type: 'zoom',
          duration: 4,
          parameters: {
            zoomStart: 1.0,
            zoomEnd: 1.3,
            zoomCenter: 'center',
            easing: 'ease-in-out'
          }
        },
        {
          id: 'smooth-transition',
          type: 'fade',
          duration: 1,
          parameters: {
            fadeIn: true,
            fadeOut: true,
            crossFade: true
          }
        }
      ]
    }
  ]
};

// Templates estáticos como fallback
export const AVAILABLE_TEMPLATES: Template[] = [
  DEFAULT_TEMPLATE,
  GRID_SHOWCASE_TEMPLATE,
];

export const getTemplateById = (id: string): Template | undefined => {
  return AVAILABLE_TEMPLATES.find(template => template.id === id);
};

export const calculateTotalDuration = (template: Template, photoCount: number): number => {
  let totalDuration = 0;
  
  template.scenes.forEach(scene => {
    if (scene.type === 'thumbnail' || scene.type === 'grid') {
      // Cena de thumbnails ou grid tem duração fixa
      totalDuration += scene.duration;
    } else if (scene.type === 'zoom') {
      // Cena de zoom: duração por foto
      const photosInScene = Math.min(photoCount, scene.maxPhotos);
      totalDuration += photosInScene * scene.duration;
    }
  });
  
  return totalDuration;
};
