import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { api, VideoStatusResponse, JobCreateRequest, UploadURLRequest } from '../lib/api';

// Hook para criar um novo job
export const useCreateJob = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: JobCreateRequest) => api.createJob(data),
    onSuccess: (data) => {
      toast.success(`Job criado com sucesso: ${data.code}`);
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
    onError: (error: Error) => {
      toast.error(`Erro ao criar job: ${error.message}`);
    },
  });
};

// Hook para obter status de um job
export const useJobStatus = (jobCode: string) => {
  return useQuery({
    queryKey: ['job', jobCode],
    queryFn: () => api.getJobStatus(jobCode),
    enabled: !!jobCode,
    refetchInterval: (query) => {
      // Parar polling se o job estiver completo ou com erro
      const data = query.state.data;
      if (data?.status === 'completed' || data?.status === 'error' || data?.status === 'failed') {
        return false;
      }
      // Poll a cada 5 segundos em vez de 2
      return 5000;
    },
    refetchIntervalInBackground: false,
    retry: 3,
    retryDelay: 1000,
  });
};

// Hook para obter informações completas do job (incluindo fotos)
export const useJobInfo = (jobCode: string) => {
  return useQuery({
    queryKey: ['jobInfo', jobCode],
    queryFn: () => api.getJobInfo(jobCode),
    enabled: !!jobCode,
    staleTime: 30000, // Dados considerados frescos por 30 segundos
    retry: 3,
    retryDelay: 1000,
  });
};

// Hook para iniciar processamento de um job
export const useStartJob = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (jobCode: string) => api.startJob(jobCode),
    onSuccess: (data, jobCode) => {
      toast.success(`Job ${jobCode} iniciado com sucesso`);
      queryClient.invalidateQueries({ queryKey: ['job', jobCode] });
    },
    onError: (error: Error) => {
      toast.error(`Erro ao iniciar job: ${error.message}`);
    },
  });
};

// Hook para obter URL de upload
export const useUploadURL = () => {
  return useMutation({
    mutationFn: (data: UploadURLRequest) => api.getUploadURL(data),
    onError: (error: Error) => {
      toast.error(`Erro ao obter URL de upload: ${error.message}`);
    },
  });
};

// Hook para fazer upload de arquivo
export const useUploadFile = () => {
  return useMutation({
    mutationFn: ({ uploadUrl, file }: { uploadUrl: string; file: File }) =>
      api.uploadFile(uploadUrl, file),
    onSuccess: (data) => {
      toast.success(`Arquivo enviado com sucesso (${data.bytes} bytes)`);
    },
    onError: (error: Error) => {
      toast.error(`Erro ao enviar arquivo: ${error.message}`);
    },
  });
};

// Hook para health check
export const useHealthCheck = () => {
  return useQuery({
    queryKey: ['health'],
    queryFn: () => api.healthCheck(),
    refetchInterval: (query) => {
      // Se a API estiver offline, verificar a cada 10 segundos
      if (query.state.error) {
        return 10000;
      }
      // Se a API estiver online, verificar a cada 60 segundos
      return 60000;
    },
    refetchIntervalInBackground: false,
    retry: 3,
    retryDelay: 2000,
    staleTime: 30000, // Dados considerados frescos por 30 segundos
  });
};

// Hooks para Templates
export const useTemplates = () => {
  return useQuery({
    queryKey: ['templates'],
    queryFn: api.getTemplates,
    staleTime: 5 * 60 * 1000, // 5 minutos
  });
};

export const useTemplate = (templateId: string) => {
  return useQuery({
    queryKey: ['template', templateId],
    queryFn: () => api.getTemplate(templateId),
    enabled: !!templateId,
    staleTime: 5 * 60 * 1000, // 5 minutos
  });
};

// Hooks para Vídeos
export const useCreateVideo = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: api.createVideo,
    onSuccess: (data) => {
      // Invalidate templates query to refresh data
      queryClient.invalidateQueries({ queryKey: ['templates'] });
      
      // Add the new video to cache
      queryClient.setQueryData(['video', data.job_id], data);
    },
    onError: (error: Error) => {
      console.error('❌ Erro no hook useCreateVideo:', error);
      toast.error(`Erro ao criar vídeo: ${error.message}`);
    },
  });
};

export const useVideoStatus = (jobId: string, enabled: boolean = true) => {
  return useQuery({
    queryKey: ['video-status', jobId],
    queryFn: () => api.getVideoStatus(jobId),
    enabled: enabled && !!jobId,
    refetchInterval: (query) => {
      // Parar polling se o vídeo estiver completo ou com erro
      const data = query.state.data;
      if (data?.status === 'completed' || data?.status === 'error') {
        return false;
      }
      // Poll a cada 5 segundos em vez de 2
      return 5000;
    },
    refetchIntervalInBackground: false,
    retry: 3,
    retryDelay: 1000,
  });
};

export const useStartVideoProcessing = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: api.startVideoProcessing,
    onSuccess: (data) => {
      // Invalidate video status query to refresh data
      queryClient.invalidateQueries({ queryKey: ['video-status', data.job_id] });
      toast.success('Processamento de vídeo iniciado!');
    },
    onError: (error: Error) => {
      toast.error(`Erro ao iniciar processamento: ${error.message}`);
    },
  });
};

export const useDownloadVideo = () => {
  return useMutation({
    mutationFn: api.downloadVideo,
    onSuccess: (blob, jobId) => {
      // Criar link de download
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `video_${jobId}.mp4`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      toast.success('Download iniciado!');
    },
    onError: (error: Error) => {
      toast.error(`Erro ao fazer download: ${error.message}`);
    },
  });
};

// Hook para deletar foto
export const useDeletePhoto = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ jobCode, fileId }: { jobCode: string; fileId: number }) =>
      api.deletePhoto(jobCode, fileId),
    onSuccess: (data, variables) => {
      // Invalidar queries relacionadas ao job
      queryClient.invalidateQueries({ queryKey: ['job', variables.jobCode] });
      queryClient.invalidateQueries({ queryKey: ['jobInfo', variables.jobCode] });
    },
  });
};

// Hook para reordenar foto
export const useReorderPhoto = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ jobCode, fileId, direction }: { jobCode: string; fileId: number; direction: 'up' | 'down' }) =>
      api.reorderPhoto(jobCode, fileId, direction),
    onSuccess: (data, variables) => {
      // Invalidar queries relacionadas ao job para atualizar a ordem
      queryClient.invalidateQueries({ queryKey: ['job', variables.jobCode] });
      queryClient.invalidateQueries({ queryKey: ['jobInfo', variables.jobCode] });
    },
  });
};
