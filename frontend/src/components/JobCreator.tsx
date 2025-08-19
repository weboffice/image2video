import { useState } from "react";
import { Button } from "./ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Sparkles, Copy, Check } from "lucide-react";
import { useCreateJob } from "@/hooks/useApi";
import { toast } from "sonner";
import { i18n } from "@/lib/i18n";

interface JobCreatorProps {
  onJobCreated?: (jobCode: string) => void;
}

export const JobCreator = ({ onJobCreated }: JobCreatorProps) => {
  const [jobCode, setJobCode] = useState<string>("");
  const [copied, setCopied] = useState(false);
  const createJob = useCreateJob();

  const handleCreateJob = async () => {
    try {
      const result = await createJob.mutateAsync({});
      const newJobCode = result.code;
      setJobCode(newJobCode);
      
      if (onJobCreated) {
        onJobCreated(newJobCode);
      }
      
      toast.success(`${i18n.t('sessionStarted')}: ${newJobCode}`);
    } catch (error) {
      console.error("Erro ao criar job:", error);
      toast.error(i18n.t('error'));
    }
  };

  const handleCopyJobCode = async () => {
    if (jobCode) {
      await navigator.clipboard.writeText(jobCode);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
      toast.success(i18n.t('copied'));
    }
  };

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-blue-500" />
          {i18n.t('createNewJob')}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {!jobCode ? (
          <Button
            onClick={handleCreateJob}
            disabled={createJob.isPending}
            className="w-full"
          >
            {createJob.isPending ? i18n.t('loading') : i18n.t('createNewJob')}
          </Button>
        ) : (
          <div className="space-y-3">
            <div>
              <Label htmlFor="jobCode" className="text-sm font-medium">
                {i18n.t('jobCode')}
              </Label>
              <div className="flex gap-2 mt-1">
                <Input
                  id="jobCode"
                  value={jobCode}
                  readOnly
                  className="font-mono text-sm"
                />
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleCopyJobCode}
                  className="px-3"
                >
                  {copied ? (
                    <Check className="w-4 h-4" />
                  ) : (
                    <Copy className="w-4 h-4" />
                  )}
                </Button>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
