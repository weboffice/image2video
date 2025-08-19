import { useHealthCheck } from '@/hooks/useApi';
import { Badge } from '@/components/ui/badge';
import { i18n } from '@/lib/i18n';

export const ApiStatus = () => {
  const { data: health, isLoading, error } = useHealthCheck();

  return (
    <div className="flex items-center space-x-2">
      <span className="text-xs text-muted-foreground">API:</span>
      {isLoading && (
        <Badge variant="secondary" className="text-xs px-2 py-1">
          {i18n.t('connecting')}
        </Badge>
      )}
      {error && (
        <Badge variant="destructive" className="text-xs px-2 py-1">
          {i18n.t('apiOffline')}
        </Badge>
      )}
      {health && (
        <Badge variant="default" className="text-xs px-2 py-1 bg-green-100 text-green-800 hover:bg-green-200">
          {i18n.t('apiOnline')}
        </Badge>
      )}
    </div>
  );
};
