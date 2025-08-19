import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Header from "../components/Header";
import PhotoUploader from "../components/PhotoUploader";
import TemplateSelector from "../components/TemplateSelector";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Sparkles, ArrowRight, Video, Settings, CheckCircle } from "lucide-react";
import { toast } from "sonner";
import { PhotoFile } from "@/types";
import { Template } from "@/types/template";
import { calculateTotalDuration } from "@/data/templates";
import { useCreateVideo, useJobInfo } from "@/hooks/useApi";
import { VideoConfig, PhotoConfig } from "@/lib/api";
import { i18n } from "@/lib/i18n";

type AppStep = 'upload' | 'template' | 'create';

const Index = () => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentJobCode, setCurrentJobCode] = useState<string | null>(null);
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);
  const [currentStep, setCurrentStep] = useState<AppStep>('upload');
  const [videoJobId, setVideoJobId] = useState<string | null>(null);
  const navigate = useNavigate();

  // Hooks
  const createVideo = useCreateVideo();
  const { data: jobInfo } = useJobInfo(currentJobCode || '');

  // Função helper para gerar URL pública da imagem
  const generatePublicUrl = (objectKey: string) => {
    if (!objectKey) return '';
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

  // Derivar photos do backend (similar ao PhotoUploader)
  const photos: PhotoFile[] = jobInfo?.files?.map(photoInfo => {
    const mappedStatus = mapBackendStatusToFrontend(photoInfo.status);
    return {
      id: photoInfo.id.toString(),
      fileName: photoInfo.filename,
      fileType: photoInfo.content_type,
      uploadStatus: mappedStatus,
      orderIndex: photoInfo.order_index,
      objectKey: photoInfo.object_key,
      fileId: photoInfo.id,
      file: undefined as File,
      preview: generatePublicUrl(photoInfo.object_key),
      imageData: generatePublicUrl(photoInfo.object_key),
      uploadProgress: mappedStatus === 'completed' ? 100 : 0,
      fileSize: photoInfo.size_bytes,
      uploadUrl: generatePublicUrl(photoInfo.object_key),
      error: undefined
    };
  }) || [];

  const handlePhotosUploaded = (uploadedPhotos: PhotoFile[]) => {
    // Não precisamos mais atualizar o estado local - as fotos vêm do backend via useJobInfo
    console.log('📸 Fotos enviadas:', uploadedPhotos.length);
  };

  const handlePhotosOrdered = (orderedPhotos: PhotoFile[]) => {
    // Não precisamos mais atualizar o estado local - as fotos vêm do backend via useJobInfo
    console.log('🔄 Fotos reordenadas:', orderedPhotos.length);
  };

  const handleJobCreated = (jobCode: string) => {
    setCurrentJobCode(jobCode);
    // Toast é exibido no PhotoUploader para evitar duplicação
  };

  const handleNewVideo = () => {
    setCurrentJobCode(null);
    setIsProcessing(false);
    setSelectedTemplate(null);
    setCurrentStep('upload');
    setVideoJobId(null);
    toast.success(i18n.t('newSessionStarted'));
  };

  const handleTemplateSelect = (template: Template) => {
    setSelectedTemplate(template);
    setCurrentStep('create');
    toast.success(`${i18n.t('templateSelectedToast')} "${template.name}"`);
  };

  const handleCreateVideo = async () => {
    if (photos.length === 0) {
      toast.error(i18n.t('noPhotosSelected'));
      return;
    }

    if (photos.some(p => p.uploadStatus !== 'completed')) {
      toast.error(i18n.t('waitForUpload'));
      return;
    }

    if (!currentJobCode) {
      toast.error(i18n.t('noJobCreated'));
      return;
    }

    if (!selectedTemplate) {
      toast.error(i18n.t('noTemplateSelected'));
      return;
    }

    setIsProcessing(true);
    
    try {
      // Preparar configuração do vídeo
      const maxPhotos = selectedTemplate.max_photos || selectedTemplate.maxPhotos || 10;
      const limitedPhotos = photos.slice(0, maxPhotos);
      
      console.log('🔍 Template selecionado:', {
        id: selectedTemplate.id,
        name: selectedTemplate.name,
        maxPhotos: selectedTemplate.maxPhotos,
        max_photos: selectedTemplate.max_photos,
        maxPhotosFallback: maxPhotos
      });
      
      console.log('🔍 Limitando fotos:', {
        totalPhotos: photos.length,
        maxPhotos: maxPhotos,
        limitedPhotos: limitedPhotos.length
      });
      
      const photoConfigs: PhotoConfig[] = limitedPhotos.map(photo => ({
        id: String(photo.id), // Garantir que é string
        filePath: photo.objectKey || '',
        order: photo.orderIndex,
        sceneAssignments: [] // Será preenchido pelo backend
      }));

      const videoConfig: VideoConfig = {
        templateId: selectedTemplate.id,
        photos: photoConfigs,
        outputFormat: 'mp4',
        resolution: '1080p',
        fps: 30
      };

      console.log('🎬 Criando vídeo com configuração:', videoConfig);

      // Criar vídeo
      console.log('🔄 Chamando createVideo.mutateAsync...');
      const result = await createVideo.mutateAsync(videoConfig);
      
      console.log('✅ Resposta da API:', result);
      console.log('🔍 Tipo do result:', typeof result);
      console.log('🔍 result.job_id:', result.job_id);
      console.log('🔍 Chaves do result:', Object.keys(result));
      console.log('🔍 result.status:', result.status);
      console.log('🔍 result.message:', result.message);
      
      if (!result.job_id) {
        toast.error(i18n.t('jobIdNotReturned'));
        console.error('Resultado da API sem job_id:', result);
        return;
      }
      
      setVideoJobId(result.job_id);
      toast.success(`${i18n.t('videoCreatedSuccess')}: ${result.job_id}`);
      
      console.log('🔄 Redirecionando para:', `/viewer/${result.job_id}`);
      
      // Navegar para a página de visualização
      setTimeout(() => {
        navigate(`/viewer/${result.job_id}`);
      }, 1000);
      
    } catch (error) {
      console.error('❌ Erro ao criar vídeo:', error);
      toast.error(i18n.t('errorCreatingVideo'));
    } finally {
      setIsProcessing(false);
    }
  };

  const canProceedToTemplate = photos.length > 0 && photos.every(p => p.uploadStatus === 'completed');
  const canCreateVideo = selectedTemplate && canProceedToTemplate;

  // Debug logs
  console.log('🔍 Debug canProceedToTemplate:');
  console.log('   photos.length:', photos.length);
  console.log('   photos uploadStatus:', photos.map(p => ({ id: p.id, uploadStatus: p.uploadStatus })));
  console.log('   every completed:', photos.every(p => p.uploadStatus === 'completed'));
  console.log('   canProceedToTemplate:', canProceedToTemplate);
  console.log('🔍 Debug createVideo:');
  console.log('   isProcessing:', isProcessing);
  console.log('   createVideo.isPending:', createVideo.isPending);
  console.log('   createVideo.isError:', createVideo.isError);
  console.log('   createVideo.error:', createVideo.error);

  const formatDuration = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <Header />
      
      <main className="container mx-auto px-4 py-6">
        <div className="max-w-5xl mx-auto">
          {/* Hero Section - Mais compacto */}
          <div className="text-center mb-8">
            <div className="flex items-center justify-center mb-3">
              <Sparkles className="w-6 h-6 text-purple-500 mr-2" />
              <h1 className="text-3xl font-bold text-gray-900">
                {i18n.t('heroTitle')}
              </h1>
            </div>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              {i18n.t('heroSubtitle')}
            </p>
          </div>

          {/* Progress Steps - Mais compacto */}
          <div className="mb-6">
            <div className="flex items-center justify-center space-x-3">
              <div className={`flex items-center space-x-2 ${currentStep === 'upload' ? 'text-blue-600' : 'text-gray-400'}`}>
                <div className={`w-6 h-6 rounded-full flex items-center justify-center text-sm ${
                  currentStep === 'upload' ? 'bg-blue-600 text-white' : 'bg-gray-200'
                }`}>
                  {currentStep === 'upload' ? '1' : <CheckCircle className="w-4 h-4" />}
                </div>
                <span className="font-medium text-sm">{i18n.t('stepUpload')}</span>
              </div>
              
              <div className={`w-12 h-1 ${currentStep === 'template' || currentStep === 'create' ? 'bg-blue-600' : 'bg-gray-200'}`}></div>
              
              <div className={`flex items-center space-x-2 ${currentStep === 'template' ? 'text-blue-600' : currentStep === 'create' ? 'text-green-600' : 'text-gray-400'}`}>
                <div className={`w-6 h-6 rounded-full flex items-center justify-center text-sm ${
                  currentStep === 'template' ? 'bg-blue-600 text-white' : 
                  currentStep === 'create' ? 'bg-green-600 text-white' : 'bg-gray-200'
                }`}>
                  {currentStep === 'create' ? <CheckCircle className="w-4 h-4" /> : '2'}
                </div>
                <span className="font-medium text-sm">{i18n.t('stepTemplate')}</span>
              </div>
              
              <div className={`w-12 h-1 ${currentStep === 'create' ? 'bg-green-600' : 'bg-gray-200'}`}></div>
              
              <div className={`flex items-center space-x-2 ${currentStep === 'create' ? 'text-green-600' : 'text-gray-400'}`}>
                <div className={`w-6 h-6 rounded-full flex items-center justify-center text-sm ${
                  currentStep === 'create' ? 'bg-green-600 text-white' : 'bg-gray-200'
                }`}>
                  3
                </div>
                <span className="font-medium text-sm">{i18n.t('stepCreate')}</span>
              </div>
            </div>
          </div>

          {/* Step 1: Upload de Fotos - Mais compacto */}
          {currentStep === 'upload' && (
            <div className="space-y-4">
              <div className="bg-white rounded-xl shadow-lg p-4">
                <PhotoUploader
                  onPhotosUploaded={handlePhotosUploaded}
                  onPhotosOrdered={handlePhotosOrdered}
                  onJobCreated={handleJobCreated}
                  onNewVideo={handleNewVideo}
                />
              </div>

              {/* Botão para próxima etapa - Mais compacto */}
              {canProceedToTemplate && (
                <div className="text-center">
                  <Button
                    size="lg"
                    onClick={() => setCurrentStep('template')}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 text-base font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all duration-300"
                  >
                    <Settings className="w-4 h-4 mr-2" />
                    {i18n.t('chooseTemplate')}
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                  
                  <p className="text-xs text-gray-600 mt-2">
                    {photos.length} {i18n.t('photosReady')}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Step 2: Seleção de Template - Mais compacto */}
          {currentStep === 'template' && (
            <div className="space-y-4">
              <div className="bg-white rounded-xl shadow-lg p-4">
                <TemplateSelector
                  selectedTemplate={selectedTemplate}
                  onTemplateSelect={handleTemplateSelect}
                  photoCount={photos.length}
                />
              </div>

              {/* Botão voltar - Mais compacto */}
              <div className="text-center">
                <Button
                  variant="outline"
                  onClick={() => setCurrentStep('upload')}
                  className="mr-4 text-sm"
                >
                  {i18n.t('backToUpload')}
                </Button>
              </div>
            </div>
          )}

          {/* Step 3: Criar Vídeo - Mais compacto */}
          {currentStep === 'create' && selectedTemplate && (
            <div className="space-y-4">
              {/* Resumo do Vídeo - Mais compacto */}
              <Card className="bg-gradient-to-r from-green-50 to-blue-50 border-green-200">
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg text-green-800">
                    {i18n.t('videoSummary')}
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <h4 className="font-semibold text-green-800 mb-1 text-sm">{i18n.t('stepTemplate')}</h4>
                      <p className="text-green-700 text-sm">{selectedTemplate.name}</p>
                      <p className="text-xs text-green-600">{selectedTemplate.description}</p>
                    </div>
                    
                    <div>
                      <h4 className="font-semibold text-green-800 mb-1 text-sm">{i18n.t('photos')}</h4>
                      <p className="text-green-700 text-sm">{photos.length} {i18n.t('photos').toLowerCase()}</p>
                      <p className="text-xs text-green-600">Job: {currentJobCode}</p>
                    </div>
                    
                    <div>
                      <h4 className="font-semibold text-green-800 mb-1 text-sm">{i18n.t('duration')}</h4>
                      <p className="text-green-700 text-sm">
                        {formatDuration(calculateTotalDuration(selectedTemplate, photos.length))}
                      </p>
                      <p className="text-xs text-green-600">MP4 • 1080p • 30fps</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Botão Criar Vídeo - Mais compacto */}
              <div className="text-center">
                <Button
                  size="lg"
                  onClick={handleCreateVideo}
                  disabled={isProcessing || createVideo.isPending}
                  className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white px-6 py-3 text-base font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all duration-300"
                >
                  {isProcessing || createVideo.isPending ? (
                    i18n.t('creatingVideo')
                  ) : (
                    <>
                      <Video className="w-4 h-4 mr-2" />
                      {i18n.t('createVideo')}
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </>
                  )}
                </Button>
                
                <p className="text-xs text-gray-600 mt-2">
                  {i18n.t('videoWillBeCreated')} "{selectedTemplate.name}"
                </p>
              </div>

              {/* Botões de navegação - Mais compactos */}
              <div className="text-center space-x-3">
                <Button
                  variant="outline"
                  onClick={() => setCurrentStep('upload')}
                  className="text-sm"
                >
                  {i18n.t('backToUpload')}
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setCurrentStep('template')}
                  className="text-sm"
                >
                  {i18n.t('changeTemplate')}
                </Button>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default Index;
