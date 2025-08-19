import { useState, useEffect } from "react";
import { Button } from "./ui/button";
import { Globe } from "lucide-react";
import { i18n, Language } from "@/lib/i18n";

export const LanguageSelector = () => {
  const [currentLanguage, setCurrentLanguage] = useState<Language>(i18n.getLanguage());

  // Sincronizar o estado com o i18n quando o componente montar
  useEffect(() => {
    setCurrentLanguage(i18n.getLanguage());
  }, []);

  const handleLanguageChange = (language: Language) => {
    i18n.setLanguage(language);
    setCurrentLanguage(language);
  };

  return (
    <div className="flex items-center space-x-2">
      <Globe className="w-4 h-4 text-muted-foreground" />
      <div className="flex border rounded-md overflow-hidden">
        <Button
          variant={currentLanguage === 'en' ? 'default' : 'ghost'}
          size="sm"
          onClick={() => handleLanguageChange('en')}
          className="px-3 py-1 text-xs rounded-none border-0"
        >
          EN
        </Button>
        <Button
          variant={currentLanguage === 'pt' ? 'default' : 'ghost'}
          size="sm"
          onClick={() => handleLanguageChange('pt')}
          className="px-3 py-1 text-xs rounded-none border-0"
        >
          PT
        </Button>
      </div>
    </div>
  );
};
