// Configuração base da API
// Em desenvolvimento, usar proxy do Vite (vazio = mesma origem)
// Em produção, usar a URL completa da API
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

// Tipos para as respostas da API
export interface JobResponse {
  code: string;
  status: string;
  progress: number;
  created_at: string;
  updated_at: string;
}

export interface JobInfo extends JobResponse {
  files: PhotoInfo[];
}

export interface UploadURLRequest {
  filename: string;
  content_type: string;
  job_code: string;
}

export interface UploadURLResponse {
  upload_url: string;
  object_key: string;
  public_url: string;
}

export interface PhotoInfo {
  id: number;
  filename: string;
  content_type: string;
  size_bytes: number;
  object_key: string;
  status: string;
  order_index: number;
  created_at: string;
}

export interface DeletePhotoResponse {
  message: string;
  deleted_file_id: number;
  deleted_object_key: string;
}

export interface ReorderResponse {
  message: string;
  moved: boolean;
  file_id: number;
  new_order?: number;
}

export interface JobCreateRequest {
  template_id?: string;
}

// Interfaces para templates
export interface Template {
  id: string;
  name: string;
  description: string;
  thumbnail: string;
  scenes: Scene[];
  totalDuration: number;
  maxPhotos: number;
}

export interface Scene {
  id: string;
  name: string;
  type: string;
  duration: number;
  maxPhotos: number;
  effects: SceneEffect[];
  order: number;
}

export interface SceneEffect {
  id: string;
  type: string;
  duration: number;
  parameters: Record<string, unknown>;
}

export interface VideoConfig {
  templateId: string;
  photos: PhotoConfig[];
  outputFormat: 'mp4' | 'mov' | 'avi';
  resolution: '720p' | '1080p' | '4k';
  fps: 24 | 30 | 60;
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

export interface VideoCreateResponse {
  job_id: string;  // Backend retorna job_id, não jobId
  status: string;
  estimated_duration: number;
  template: Template;
  message: string;
}

export interface VideoStatusResponse {
  jobId: string;  // Mantém jobId para compatibilidade com o frontend
  status: string;
  progress: number;
  estimated_duration: number;
  outputPath?: string;
  error?: string;
  template?: {
    id: string;
    name: string;
    description: string;
    thumbnail: string;
    scenes: Scene[];
    total_duration: number;
    max_photos: number;
  };
}

// Função utilitária para fazer requisições
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

// Funções da API
export const api = {
  // Jobs
  createJob: (data: JobCreateRequest): Promise<JobResponse> =>
    apiRequest<JobResponse>('/api/jobs', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // Obter status de um job
  getJobStatus: (jobCode: string): Promise<JobResponse> =>
    apiRequest<JobResponse>(`/api/jobs/${jobCode}`),

  // Obter informações completas de um job (incluindo fotos)
  getJobInfo: (jobCode: string): Promise<JobInfo> =>
    apiRequest<JobInfo>(`/api/jobs/${jobCode}`),

  // Iniciar processamento de um job
  startJob: (jobCode: string): Promise<{ message: string }> =>
    apiRequest<{ message: string }>(`/api/jobs/${jobCode}/start`, {
      method: 'POST',
    }),

  // Obter URL de upload
  getUploadURL: (data: UploadURLRequest): Promise<UploadURLResponse> =>
    apiRequest<UploadURLResponse>('/api/jobs/upload-url', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // Obter URL de arquivo do MinIO
  getFileURL: (objectKey: string): string => {
    return `${API_BASE_URL}/api/files/${objectKey}`;
  },

  // Obter informações de uma foto
  getPhotoInfo: (photoId: string): Promise<PhotoInfo> =>
    apiRequest<PhotoInfo>(`/api/photos/${photoId}`),

  // Deletar uma foto
  deletePhoto: (jobCode: string, fileId: number): Promise<DeletePhotoResponse> =>
    apiRequest<DeletePhotoResponse>(`/api/jobs/${jobCode}/files/${fileId}`, {
      method: 'DELETE',
    }),

  // Reordenar uma foto
  reorderPhoto: (jobCode: string, fileId: number, direction: 'up' | 'down'): Promise<ReorderResponse> =>
    apiRequest<ReorderResponse>(`/api/jobs/${jobCode}/files/${fileId}/reorder?direction=${direction}`, {
      method: 'PUT',
    }),

  // Fazer upload de arquivo
  uploadFile: async (uploadUrl: string, file: File): Promise<{ message: string; bytes: number }> => {
    const response = await fetch(uploadUrl, {
      method: 'PUT',
      body: file,
      headers: {
        'Content-Type': file.type,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Upload failed! status: ${response.status}`);
    }

    return response.json();
  },

  // Health check
  healthCheck: (): Promise<{ status: string }> =>
    apiRequest<{ status: string }>('/health'),
  
  // Templates
  getTemplates: async (): Promise<{ templates: Template[] }> => {
    return apiRequest<{ templates: Template[] }>('/api/templates', { method: 'GET' });
  },

  getTemplate: async (templateId: string): Promise<Template> => {
    return apiRequest<Template>(`/api/templates/${templateId}`, { method: 'GET' });
  },
  
  // Videos
  createVideo: async (config: VideoConfig): Promise<VideoCreateResponse> => {
    console.log('🔍 createVideo - Config recebida:', config);
    console.log('🔍 createVideo - JSON stringified:', JSON.stringify(config, null, 2));
    
    return apiRequest<VideoCreateResponse>('/api/videos/create', {
      method: 'POST',
      body: JSON.stringify(config)
    });
  },

  getVideoStatus: async (jobId: string): Promise<VideoStatusResponse> => {
    return apiRequest<VideoStatusResponse>(`/api/videos/${jobId}/status`, { method: 'GET' });
  },

  startVideoProcessing: async (jobId: string): Promise<{ message: string; job_id: string; status: string }> => {
    return apiRequest<{ message: string; job_id: string; status: string }>('/api/videos/' + jobId + '/process', {
      method: 'POST'
    });
  },

  downloadVideo: async (jobId: string): Promise<Blob> => {
    const response = await fetch(API_BASE_URL + '/api/videos/' + jobId + '/download');
    if (!response.ok) {
      throw new Error('Erro ao fazer download do vídeo');
    }
    return response.blob();
  },
};

export default api;
