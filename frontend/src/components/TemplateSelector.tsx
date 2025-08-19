
import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Check, Image, Sparkles, Zap } from 'lucide-react';
import { Template } from '@/types/template';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { calculateTotalDuration } from '@/data/templates';
import { i18n } from '@/lib/i18n';

interface TemplateSelectorProps {
  onTemplateSelect: (template: Template) => void;
  selectedTemplate: Template | null;
  photoCount: number;
}

export default function TemplateSelector({
  onTemplateSelect,
  selectedTemplate,
  photoCount
}: TemplateSelectorProps) {
  const [hoveredTemplate, setHoveredTemplate] = useState<string | null>(null);

  // Buscar templates do backend
  const { data: templatesData, isLoading, error } = useQuery({
    queryKey: ['templates'],
    queryFn: api.getTemplates,
    staleTime: 5 * 60 * 1000, // 5 minutos
  });

  // Usar templates do backend ou fallback para templates estáticos
  const templates = templatesData?.templates || [];

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="flex items-center space-x-2">
          <Sparkles className="w-5 h-5 text-blue-500 animate-pulse" />
          <h3 className="text-lg font-semibold text-gray-800">{i18n.t('loadingTemplates')}</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="animate-pulse">
              <CardHeader>
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
              </CardHeader>
              <CardContent>
                <div className="h-32 bg-gray-200 rounded"></div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <div className="flex items-center space-x-2">
          <Sparkles className="w-5 h-5 text-red-500" />
          <h3 className="text-lg font-semibold text-gray-800">{i18n.t('errorLoadingTemplates')}</h3>
        </div>
        <p className="text-red-600">{i18n.t('errorLoadingTemplatesMessage')}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center space-x-2">
        <Sparkles className="w-5 h-5 text-blue-500 animate-pulse" />
        <h3 className="text-lg font-semibold text-gray-800">{i18n.t('chooseTemplateTitle')}</h3>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {templates.map((template: Template, index: number) => {
          const totalDuration = calculateTotalDuration(template, photoCount);
          const isSelected = selectedTemplate?.id === template.id;
          const isHovered = hoveredTemplate === template.id;

          return (
            <Card
              key={template.id}
              className={`cursor-pointer transition-all duration-500 ease-out transform ${
                isSelected
                  ? 'ring-2 ring-blue-500 bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-200 scale-105 shadow-xl'
                  : 'hover:shadow-2xl hover:border-gray-300 hover:scale-102'
              } ${
                isHovered && !isSelected 
                  ? 'ring-1 ring-gray-300 shadow-lg' 
                  : ''
              } animate-fade-in-up`}
              style={{
                animationDelay: `${index * 0.1}s`,
                transform: isHovered ? 'translateY(-2px)' : 'translateY(0)'
              }}
              onClick={() => onTemplateSelect(template)}
              onMouseEnter={() => setHoveredTemplate(template.id)}
              onMouseLeave={() => setHoveredTemplate(null)}
            >
              {/* Animated Border Effect */}
              <div className={`absolute inset-0 rounded-lg transition-all duration-700 ${
                isSelected 
                  ? 'bg-gradient-to-r from-blue-400 via-purple-500 to-pink-500 opacity-20 animate-pulse' 
                  : 'bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 opacity-0'
              }`} />
              
              <div className="relative z-10">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base font-semibold transition-all duration-300">
                      {template.name}
                    </CardTitle>
                    {isSelected && (
                      <div className="flex items-center space-x-1">
                        <Check className="w-4 h-4 text-blue-600 animate-bounce" />
                        <Sparkles className="w-3 h-3 text-yellow-500 animate-pulse" />
                      </div>
                    )}
                  </div>
                </CardHeader>

                <CardContent className="space-y-3 pt-0">
                  {/* Enhanced Preview Placeholder */}
                  <div className="relative aspect-video bg-gradient-to-br from-gray-100 via-gray-200 to-gray-300 rounded-lg overflow-hidden group">
                    {/* Animated Background */}
                    <div className="absolute inset-0 bg-gradient-to-br from-blue-100 via-purple-100 to-pink-100 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                    
                    {/* Floating Icons */}
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="flex space-x-2">
                        {template.scenes.slice(0, 3).map((scene, index) => (
                          <div
                            key={scene.id}
                            className={`w-8 h-8 rounded-lg flex items-center justify-center transition-all duration-500 ${
                              scene.type === 'thumbnail' || scene.type === 'grid'
                                ? 'bg-blue-500 text-white' 
                                : scene.type === 'zoom'
                                ? 'bg-green-500 text-white'
                                : 'bg-purple-500 text-white'
                            }`}
                            style={{
                              animationDelay: `${index * 0.1}s`,
                              transform: isHovered ? 'scale(1.05)' : 'scale(1)'
                            }}
                          >
                            <Image className="w-4 h-4" />
                          </div>
                        ))}
                      </div>
                    </div>
                    
                    {/* Enhanced Scene Indicators */}
                    <div className="absolute bottom-1 left-1 flex gap-0.5">
                      {template.scenes.map((scene, index) => (
                        <div
                          key={scene.id}
                          className={`w-1.5 h-1.5 rounded-full transition-all duration-300 ${
                            scene.type === 'thumbnail' || scene.type === 'grid'
                              ? 'bg-gradient-to-r from-blue-500 to-blue-600' 
                              : scene.type === 'zoom'
                              ? 'bg-gradient-to-r from-green-500 to-green-600'
                              : 'bg-gradient-to-r from-purple-500 to-purple-600'
                          } ${
                            isHovered ? 'scale-125 animate-pulse' : ''
                          }`}
                          style={{
                            animationDelay: `${index * 0.1}s`
                          }}
                        />
                      ))}
                    </div>
                  </div>

                  {/* Template Description */}
                  <p className="text-xs text-gray-600 leading-relaxed">
                    {template.description}
                  </p>

                  {/* Template Stats */}
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <span>{i18n.t('duration')}: {Math.round(totalDuration)}s</span>
                    <span>{i18n.t('photos')}: {photoCount}/{template.maxPhotos || template.max_photos}</span>
                  </div>
                </CardContent>
              </div>
            </Card>
          );
        })}
      </div>

      {/* Selected Template Details */}
      {selectedTemplate && (
        <div className="mt-6 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-200">
          <div className="flex items-center space-x-2 mb-3">
            <Check className="w-5 h-5 text-blue-600" />
            <span className="font-semibold text-blue-800">{i18n.t('selectedTemplate')}: {selectedTemplate.name}</span>
          </div>
          
          <div className="space-y-2">
            <p className="text-sm text-blue-700">{selectedTemplate.description}</p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
              <div>
                <h4 className="font-medium text-blue-800 mb-2">{i18n.t('scenes')}:</h4>
                <div className="space-y-1">
                  {selectedTemplate.scenes.map((scene, index) => (
                    <div key={scene.id} className="flex items-center space-x-2 text-sm">
                      <div className={`w-2 h-2 rounded-full ${
                        scene.type === 'thumbnail' || scene.type === 'grid'
                          ? 'bg-blue-500' 
                          : scene.type === 'zoom'
                          ? 'bg-green-500'
                          : 'bg-purple-500'
                      }`} />
                      <span className="text-blue-700">{scene.name}</span>
                      <span className="text-blue-500">({scene.duration}s)</span>
                    </div>
                  ))}
                </div>
              </div>
              
              <div>
                <h4 className="font-medium text-blue-800 mb-2">{i18n.t('information')}:</h4>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-blue-700">{i18n.t('totalDuration')}:</span>
                    <span className="text-blue-600 font-medium">{formatDuration(calculateTotalDuration(selectedTemplate, photoCount))}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-blue-700">{i18n.t('photos')}:</span>
                    <span className="text-blue-600 font-medium">{photoCount}/{selectedTemplate.maxPhotos || selectedTemplate.max_photos}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function formatDuration(seconds: number): string {
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
}
