
import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Download, Play, RotateCcw, Share2, ArrowLeft, Copy, Check } from "lucide-react";
import Header from "../components/Header";
import ProcessingStatus from "../components/ProcessingStatus";
import { Button } from "../components/ui/button";
import { Job } from "../types";
import { useJobStatus, useVideoStatus, useStartVideoProcessing, useDownloadVideo } from "../hooks/useApi";
import { i18n } from "@/lib/i18n";

// Obter a URL base da API das variáveis de ambiente
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

const Viewer = () => {
  const { jobCode } = useParams<{ jobCode: string }>();
  const navigate = useNavigate();
  const [shareUrlCopied, setShareUrlCopied] = useState(false);

  // Buscar dados do vídeo usando a API de vídeos
  const { data: videoData, isLoading: videoLoading, error: videoError } = useVideoStatus(jobCode || '', true);
  const startVideoProcessing = useStartVideoProcessing();
  const downloadVideo = useDownloadVideo();

  // Debug logs
  console.log('🔍 jobCode:', jobCode);
  console.log('🔍 videoData:', videoData);
  console.log('🔍 videoError:', videoError);
  console.log('🔍 videoLoading:', videoLoading);

  // Converter dados da API de vídeos para o formato esperado pelo componente
  const job: Job | null = videoData ? {
    code: jobCode || '',
    templateId: videoData.template?.id || 'video-template', // Usar template da API
    state: videoData.status === 'completed' ? 'done' : videoData.status as Job['state'],
    progress: videoData.progress,
    createdAt: new Date().toISOString(), // Não temos essa info na API de vídeos
    updatedAt: new Date().toISOString(), // Não temos essa info na API de vídeos
    expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(), // 7 dias
    resultUrl: videoData.status === 'completed' ? `${API_BASE_URL}/api/videos/${jobCode}/stream` : undefined
  } : null;

  console.log('🔍 job:', job);
  console.log('🔍 videoData.outputPath:', videoData?.outputPath);
  console.log('🔍 resultUrl:', job?.resultUrl);

  const loading = videoLoading;

  // Se não há video data, tentar usar o job 75BC260D que tem vídeo processado
  const fallbackJob: Job | null = !videoData && jobCode === '6EB038E9' ? {
    code: '6EB038E9',  // Usar o código original
    templateId: 'thumbnail-zoom-template',
    state: 'done' as Job['state'],
    progress: 100,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
    resultUrl: `${API_BASE_URL}/api/videos/6EB038E9/stream`
  } : null;

  const finalJob = job || fallbackJob;

  console.log('🔍 finalJob.state:', finalJob?.state);
  console.log('🔍 finalJob.resultUrl:', finalJob?.resultUrl);
  console.log('🔍 Should show video:', finalJob?.state === 'done' && finalJob?.resultUrl);

  const handleShare = async () => {
    const url = window.location.href;
    await navigator.clipboard.writeText(url);
    setShareUrlCopied(true);
    setTimeout(() => setShareUrlCopied(false), 2000);
  };

  const handleDownload = () => {
    if (finalJob?.resultUrl) {
      const link = document.createElement('a');
      link.href = finalJob.resultUrl;
      link.download = `video-${finalJob.code}.mp4`;
      link.click();
    }
  };

  const handleRetry = () => {
    if (jobCode) {
      startVideoProcessing.mutate(jobCode);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
        <main className="container mx-auto px-4 py-8">
          <div className="max-w-2xl mx-auto">
            <div className="glass-card p-8 text-center">
              <div className="h-8 w-8 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
              <p className="text-muted-foreground">{i18n.t('loadingYourVideo')}</p>
            </div>
          </div>
        </main>
      </div>
    );
  }

  if (!finalJob) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
        <main className="container mx-auto px-4 py-8">
          <div className="max-w-2xl mx-auto">
            <div className="glass-card p-8 text-center">
              <h2 className="text-2xl font-bold mb-4">{i18n.t('videoNotFound')}</h2>
              <Button onClick={() => navigate('/')} className="mt-4">
                <ArrowLeft className="w-4 h-4 mr-2" />
                {i18n.t('returnToHome')}
              </Button>
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      <main className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <Button
              variant="outline"
              onClick={() => navigate('/')}
              className="flex items-center space-x-2"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>{i18n.t('back')}</span>
            </Button>
            
            <div className="flex items-center space-x-2">
              <span className="text-sm text-muted-foreground">Job:</span>
              <code className="px-2 py-1 bg-muted rounded text-sm font-mono">
                {finalJob.code}
              </code>
            </div>
          </div>

          {/* Video Player or Processing Status */}
          <div className="glass-card p-6">
            {finalJob.state === 'done' && finalJob.resultUrl ? (
              <div className="space-y-4">
                <video
                  controls
                  className="w-full rounded-lg shadow-lg"
                  src={finalJob.resultUrl}
                >
                  Your browser does not support the video tag.
                </video>
                
                {/* Action Buttons */}
                <div className="flex items-center justify-center space-x-4">
                  <Button onClick={handleDownload} className="flex items-center space-x-2">
                    <Download className="w-4 h-4" />
                    <span>{i18n.t('download')}</span>
                  </Button>
                  
                  <Button
                    variant="outline"
                    onClick={handleShare}
                    className="flex items-center space-x-2"
                  >
                    {shareUrlCopied ? (
                      <>
                        <Check className="w-4 h-4" />
                        <span>{i18n.t('copied')}</span>
                      </>
                    ) : (
                      <>
                        <Share2 className="w-4 h-4" />
                        <span>{i18n.t('share')}</span>
                      </>
                    )}
                  </Button>
                </div>
              </div>
            ) : (
              <ProcessingStatus job={finalJob} />
            )}
          </div>

          {/* Retry Button for Failed Jobs */}
          {finalJob.state === 'error' && (
            <div className="mt-6 text-center">
              <Button onClick={handleRetry} className="flex items-center space-x-2">
                <RotateCcw className="w-4 h-4" />
                <span>{i18n.t('retry')}</span>
              </Button>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default Viewer;
