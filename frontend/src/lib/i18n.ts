// Internationalization system for translating the frontend from Portuguese to English

export const translations = {
  en: {
    // Common
    loading: "Loading...",
    error: "Error",
    success: "Success",
    cancel: "Cancel",
    save: "Save",
    delete: "Delete",
    edit: "Edit",
    back: "Back",
    next: "Next",
    previous: "Previous",
    close: "Close",
    confirm: "Confirm",
    retry: "Retry",
    download: "Download",
    share: "Share",
    copy: "Copy",
    copied: "Copied!",
    
    // Header
    appName: "VideoMaker",
    appDescription: "Transform photos into videos",
    templates: "Templates",
    howItWorks: "How it works",
    
    // Main page
    heroTitle: "Transform your photos into video",
    heroSubtitle: "Upload your photos, choose a template and create an amazing video",
    stepUpload: "Upload",
    stepTemplate: "Template", 
    stepCreate: "Create",
    
    // Upload step
    chooseTemplate: "Choose Template",
    photosReady: "photo(s) ready for next step",
    backToUpload: "Back to Upload",
    
    // Template step
    chooseTemplateTitle: "Choose a Template",
    loadingTemplates: "Loading templates...",
    errorLoadingTemplates: "Error loading templates",
    errorLoadingTemplatesMessage: "Could not load templates. Please try again.",
    templateSelected: "Template selected",
    duration: "Duration",
    photos: "Photos",
    scenes: "Scenes",
    information: "Information",
    totalDuration: "Total Duration",
    selectedTemplate: "Selected Template",
    
    // Create step
    videoSummary: "Video Summary",
    creatingVideo: "Creating video...",
    createVideo: "Create Video",
    videoWillBeCreated: "Your video will be created with template",
    changeTemplate: "Change Template",
    
    // Toast messages
    sessionStarted: "Session started",
    newSessionStarted: "New session started!",
    newSession: "New Session",
    templateSelectedToast: "Template selected!",
    noPhotosSelected: "No photos selected",
    waitForUpload: "Wait for all photos to upload",
    noJobCreated: "No job created",
    noTemplateSelected: "No template selected",
    jobIdNotReturned: "Error: Job ID not returned by server",
    videoCreatedSuccess: "Video created successfully! Job ID",
    errorCreatingVideo: "Error creating video",
    sessionNotInitialized: "Session not initialized",
    photoNotFound: "Photo not found",
    photoRemovedSuccess: "Photo removed successfully",
    errorRemovingPhoto: "Error removing photo",
    noPhotosSelectedUpload: "No photos selected",
    allPhotosAlreadyUploaded: "All photos already uploaded!",
    newPhotosUploaded: "new photo(s) uploaded successfully!",
    allPhotosWereUploaded: "All photos were already uploaded!",
    errorUploadingPhotos: "Error uploading photos",
    
    // Processing status
    uploadingPhotos: "Uploading Photos",
    sendingPhotosToServers: "Sending your photos to our servers...",
    inQueue: "In Queue",
    waitingToBeProcessed: "Your video is waiting to be processed...",
    aiCraftingMasterpiece: "Our AI is crafting your masterpiece...",
    videoReady: "Video Ready!",
    videoCreatedSuccessfully: "Your video has been created successfully.",
    processingFailed: "Processing Failed",
    somethingWentWrong: "Something went wrong. Please try again.",
    preparing: "Preparing",
    gettingEverythingReady: "Getting everything ready...",
    progress: "Progress",
    usuallyTakes30to60Seconds: "This usually takes 30-60 seconds",
    
    // Viewer page
    loadingYourVideo: "Loading your video...",
    videoNotFound: "Video not found",
    returnToHome: "Return to Home",
    
    // 404 page
    pageNotFound: "Oops! Page not found",
    
    // Photo uploader
    dragAndDropPhotos: "Drag and drop photos here, or click to select",
    orClickToSelect: "or click to select",
    dropToAddMorePhotos: "Drop to add more photos",
    clickOrDragToAddMore: "Click or drag to add more photos",
    youCanAddMorePhotos: "You can add as many photos as you want",
    uploadPhotos: "Upload Photos",
    removePhoto: "Remove Photo",
    moveUp: "Move Up",
    moveDown: "Move Down",
    uploadAllPhotos: "Upload All Photos",
    photosUploaded: "photos uploaded",
    of: "of",
    
    // Job creator
    createNewJob: "Create New Job",
    jobCode: "Job Code",
    
    // API status
    apiOnline: "API Online",
    apiOffline: "API Offline",
    connecting: "Connecting...",
  },
  pt: {
    // Common
    loading: "Carregando...",
    error: "Erro",
    success: "Sucesso",
    cancel: "Cancelar",
    save: "Salvar",
    delete: "Excluir",
    edit: "Editar",
    back: "Voltar",
    next: "Próximo",
    previous: "Anterior",
    close: "Fechar",
    confirm: "Confirmar",
    retry: "Tentar novamente",
    download: "Baixar",
    share: "Compartilhar",
    copy: "Copiar",
    copied: "Copiado!",
    
    // Header
    appName: "VideoMaker",
    appDescription: "Transforme fotos em vídeos",
    templates: "Templates",
    howItWorks: "Como funciona",
    
    // Main page
    heroTitle: "Transforme suas fotos em vídeo",
    heroSubtitle: "Carregue suas fotos, escolha um template e crie um vídeo incrível",
    stepUpload: "Upload",
    stepTemplate: "Template",
    stepCreate: "Criar",
    
    // Upload step
    chooseTemplate: "Escolher Template",
    photosReady: "foto(s) pronta(s) para o próximo passo",
    backToUpload: "Voltar para Upload",
    
    // Template step
    chooseTemplateTitle: "Escolha um Template",
    loadingTemplates: "Carregando templates...",
    errorLoadingTemplates: "Erro ao carregar templates",
    errorLoadingTemplatesMessage: "Não foi possível carregar os templates. Tente novamente.",
    templateSelected: "Template selecionado",
    duration: "Duração",
    photos: "Fotos",
    scenes: "Cenas",
    information: "Informações",
    totalDuration: "Duração Total",
    selectedTemplate: "Template Selecionado",
    
    // Create step
    videoSummary: "Resumo do Vídeo",
    creatingVideo: "Criando vídeo...",
    createVideo: "Criar Vídeo",
    videoWillBeCreated: "Seu vídeo será criado com o template",
    changeTemplate: "Trocar Template",
    
    // Toast messages
    sessionStarted: "Sessão iniciada",
    newSessionStarted: "Nova sessão iniciada!",
    newSession: "Nova Sessão",
    templateSelectedToast: "Template selecionado!",
    noPhotosSelected: "Nenhuma foto selecionada",
    waitForUpload: "Aguarde o upload de todas as fotos",
    noJobCreated: "Nenhum job criado",
    noTemplateSelected: "Nenhum template selecionado",
    jobIdNotReturned: "Erro: Job ID não retornado pelo servidor",
    videoCreatedSuccess: "Vídeo criado com sucesso! Job ID",
    errorCreatingVideo: "Erro ao criar vídeo",
    sessionNotInitialized: "Sessão não inicializada",
    photoNotFound: "Foto não encontrada",
    photoRemovedSuccess: "Foto removida com sucesso",
    errorRemovingPhoto: "Erro ao remover foto",
    noPhotosSelectedUpload: "Nenhuma foto selecionada",
    allPhotosAlreadyUploaded: "Todas as fotos já foram enviadas!",
    newPhotosUploaded: "nova(s) foto(s) enviada(s) com sucesso!",
    allPhotosWereUploaded: "Todas as fotos já estavam enviadas!",
    errorUploadingPhotos: "Erro ao enviar fotos",
    
    // Processing status
    uploadingPhotos: "Enviando Fotos",
    sendingPhotosToServers: "Enviando suas fotos para nossos servidores...",
    inQueue: "Na Fila",
    waitingToBeProcessed: "Seu vídeo está aguardando para ser processado...",
    aiCraftingMasterpiece: "Nossa IA está criando sua obra-prima...",
    videoReady: "Vídeo Pronto!",
    videoCreatedSuccessfully: "Seu vídeo foi criado com sucesso.",
    processingFailed: "Processamento Falhou",
    somethingWentWrong: "Algo deu errado. Tente novamente.",
    preparing: "Preparando",
    gettingEverythingReady: "Preparando tudo...",
    progress: "Progresso",
    usuallyTakes30to60Seconds: "Isso geralmente leva 30-60 segundos",
    
    // Viewer page
    loadingYourVideo: "Carregando seu vídeo...",
    videoNotFound: "Vídeo não encontrado",
    returnToHome: "Voltar ao Início",
    
    // 404 page
    pageNotFound: "Ops! Página não encontrada",
    
    // Photo uploader
    dragAndDropPhotos: "Arraste e solte fotos aqui, ou clique para selecionar",
    orClickToSelect: "ou clique para selecionar",
    dropToAddMorePhotos: "Solte para adicionar mais fotos",
    clickOrDragToAddMore: "Clique ou arraste para adicionar mais fotos",
    youCanAddMorePhotos: "Você pode adicionar quantas fotos quiser",
    uploadPhotos: "Enviar Fotos",
    removePhoto: "Remover Foto",
    moveUp: "Mover para Cima",
    moveDown: "Mover para Baixo",
    uploadAllPhotos: "Enviar Todas as Fotos",
    photosUploaded: "fotos enviadas",
    of: "de",
    
    // Job creator
    createNewJob: "Criar Novo Job",
    jobCode: "Código do Job",
    
    // API status
    apiOnline: "API Online",
    apiOffline: "API Offline",
    connecting: "Conectando...",
  }
};

export type Language = 'en' | 'pt';
export type TranslationKey = keyof typeof translations.en;

// Default language
let currentLanguage: Language = 'en';

export const i18n = {
  // Set the current language
  setLanguage: (lang: Language) => {
    currentLanguage = lang;
    // You can also save to localStorage here
    localStorage.setItem('language', lang);
  },
  
  // Get the current language
  getLanguage: (): Language => {
    return currentLanguage;
  },
  
  // Initialize language from localStorage
  init: () => {
    const savedLang = localStorage.getItem('language') as Language;
    if (savedLang && (savedLang === 'en' || savedLang === 'pt')) {
      currentLanguage = savedLang;
    }
  },
  
  // Translate a key
  t: (key: TranslationKey): string => {
    return translations[currentLanguage][key] || key;
  },
  
  // Get all translations for a key
  getAll: (key: TranslationKey) => {
    return {
      en: translations.en[key],
      pt: translations.pt[key]
    };
  }
};

// Initialize on import
i18n.init();
