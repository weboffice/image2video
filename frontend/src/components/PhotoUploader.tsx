
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
  MoveDown
} from "lucide-react";
import { toast } from "sonner";
import { useCreateJob, useUploadURL, useUploadFile, useDeletePhoto, useJobInfo, useReorderPhoto } from "@/hooks/useApi";
import { PhotoFile } from "@/types";
import { api } from "@/lib/api";
import { i18n } from "@/lib/i18n";

interface PhotoUploaderProps {
  onPhotosUploaded: (photos: PhotoFile[]) => void;
  onPhotosOrdered: (photos: PhotoFile[]) => void;
  onJobCreated?: (jobCode: string) => void;
  onNewVideo?: () => void; // Callback para iniciar novo vídeo
}

export const PhotoUploader = ({ onPhotosUploaded, onPhotosOrdered, onJobCreated, onNewVideo }: PhotoUploaderProps) => {
  const [isUploading, setIsUploading] = useState(false);
  const [sessionJobCode, setSessionJobCode] = useState<string | null>(null);

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
      // Gerar URL pública baseada no object_key
      const publicUrl = generatePublicUrl(photoInfo.object_key);
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
        preview: publicUrl, // Usar a URL pública gerada
        imageData: publicUrl, // Usar a URL pública gerada
        uploadProgress: mappedStatus === 'completed' ? 100 : 0,
        fileSize: photoInfo.size_bytes,
        uploadUrl: publicUrl, // Usar a URL pública gerada
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
    
    if (existingJobCode) {
      setSessionJobCode(existingJobCode);
      
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
        setSessionJobCode(currentJobCode);
        
        if (onJobCreatedRef.current) {
          onJobCreatedRef.current(currentJobCode);
        }

        // Salvar no localStorage
        localStorage.setItem('sessionJobCode', currentJobCode);
        
        toast.success(`${i18n.t('sessionStarted')}: ${currentJobCode}`);
        console.log('✅ Sessão criada automaticamente:', currentJobCode);
      } catch (error) {
        console.error('❌ Erro ao criar sessão automaticamente:', error);
        toast.error(i18n.t('sessionNotInitialized'));
        return;
      }
    }

    // Upload imediato dos arquivos
    setIsUploading(true);
    
    try {
      for (const file of acceptedFiles) {
        try {
          // 1. Obter URL de upload
          const urlResponse = await uploadURL.mutateAsync({
            filename: file.name,
            content_type: file.type,
            job_code: currentJobCode
          });

          // 2. Fazer upload do arquivo
          await uploadFile.mutateAsync({
            uploadUrl: urlResponse.upload_url,
            file: file
          });

          console.log(`✅ Arquivo ${file.name} enviado com sucesso`);
        } catch (error) {
          console.error(`❌ Erro ao enviar ${file.name}:`, error);
          toast.error(`Erro ao enviar ${file.name}`);
        }
      }

      // 3. Refetch das informações do job para atualizar a lista de fotos
      await refetchJobInfo();
      
      toast.success(`${acceptedFiles.length} foto(s) enviada(s) com sucesso!`);
    } catch (error) {
      console.error('Erro geral no upload:', error);
      toast.error(i18n.t('errorUploadingPhotos'));
    } finally {
      setIsUploading(false);
    }
  }, [sessionJobCode, createJob, uploadURL, uploadFile, refetchJobInfo, onJobCreatedRef]);

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
        
        {totalPhotos > 0 && (
          <Button
            variant="outline"
            size="sm"
            onClick={handleNewVideo}
            className="text-xs"
          >
            {i18n.t('newSessionStarted')}
          </Button>
        )}
      </div>

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

      {/* Photo List */}
      {totalPhotos > 0 && !isLoadingJobInfo && (
        <div className="space-y-4">
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
                        className="w-8 h-8 p-0 text-red-500 hover:text-red-700"
                      >
                        <Trash2 className="w-3 h-3" />
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
