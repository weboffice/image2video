import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { componentTagger } from "lovable-tagger";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // Carregar variáveis de ambiente
  const env = loadEnv(mode, process.cwd(), '');
  const API_TARGET = env.VITE_API_BASE_URL || "http://localhost:8080";
  
  return {
    server: {
      host: "::",
      port: 5173,
      proxy: {
        "/api": {
          target: API_TARGET,
          changeOrigin: true,
          secure: false,
        },
        "/files": {
          target: API_TARGET,
          changeOrigin: true,
          secure: false,
        },
      },
    },
    plugins: [
      react(),
      mode === 'development' &&
      componentTagger(),
    ].filter(Boolean),
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
    },
  };
});
