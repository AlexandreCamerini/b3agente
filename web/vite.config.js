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
        name: "Boris+",
        short_name: "Boris+",
        // Brand Book v2 — subtítulo da loja + tagline, nesta ordem.
        description: "Treine com mercado real. Aprenda a operar sem pôr dinheiro em risco.",
        // --bg do tema escuro (Brand Book v2); antes era o #0b0e14 da era BolsIA.
        theme_color: "#10121a",
        background_color: "#10121a",
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
    // Porta registrada em ~/.claude/portas.md para este projeto — a 5173 é do
    // ~/dev/Bora/web. strictPort: nunca cair em outra porta em silêncio.
    port: 5174,
    strictPort: true,
    proxy: {
      "/api": { target: "http://localhost:8787", changeOrigin: true },
    },
  },
});
