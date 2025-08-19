
export interface Job {
  code: string;
  templateId: string;
  state: 'created' | 'uploading' | 'queued' | 'processing' | 'done' | 'error' | 'expired';
  progress: number;
  errorCode?: string;
  errorMessage?: string;
  createdAt: string;
  updatedAt: string;
  expiresAt: string;
  resultUrl?: string;
}

export interface Asset {
  jobCode: string;
  objectKey: string;
  originalFilename: string;
  contentType: string;
  sizeBytes: number;
  orderIndex: number;
  uploadProgress?: number;
  uploadStatus?: 'pending' | 'uploading' | 'completed' | 'error';
  file?: File;
}

export interface Template {
  id: string;
  name: string;
  description: string;
  constraints: {
    minImages: number;
    maxImages: number;
    aspectRatio?: string;
  };
  outputSpecs: {
    resolution: string;
    frameRate: number;
  };
  musicPolicy: 'default' | 'none' | 'user';
  previewUrl?: string;
}

export interface UploadUrlResponse {
  url: string;
  objectKey: string;
  publicUrl: string;
}

export interface PhotoFile {
  id: string;
  file: File;
  preview: string;
  uploadStatus: 'pending' | 'uploading' | 'completed' | 'error';
  uploadProgress?: number;
  error?: string;
  uploadUrl?: string;
  objectKey?: string;
  orderIndex: number;
  // Dados para persistência no localStorage
  imageData?: string; // Data URL da imagem
  fileName?: string; // Nome do arquivo
  fileType?: string; // Tipo do arquivo
  fileSize?: number; // Tamanho do arquivo em bytes
  // Dados do backend
  fileId?: number; // ID do arquivo no backend
}
