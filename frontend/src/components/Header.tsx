
import { Video, Sparkles } from "lucide-react";
import { ApiStatus } from "./ApiStatus";
import { LanguageSelector } from "./LanguageSelector";
import { Button } from "./ui/button";
import { i18n } from "@/lib/i18n";
import { useNavigate } from "react-router-dom";

const Header = () => {
  const navigate = useNavigate();

  return (
    <header className="relative z-10 border-b border-white/10 bg-background/80 backdrop-blur-lg">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <div 
            className="flex items-center space-x-3 cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => navigate('/')}
          >
            <div className="relative">
              <Video className="h-8 w-8 text-primary" />
              <Sparkles className="absolute -top-1 -right-1 h-4 w-4 text-accent animate-pulse" />
            </div>
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
                {i18n.t('appName')}
              </h1>
              <p className="text-xs text-muted-foreground">{i18n.t('appDescription')}</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-6">
            {/* Language Selector */}
            <div className="hidden md:block">
              <LanguageSelector />
            </div>
            
            {/* Status da API */}
            <div className="hidden md:block">
              <ApiStatus />
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
