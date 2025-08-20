
import { useState, useCallback, useEffect, useRef, useMemo } from "react";
import { useDropzone } from 'react-dropzone';
import { Button } from "./ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Progress } from "./ui/progress";
import { 
  Upload, 
  X, 
  GripVertical, 
  ImageIcon, 
  Sparkles, 
  Zap, 
  Camera,
  Trash2,
  CheckCircle,
  AlertCircle,
  RefreshCw,
  MoveUp,
  MoveDown,
  Clock,
  Loader2,
  List
} from "lucide-react";
import { toast } from "sonner";
import { useCreateJob, useUploadURL, useUploadFile, useDeletePhoto, useJobInfo, useReorderPhoto } from "@/hooks/useApi";
import { PhotoFile } from "@/types";
import { api } from "@/lib/api";
import { i18n } from "@/lib/i18n";
import { JobCodeDisplay } from "./JobCodeDisplay";

interface PhotoUploaderProps {
  onPhotosUploaded: (photos: PhotoFile[]) => void;
  onPhotosOrdered: (photos: PhotoFile[]) => void;
  onJobCreated?: (jobCode: string) => void;
  onNewVideo?: () => void; // Callback para iniciar novo vídeo
}

interface UploadQueueItem {
  id: string;
  fileName: string;
  status: 'waiting' | 'uploading' | 'completed' | 'error';
  progress: number;
  error?: string;
}

