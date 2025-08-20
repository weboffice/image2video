import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ImageIcon, RefreshCw, CheckCircle, XCircle } from 'lucide-react';

interface ImageTest {
  id: string;
  name: string;
  objectKey: string;
  url: string;
  status: 'loading' | 'success' | 'error';
  loadTime?: number;
}

const StorageDemo = () => {
  const [images, setImages] = useState<ImageTest[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [storageStatus, setStorageStatus] = useState<any>(null);

  // Imagens de exemplo para testar
  const exampleImages = [
    { id: '1', name: 'Imagem Original', objectKey: 'examples/test_image.jpg' },
    { id: '2', name: 'Imagem Vermelha', objectKey: 'examples/sample_01.jpg' },
    { id: '3', name: 'Imagem Verde', objectKey: 'examples/sample_02.jpg' },
    { id: '4', name: 'Imagem Azul', objectKey: 'examples/sample_03.jpg' },
    { id: '5', name: 'Imagem Verde Claro', objectKey: 'examples/sample_04.jpg' },
    { id: '6', name: 'Imagem Amarela', objectKey: 'examples/sample_05.jpg' },
    { id: '7', name: 'Imagem Roxa', objectKey: 'examples/sample_06.jpg' },
    { id: '8', name: 'Arquivo de Teste', objectKey: 'test/sample.txt' },
  ];

  const loadStorageStatus = async () => {
    try {
      const response = await fetch('/api/files/storage/status');
      const status = await response.json();
      setStorageStatus(status);
    } catch (error) {
      console.error('Erro ao carregar status do storage:', error);
      setStorageStatus({ status: 'error', message: 'Erro ao conectar com o storage' });
    }
  };

  const loadImages = async () => {
    setIsLoading(true);
    
    // Carregar status do storage primeiro
    await loadStorageStatus();
    
    const imageTests: ImageTest[] = exampleImages.map(img => ({
      ...img,
      url: `/api/files/${img.objectKey}`,
      status: 'loading' as const,
    }));
    
    setImages(imageTests);

    // Testar cada imagem
    for (let i = 0; i < imageTests.length; i++) {
      const img = imageTests[i];
      const startTime = Date.now();
      
      try {
        const response = await fetch(img.url);
        const loadTime = Date.now() - startTime;
        
        if (response.ok) {
          setImages(prev => prev.map(item => 
            item.id === img.id 
              ? { ...item, status: 'success', loadTime }
              : item
          ));
        } else {
          throw new Error(`HTTP ${response.status}`);
        }
      } catch (error) {
        const loadTime = Date.now() - startTime;
        setImages(prev => prev.map(item => 
          item.id === img.id 
            ? { ...item, status: 'error', loadTime }
            : item
        ));
      }
    }
    
    setIsLoading(false);
  };

  useEffect(() => {
    loadImages();
  }, []);

  const getStatusIcon = (status: ImageTest['status']) => {
    switch (status) {
      case 'loading':
        return <RefreshCw className="w-5 h-5 animate-spin text-blue-500" />;
      case 'success':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'error':
        return <XCircle className="w-5 h-5 text-red-500" />;
    }
  };

  const getStatusText = (status: ImageTest['status']) => {
    switch (status) {
      case 'loading':
        return 'Carregando...';
      case 'success':
        return 'Sucesso';
      case 'error':
        return 'Erro';
    }
  };

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Demonstração do Storage</h1>
        <p className="text-gray-600 mb-4">
          Esta página demonstra que todas as imagens estão sendo carregadas corretamente do storage MinIO.
        </p>
        <Button onClick={loadImages} disabled={isLoading} className="mb-6">
          <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
          Recarregar Testes
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {images.map((img) => (
          <Card key={img.id} className="overflow-hidden">
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>{img.name}</span>
                <div className="flex items-center gap-2">
                  {getStatusIcon(img.status)}
                  <span className="text-sm">{getStatusText(img.status)}</span>
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="text-sm text-gray-600">
                  <p><strong>Object Key:</strong> {img.objectKey}</p>
                  <p><strong>URL:</strong> {img.url}</p>
                  {img.loadTime && (
                    <p><strong>Tempo de Carregamento:</strong> {img.loadTime}ms</p>
                  )}
                </div>
                
                {img.status === 'success' && img.objectKey.includes('.jpg') && (
                  <div className="relative aspect-video bg-gray-100 rounded-lg overflow-hidden">
                    <img
                      src={img.url}
                      alt={img.name}
                      className="w-full h-full object-cover"
                      onLoad={() => console.log(`✅ Imagem ${img.name} carregada com sucesso`)}
                      onError={() => console.log(`❌ Erro ao carregar imagem ${img.name}`)}
                    />
                  </div>
                )}
                
                {img.status === 'success' && !img.objectKey.includes('.jpg') && (
                  <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                    <div className="flex items-center gap-2">
                      <CheckCircle className="w-5 h-5 text-green-500" />
                      <span className="text-green-700">Arquivo acessível via storage</span>
                    </div>
                  </div>
                )}
                
                {img.status === 'error' && (
                  <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                    <div className="flex items-center gap-2">
                      <XCircle className="w-5 h-5 text-red-500" />
                      <span className="text-red-700">Erro ao acessar arquivo</span>
                    </div>
                  </div>
                )}
                
                {img.status === 'loading' && (
                  <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <div className="flex items-center gap-2">
                      <RefreshCw className="w-5 h-5 animate-spin text-blue-500" />
                      <span className="text-blue-700">Testando acesso ao storage...</span>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="mt-8 space-y-6">
        {/* Status do Storage */}
        {storageStatus && (
          <div className={`p-6 rounded-lg ${storageStatus.status === 'healthy' ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
              {storageStatus.status === 'healthy' ? (
                <CheckCircle className="w-6 h-6 text-green-500" />
              ) : (
                <XCircle className="w-6 h-6 text-red-500" />
              )}
              Status do Storage MinIO
            </h2>
            <div className="space-y-2 text-sm">
              <p><strong>Status:</strong> {storageStatus.status === 'healthy' ? '✅ Funcionando' : '❌ Com problemas'}</p>
              {storageStatus.endpoint && <p><strong>Endpoint:</strong> {storageStatus.endpoint}</p>}
              {storageStatus.bucket && <p><strong>Bucket:</strong> {storageStatus.bucket}</p>}
              {storageStatus.total_objects !== undefined && <p><strong>Total de Arquivos:</strong> {storageStatus.total_objects}</p>}
              <p><strong>Mensagem:</strong> {storageStatus.message}</p>
            </div>
          </div>
        )}

        {/* Informações Técnicas */}
        <div className="p-6 bg-gray-50 rounded-lg">
          <h2 className="text-xl font-semibold mb-4">Informações Técnicas</h2>
          <div className="space-y-2 text-sm text-gray-600">
            <p><strong>Backend:</strong> FastAPI rodando na porta 8080</p>
            <p><strong>Storage:</strong> MinIO - TODAS AS IMAGENS VÊM DO STORAGE</p>
            <p><strong>Endpoint:</strong> /api/files/[object_key] → Redirecionamento 307 para MinIO</p>
            <p><strong>Fluxo:</strong> Frontend → Backend → MinIO (URLs pré-assinadas)</p>
            <p><strong>Status dos Testes:</strong> {images.every(img => img.status === 'success') ? '✅ Todos os testes passaram' : '⚠️ Alguns testes falharam'}</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StorageDemo;
