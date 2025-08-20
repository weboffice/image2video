
import { useState } from "react";
import { Button } from "./ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Copy, Check, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { i18n } from "@/lib/i18n";

interface JobCodeDisplayProps {
  jobCode: string;
  status?: 'active' | 'completed' | 'error';
  photoCount?: number;
  onNewVideo?: () => void;
}

export const JobCodeDisplay = ({ 
  jobCode, 
  status = 'active', 
  photoCount = 0,
  onNewVideo 
}: JobCodeDisplayProps) => {
  const [copied, setCopied] = useState(false);

  const handleCopyJobCode = async () => {
    await navigator.clipboard.writeText(jobCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    toast.success(i18n.t('copied'));
  };

  const getStatusConfig = () => {
    switch (status) {
      case 'active':
        return {
          label: i18n.t('apiOnline'),
          className: 'bg-gradient-to-r from-green-100 to-green-200 text-green-800 animate-pulse'
        };
      case 'completed':
        return {
          label: i18n.t('success'),
          className: 'bg-gradient-to-r from-blue-100 to-blue-200 text-blue-800'
        };
      case 'error':
        return {
          label: i18n.t('error'),
          className: 'bg-gradient-to-r from-red-100 to-red-200 text-red-800'
        };
      default:
        return {
          label: i18n.t('loading'),
          className: 'bg-gradient-to-r from-gray-100 to-gray-200 text-gray-800'
        };
    }
  };

  const statusConfig = getStatusConfig();

  return (
    <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200 animate-fade-in-up shadow-lg">
      <CardContent className="py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex items-center space-x-2">
              <Sparkles className="w-4 h-4 text-yellow-500 animate-pulse" />
              <div>
                <p className="text-xs font-medium text-blue-900">{i18n.t('sessionStarted')}</p>
                <p className="text-sm font-bold text-blue-700">{jobCode}</p>
              </div>
            </div>
            <div className="text-xs text-blue-600 font-medium">
              {photoCount} {i18n.t('photos')}
            </div>
          </div>
          <div className="flex gap-2">
            <Badge className={`text-xs ${statusConfig.className}`}>
              {statusConfig.label}
            </Badge>
            <Button
              variant="outline"
              size="sm"
              onClick={handleCopyJobCode}
              className="text-blue-600 hover:text-blue-700 hover:bg-blue-50 text-xs h-7 px-2 transition-all duration-300 hover:scale-105"
            >
              {copied ? (
                <Check className="w-3 h-3" />
              ) : (
                <Copy className="w-3 h-3" />
              )}
            </Button>
            {onNewVideo && (
              <Button
                variant="outline"
                size="sm"
                onClick={onNewVideo}
                className="text-red-600 hover:text-red-700 hover:bg-red-50 text-xs h-7 px-2 transition-all duration-300 hover:scale-105"
              >
                {i18n.t('newSession')}
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