export const PhotoUploader = ({ onPhotosUploaded, onPhotosOrdered, onJobCreated, onNewVideo }: PhotoUploaderProps) => {
  const [isUploading, setIsUploading] = useState(false);
  const [sessionJobCode, setSessionJobCode] = useState<string | null>(null);
  const [uploadQueue, setUploadQueue] = useState<UploadQueueItem[]>([]);
  const [showUploadQueue, setShowUploadQueue] = useState(false);
  const [isRefreshingGallery, setIsRefreshingGallery] = useState(false);
  const [removingPhotoId, setRemovingPhotoId] = useState<string | null>(null);

  // Refs para scroll automático
  const galleryRef = useRef<HTMLDivElement>(null);
  const uploadQueueRef = useRef<HTMLDivElement>(null);

  // Hooks da API
  const createJob = useCreateJob();
  const uploadURL = useUploadURL();
  const uploadFile = useUploadFile();
  const deletePhoto = useDeletePhoto();
  const reorderPhoto = useReorderPhoto();
  
  // Buscar informações do job (incluindo fotos) do backend
  const { data: jobInfo, refetch: refetchJobInfo, isLoading: isLoadingJobInfo } = useJobInfo(sessionJobCode || '');

  // Função helper para gerar URL pública da imagem
  const generatePublicUrl = (objectKey: string) => {
    if (!objectKey) return '';
    // Baseado no padrão do backend: /api/files/{object_key}
    return `/api/files/${objectKey}`;
  };

  // Função helper para mapear status do backend para frontend
  const mapBackendStatusToFrontend = (backendStatus: string): 'pending' | 'uploading' | 'completed' | 'error' => {
    switch (backendStatus) {
      case 'uploaded':
        return 'completed';
      case 'pending':
        return 'pending';
      case 'uploading':
        return 'uploading';
      case 'error':
      case 'failed':
        return 'error';
      default:
        console.warn(`Status desconhecido do backend: ${backendStatus}`);
        return 'pending';
    }
  };

  // Converter PhotoInfo do backend para PhotoFile do frontend
  const photos: PhotoFile[] = useMemo(() => {
    return jobInfo?.files?.map(photoInfo => {
      // IMPORTANTE: Usar public_url do backend (URL direta do CDN) em vez de gerar
      const publicUrl = photoInfo.public_url || generatePublicUrl(photoInfo.object_key);
      const mappedStatus = mapBackendStatusToFrontend(photoInfo.status);
      
      return {
        id: photoInfo.id.toString(), // Converter number para string
        fileName: photoInfo.filename,
        fileType: photoInfo.content_type,
        uploadStatus: mappedStatus,
        orderIndex: photoInfo.order_index, // Usar o order_index do backend
        objectKey: photoInfo.object_key,
        fileId: photoInfo.id, // Usar o ID do backend
        // Campos que não vêm do backend
        file: undefined as File, // Não temos o arquivo original
        preview: publicUrl, // Usar URL direta do CDN
        imageData: publicUrl, // Usar URL direta do CDN
        uploadProgress: mappedStatus === 'completed' ? 100 : 0,
        fileSize: photoInfo.size_bytes,
        uploadUrl: publicUrl, // Usar URL direta do CDN
        error: undefined
      };
    }) || [];
  }, [jobInfo]);

  // Refs para evitar dependências desnecessárias em useEffect
  const onJobCreatedRef = useRef(onJobCreated);
  const onPhotosUploadedRef = useRef(onPhotosUploaded);
  const onPhotosOrderedRef = useRef(onPhotosOrdered);
  const createJobRef = useRef(createJob);

  // Atualizar refs quando as props mudarem
  useEffect(() => {
    onJobCreatedRef.current = onJobCreated;
    onPhotosUploadedRef.current = onPhotosUploaded;
    onPhotosOrderedRef.current = onPhotosOrdered;
    createJobRef.current = createJob;
  });



  // Restaurar sessão existente ao montar o componente (se houver)
  useEffect(() => {
    // Verificar se já existe uma sessão ativa no localStorage
    const existingJobCode = localStorage.getItem('sessionJobCode');
    
    console.log('🔍 Debug - localStorage sessionJobCode:', existingJobCode);
    
    if (existingJobCode) {
      setSessionJobCode(existingJobCode);
      console.log('🔍 Debug - setSessionJobCode chamado com:', existingJobCode);
      
      if (onJobCreatedRef.current) {
        onJobCreatedRef.current(existingJobCode);
      }
      
      console.log('🔄 Sessão restaurada:', existingJobCode);
    } else {
      console.log('💡 Nenhuma sessão existente. Sessão será criada automaticamente no primeiro upload.');
    }
  }, []); // Executar apenas uma vez ao montar o componente

  // Notificar quando as fotos mudarem (vêm do backend via useJobInfo)
  useEffect(() => {
    if (photos.length > 0 && onPhotosUploadedRef.current) {
      onPhotosUploadedRef.current(photos);
    }
  }, [photos]);

  // Configuração do dropzone
  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    console.log('📸 Arquivos aceitos:', acceptedFiles.length);
    
    let currentJobCode = sessionJobCode;
    
    // Se não há sessão ativa, criar uma automaticamente antes do upload
    if (!currentJobCode) {
      console.log('🔄 Criando sessão automaticamente antes do upload...');
      try {
        const jobResult = await createJob.mutateAsync({});
        currentJobCode = jobResult.code;
        console.log('🔍 Debug - Nova sessão criada:', currentJobCode);
        setSessionJobCode(currentJobCode);
        console.log('🔍 Debug - setSessionJobCode chamado durante upload com:', currentJobCode);
        
        if (onJobCreatedRef.current) {
          onJobCreatedRef.current(currentJobCode);
        }

        // Salvar no localStorage
        localStorage.setItem('sessionJobCode', currentJobCode);
        console.log('🔍 Debug - sessionJobCode salvo no localStorage:', currentJobCode);
        
        toast.success(`${i18n.t('sessionStarted')}: ${currentJobCode}`);
        console.log('✅ Sessão criada automaticamente:', currentJobCode);
      } catch (error) {
        console.error('❌ Erro ao criar sessão automaticamente:', error);
        toast.error(i18n.t('sessionNotInitialized'));
        return;
      }
    }

    // Adicionar arquivos à fila de upload
    const newQueueItems: UploadQueueItem[] = acceptedFiles.map(file => ({
      id: `${Date.now()}-${Math.random()}`,
      fileName: file.name,
      status: 'waiting' as const,
      progress: 0
    }));

    setUploadQueue(prev => [...prev, ...newQueueItems]);
    setShowUploadQueue(true);
    setIsUploading(true);
    
    // Scroll automático para a área de upload/galeria quando upload iniciar
    setTimeout(() => {
      // Priorizar scroll para upload queue se estiver visível
      if (uploadQueueRef.current && showUploadQueue) {
        uploadQueueRef.current.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'start' 
        });
      } 
      // Caso contrário, scroll para galeria se houver fotos
      else if (galleryRef.current && totalPhotos > 0) {
        galleryRef.current.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'start' 
        });
      }
      // Se não houver fotos ainda, scroll para onde a galeria aparecerá
      else {
        // Scroll para o final da página onde a galeria aparecerá
        window.scrollTo({ 
          top: document.body.scrollHeight, 
          behavior: 'smooth' 
        });
      }
    }, 150); // Pequeno delay para garantir que o DOM foi atualizado
    
    try {
      for (let i = 0; i < acceptedFiles.length; i++) {
        const file = acceptedFiles[i];
        const queueItem = newQueueItems[i];
        
        try {
          // Atualizar status para uploading
          setUploadQueue(prev => prev.map(item => 
            item.id === queueItem.id 
              ? { ...item, status: 'uploading' as const, progress: 10 }
              : item
          ));

          // 1. Obter URL de upload
          const urlResponse = await uploadURL.mutateAsync({
            filename: file.name,
            content_type: file.type,
            job_code: currentJobCode
          });

          // Atualizar progresso
          setUploadQueue(prev => prev.map(item => 
            item.id === queueItem.id 
              ? { ...item, progress: 50 }
              : item
          ));

          // 2. Fazer upload do arquivo
          await uploadFile.mutateAsync({
            uploadUrl: urlResponse.upload_url,
            file: file
          });

          // Marcar como concluído
          setUploadQueue(prev => prev.map(item => 
            item.id === queueItem.id 
              ? { ...item, status: 'completed' as const, progress: 100 }
              : item
          ));

          // Recarregar galeria imediatamente após cada upload
          setIsRefreshingGallery(true);
          try {
            await refetchJobInfo();
          } finally {
            setIsRefreshingGallery(false);
          }

          console.log(`✅ Arquivo ${file.name} enviado com sucesso`);
        } catch (error) {
          console.error(`❌ Erro ao enviar ${file.name}:`, error);
          
          // Marcar como erro
          setUploadQueue(prev => prev.map(item => 
            item.id === queueItem.id 
              ? { ...item, status: 'error' as const, error: error instanceof Error ? error.message : 'Erro desconhecido' }
              : item
          ));
          
          toast.error(`Erro ao enviar ${file.name}`);
        }
      }

      // Contar sucessos após todos os uploads
      const successCount = newQueueItems.filter(item => {
        const queueItem = uploadQueue.find(q => q.id === item.id);
        return queueItem?.status === 'completed';
      }).length;
      
      if (successCount > 0) {
        toast.success(`${successCount} foto(s) enviada(s) com sucesso!`);
      }
    } catch (error) {
      console.error('Erro geral no upload:', error);
      toast.error(i18n.t('errorUploadingPhotos'));
    } finally {
      setIsUploading(false);
    }
  }, [sessionJobCode, createJob, uploadURL, uploadFile, refetchJobInfo, onJobCreatedRef, uploadQueue]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png', '.gif', '.webp']
    },
    multiple: true
  });

  // Função para remover foto
  const handleRemovePhoto = async (photoId: string) => {
    const photoToRemove = photos.find(p => p.id === photoId);
    if (!photoToRemove) {
      toast.error(i18n.t('photoNotFound'));
      return;
    }

    if (!sessionJobCode) {
      toast.error(i18n.t('sessionNotInitialized'));
      return;
    }

    // Definir qual foto está sendo removida
    setRemovingPhotoId(photoId);

    try {
      // Se a foto foi enviada, tentar deletar do servidor
      if (photoToRemove.objectKey) {
        await deletePhoto.mutateAsync({
          jobCode: sessionJobCode,
          fileId: photoToRemove.fileId || 0
        });
      }

      // Refetch das informações do job para atualizar a lista de fotos
      await refetchJobInfo();
      
      toast.success(i18n.t('photoRemovedSuccess'));
    } catch (error) {
      console.error('Erro ao remover foto:', error);
      toast.error(i18n.t('errorRemovingPhoto'));
    } finally {
      // Limpar o estado de remoção
      setRemovingPhotoId(null);
    }
  };

  const handleMoveUp = async (photoId: string) => {
    if (!sessionJobCode) {
      toast.error(i18n.t('sessionNotInitialized'));
      return;
    }

    try {
      const photo = photos.find(p => p.id === photoId);
      if (!photo) {
        toast.error('Foto não encontrada');
        return;
      }

      const result = await reorderPhoto.mutateAsync({
        jobCode: sessionJobCode,
        fileId: photo.fileId,
        direction: 'up'
      });

      if (result.moved) {
        toast.success('Foto movida para cima');
        await refetchJobInfo(); // Atualizar a lista
      } else {
        toast.info('Foto já está na primeira posição');
      }
    } catch (error) {
      console.error('Erro ao mover foto para cima:', error);
      toast.error('Erro ao reordenar foto');
    }
  };

  const handleMoveDown = async (photoId: string) => {
    if (!sessionJobCode) {
      toast.error(i18n.t('sessionNotInitialized'));
      return;
    }

    try {
      const photo = photos.find(p => p.id === photoId);
      if (!photo) {
        toast.error('Foto não encontrada');
        return;
      }

      const result = await reorderPhoto.mutateAsync({
        jobCode: sessionJobCode,
        fileId: photo.fileId,
        direction: 'down'
      });

      if (result.moved) {
        toast.success('Foto movida para baixo');
        await refetchJobInfo(); // Atualizar a lista
      } else {
        toast.info('Foto já está na última posição');
      }
    } catch (error) {
      console.error('Erro ao mover foto para baixo:', error);
      toast.error('Erro ao reordenar foto');
    }
  };



  // Função para iniciar novo vídeo
  const handleNewVideo = () => {
    setSessionJobCode(null);
    localStorage.removeItem('sessionJobCode');
    
    if (onNewVideo) {
      onNewVideo();
    }
  };

  const completedPhotos = photos.filter(p => p.uploadStatus === 'completed').length;
  const totalPhotos = photos.length;

  return (
    <div className="space-y-6">
      {/* Fixed Upload Status */}
      {isUploading && (
        <div className="fixed top-4 right-4 z-50 bg-white border border-blue-200 rounded-lg shadow-lg p-4 min-w-64">
          <div className="flex items-center gap-3">
            <Loader2 className="w-5 h-5 animate-spin text-blue-500" />
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-900">
                Enviando fotos...
              </p>
              <p className="text-xs text-gray-600">
                {uploadQueue.filter(item => item.status === 'completed').length} de {uploadQueue.length} concluídos
              </p>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowUploadQueue(true)}
              className="h-8 w-8 p-0"
            >
              <List className="w-4 h-4" />
            </Button>
          </div>
          
          {/* Mini Progress Bar */}
          <div className="mt-2">
            <Progress 
              value={(uploadQueue.filter(item => item.status === 'completed').length / uploadQueue.length) * 100} 
              className="h-1"
            />
          </div>
        </div>
      )}
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-800">
            {i18n.t('uploadPhotos')}
          </h3>
          <p className="text-sm text-gray-600">
            {totalPhotos > 0 
              ? `${completedPhotos} ${i18n.t('of')} ${totalPhotos} ${i18n.t('photosUploaded')}`
              : i18n.t('dragAndDropPhotos')
            }
          </p>
        </div>
        
        {/* Upload Queue Button */}
        {uploadQueue.length > 0 && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowUploadQueue(!showUploadQueue)}
            className="flex items-center gap-2"
          >
            <List className="w-4 h-4" />
            Fila ({uploadQueue.length})
            {uploadQueue.some(item => item.status === 'uploading') && (
              <Loader2 className="w-4 h-4 animate-spin" />
            )}
          </Button>
        )}
      </div>

      {/* Upload Queue Window */}
      {showUploadQueue && uploadQueue.length > 0 && (
        <Card ref={uploadQueueRef} className="border-blue-200 bg-blue-50">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium text-blue-800">
                Fila de Uploads
              </CardTitle>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowUploadQueue(false)}
                className="h-6 w-6 p-0 text-blue-600 hover:text-blue-800"
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="space-y-2 max-h-40 overflow-y-auto">
              {uploadQueue.map((item) => (
                <div key={item.id} className="flex items-center gap-3 p-2 bg-white rounded-md border">
                  {/* Status Icon */}
                  <div className="flex-shrink-0">
                    {item.status === 'waiting' && <Clock className="w-4 h-4 text-gray-400" />}
                    {item.status === 'uploading' && <Loader2 className="w-4 h-4 animate-spin text-blue-500" />}
                    {item.status === 'completed' && <CheckCircle className="w-4 h-4 text-green-500" />}
                    {item.status === 'error' && <AlertCircle className="w-4 h-4 text-red-500" />}
                  </div>
                  
                  {/* File Info */}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {item.fileName}
                    </p>
                    {item.status === 'error' && item.error && (
                      <p className="text-xs text-red-600 truncate">
                        {item.error}
                      </p>
                    )}
                  </div>
                  
                  {/* Progress */}
                  <div className="flex-shrink-0 w-16">
                    {item.status === 'uploading' && (
                      <Progress value={item.progress} className="h-2" />
                    )}
                    {item.status === 'completed' && (
                      <Badge variant="secondary" className="text-xs bg-green-100 text-green-800">
                        100%
                      </Badge>
                    )}
                    {item.status === 'error' && (
                      <Badge variant="destructive" className="text-xs">
                        Erro
                      </Badge>
                    )}
                    {item.status === 'waiting' && (
                      <Badge variant="outline" className="text-xs">
                        Aguardando
                      </Badge>
                    )}
                  </div>
                </div>
              ))}
            </div>
            
            {/* Queue Actions */}
            <div className="flex justify-between items-center mt-3 pt-3 border-t">
              <div className="text-xs text-gray-600">
                {uploadQueue.filter(item => item.status === 'completed').length} de {uploadQueue.length} concluídos
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setUploadQueue(prev => prev.filter(item => item.status !== 'completed'))}
                className="text-xs h-6 px-2"
                disabled={!uploadQueue.some(item => item.status === 'completed')}
              >
                Limpar Concluídos
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Session Info - Mostrar ID da sessão e botão Nova Sessão sempre que houver sessão */}
      {sessionJobCode && (
        <>
          {/* Debug info */}
          {(() => {
            console.log('🔍 Debug - sessionJobCode:', sessionJobCode, 'totalPhotos:', totalPhotos);
            console.log('🔍 Debug - Renderizando JobCodeDisplay!');
            return null;
          })()}
          
          {/* Debug visual temporário */}
          <div className="bg-yellow-200 p-2 mb-2 rounded">
            <p className="text-xs">DEBUG: Tentando renderizar JobCodeDisplay com sessionJobCode: {sessionJobCode}</p>
          </div>
          
          <JobCodeDisplay
            jobCode={sessionJobCode}
            status="active"
            photoCount={totalPhotos}
            onNewVideo={handleNewVideo}
          />
        </>
      )}

      {/* Dropzone - Sempre visível */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-6 text-center transition-all duration-300 cursor-pointer ${
          isDragActive
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
        } ${totalPhotos > 0 ? 'mb-6' : 'p-8'}`}
      >
        <input {...getInputProps()} />
        <div className="space-y-3">
          <div className="flex justify-center">
            <div className="relative">
              <Camera className={`${totalPhotos > 0 ? 'w-8 h-8' : 'w-12 h-12'} text-gray-400`} />
              <Sparkles className="absolute -top-1 -right-1 w-4 h-4 text-blue-500 animate-pulse" />
            </div>
          </div>
          <div>
            <p className={`${totalPhotos > 0 ? 'text-base' : 'text-lg'} font-medium text-gray-700`}>
              {totalPhotos === 0 
                ? (isDragActive ? i18n.t('dragAndDropPhotos') : i18n.t('dragAndDropPhotos'))
                : (isDragActive ? i18n.t('dropToAddMorePhotos') : i18n.t('clickOrDragToAddMore'))
              }
            </p>
            <p className="text-sm text-gray-500 mt-1">
              {totalPhotos === 0 ? i18n.t('orClickToSelect') : i18n.t('youCanAddMorePhotos')}
            </p>
          </div>
        </div>
      </div>

      {/* Loading State */}
      {isLoadingJobInfo && sessionJobCode && (
        <div className="flex justify-center items-center p-8">
          <RefreshCw className="w-6 h-6 mr-2 animate-spin text-blue-600" />
          <span className="text-gray-600">Carregando fotos...</span>
        </div>
      )}

      {/* Gallery Refresh Indicator */}
      {isRefreshingGallery && !isLoadingJobInfo && (
        <div className="flex justify-center items-center p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <RefreshCw className="w-4 h-4 mr-2 animate-spin text-blue-600" />
          <span className="text-sm text-blue-700">Atualizando galeria...</span>
        </div>
      )}

      {/* Photo List */}
      {totalPhotos > 0 && !isLoadingJobInfo && (
        <div ref={galleryRef} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {photos.map((photo, index) => (
              <Card key={photo.id} className="relative group">
                <CardContent className="p-4">
                  {/* Photo Preview */}
                  <div className="relative aspect-square bg-gray-100 rounded-lg overflow-hidden mb-3">
                    {photo.imageData || photo.file ? (
                      <img
                        src={photo.imageData || URL.createObjectURL(photo.file)}
                        alt={photo.fileName || 'Foto'}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          console.error('Erro ao carregar imagem:', photo.fileName, e);
                        }}
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center bg-gray-200">
                        <ImageIcon className="w-12 h-12 text-gray-400" />
                        <span className="text-xs text-gray-500 ml-2">Sem imagem</span>
                      </div>
                    )}
                    
                    {/* Status Overlay */}
                    <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 transition-all duration-300 flex items-center justify-center">
                      {photo.uploadStatus === 'completed' && (
                        <CheckCircle className="w-8 h-8 text-green-500 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                      )}
                      {photo.uploadStatus === 'error' && (
                        <AlertCircle className="w-8 h-8 text-red-500 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                      )}
                      {photo.uploadStatus === 'uploading' && (
                        <RefreshCw className="w-8 h-8 text-blue-500 animate-spin opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                      )}
                    </div>

                    {/* Remove Loading Overlay */}
                    {removingPhotoId === photo.id && (
                      <div className="absolute inset-0 bg-black bg-opacity-60 flex items-center justify-center z-10">
                        <div className="bg-white rounded-lg p-4 flex flex-col items-center shadow-lg">
                          <Loader2 className="w-8 h-8 text-red-500 animate-spin mb-2" />
                          <span className="text-sm font-medium text-gray-800">Removendo...</span>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Photo Info */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-medium text-gray-700 truncate">
                        {photo.fileName || 'Foto sem nome'}
                      </p>
                      <Badge
                        variant={
                          photo.uploadStatus === 'completed' ? 'default' :
                          photo.uploadStatus === 'error' ? 'destructive' :
                          photo.uploadStatus === 'uploading' ? 'secondary' :
                          'outline'
                        }
                        className="text-xs"
                      >
                        {photo.uploadStatus === 'completed' ? i18n.t('success') :
                         photo.uploadStatus === 'error' ? i18n.t('error') :
                         photo.uploadStatus === 'uploading' ? i18n.t('loading') :
                         'pending'}
                      </Badge>
                    </div>

                    {/* Progress Bar */}
                    {photo.uploadStatus === 'uploading' && (
                      <Progress value={photo.uploadProgress || 0} className="h-2" />
                    )}

                    {/* Action Buttons */}
                    <div className="flex items-center justify-between">
                      <div className="flex space-x-1">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleMoveUp(photo.id)}
                          disabled={index === 0}
                          className="w-8 h-8 p-0"
                        >
                          <MoveUp className="w-3 h-3" />
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleMoveDown(photo.id)}
                          disabled={index === photos.length - 1}
                          className="w-8 h-8 p-0"
                        >
                          <MoveDown className="w-3 h-3" />
                        </Button>
                      </div>
                      
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleRemovePhoto(photo.id)}
                        disabled={removingPhotoId === photo.id}
                        className="w-8 h-8 p-0 text-red-500 hover:text-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {removingPhotoId === photo.id ? (
                          <Loader2 className="w-3 h-3 animate-spin" />
                        ) : (
                          <Trash2 className="w-3 h-3" />
                        )}
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Status de upload */}
          {isUploading && (
            <div className="flex justify-center items-center p-4 bg-blue-50 rounded-lg">
              <RefreshCw className="w-4 h-4 mr-2 animate-spin text-blue-600" />
              <span className="text-blue-700">{i18n.t('loading')}...</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default PhotoUploader;
