
import { Job } from "../types";
import { Clock, Video, CheckCircle, AlertCircle, Upload } from "lucide-react";
import { i18n } from "@/lib/i18n";

interface ProcessingStatusProps {
  job: Job;
  className?: string;
}

const ProcessingStatus = ({ job, className = "" }: ProcessingStatusProps) => {
  const getStatusConfig = () => {
    switch (job.state) {
      case 'uploading':
        return {
          icon: Upload,
          label: i18n.t('uploadingPhotos'),
          description: i18n.t('sendingPhotosToServers'),
          className: 'status-uploading'
        };
      case 'queued':
        return {
          icon: Clock,
          label: i18n.t('inQueue'),
          description: i18n.t('waitingToBeProcessed'),
          className: 'status-processing'
        };
      case 'processing':
        return {
          icon: Video,
          label: i18n.t('creatingVideo'),
          description: i18n.t('aiCraftingMasterpiece'),
          className: 'status-processing'
        };
      case 'done':
        return {
          icon: CheckCircle,
          label: i18n.t('videoReady'),
          description: i18n.t('videoCreatedSuccessfully'),
          className: 'status-done'
        };
      case 'error':
        return {
          icon: AlertCircle,
          label: i18n.t('processingFailed'),
          description: job.errorMessage || i18n.t('somethingWentWrong'),
          className: 'status-error'
        };
      default:
        return {
          icon: Clock,
          label: i18n.t('preparing'),
          description: i18n.t('gettingEverythingReady'),
          className: 'status-processing'
        };
    }
  };

  const config = getStatusConfig();
  const Icon = config.icon;

  return (
    <div className={`glass-card p-6 text-center ${className}`}>
      <div className="flex flex-col items-center space-y-4">
        <div className={`status-badge ${config.className}`}>
          <Icon className="h-4 w-4 mr-2" />
          {config.label}
        </div>
        
        <div className="space-y-2">
          <p className="text-muted-foreground">{config.description}</p>
          
          {(job.state === 'processing' || job.state === 'uploading') && (
            <div className="w-full max-w-md">
              <div className="flex justify-between text-sm mb-1">
                <span>{i18n.t('progress')}</span>
                <span>{job.progress}%</span>
              </div>
              <div className="progress-bar h-2">
                <div 
                  className="progress-fill h-full"
                  style={{ width: `${job.progress}%` }}
                />
              </div>
            </div>
          )}
        </div>
        
        {job.state === 'processing' && (
          <div className="text-xs text-muted-foreground">
            {i18n.t('usuallyTakes30to60Seconds')}
          </div>
        )}
      </div>
    </div>
  );
};

export default ProcessingStatus;
