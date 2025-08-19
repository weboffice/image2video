import { i18n } from "@/lib/i18n";

export const TestI18n = () => {
  return (
    <div className="p-4 bg-gray-100 rounded">
      <h3>Teste de Internacionalização</h3>
      <p>Idioma atual: {i18n.getLanguage()}</p>
      <p>App Name: {i18n.t('appName')}</p>
      <p>Loading: {i18n.t('loading')}</p>
      <p>Error: {i18n.t('error')}</p>
    </div>
  );
};
