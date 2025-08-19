// Tipos para a API do backend

export interface Job {
  code: string;
  status: 'created' | 'processing' | 'completed' | 'failed';
  progress: number;
  created_at: string;
  updated_at: string;
}

export interface JobCreateRequest {
  template_id?: string;
}

export interface JobResponse {
  code: string;
  status: string;
  progress: number;
  created_at: string;
  updated_at: string;
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

export interface UploadFile {
  id: number;
  job_id: number;
  filename: string;
  content_type: string;
  object_key: string;
  status: 'pending' | 'uploaded' | 'failed';
  size_bytes?: number;
  created_at: string;
}

export interface HealthResponse {
  status: string;
}

export interface ApiError {
  detail: string;
  status_code?: number;
}

// Tipos para eventos de streaming
export interface JobStatusEvent {
  status: string;
  progress?: number;
  message?: string;
}
