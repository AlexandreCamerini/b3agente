import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

// Em desenvolvimento, /api é encaminhado para o backend (porta 8787), evitando
// CORS. Em produção, o próprio backend serve o app (mesma origem). Para o app
// nativo (Capacitor), defina VITE_API_BASE com a URL do servidor na sua rede
// (ex.: http://192.168.0.10:8787) ao rodar o build.
export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      injectRegister: null,
      includeAssets: ["apple-touch-icon.png"],
      manifest: {
        name: "B3 Agente",
        short_name: "B3 Agente",
        description: "Simulador educacional de paper trading da B3.",
        theme_color: "#0b0e14",
        background_color: "#0b0e14",
        display: "standalone",
        icons: [
          { src: "icon-192.png", sizes: "192x192", type: "image/png" },
          { src: "icon-512.png", sizes: "512x512", type: "image/png" },
          { src: "icon-512-maskable.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
        ],
      },
    }),
  ],
  server: {
    proxy: {
      "/api": { target: "http://localhost:8787", changeOrigin: true },
    },
  },
});
