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
      // ADR-011/012: o portal de observabilidade (server/admin_dist) e a
      // página de instalação do iOS Ad Hoc (server/ios_dist) são servidos na
      // MESMA origem, em /admin/* e /ios/* — sem isto, o NavigationRoute
      // padrão do Workbox intercepta QUALQUER navegação da origem (sem
      // denylist) e serve o shell deste app no lugar deles. Bug real
      // reportado em produção: "/admin abre o app" em vez do portal; mesma
      // classe reapareceu em "/ios abre o app" em vez da página de instalação.
      workbox: {
        navigateFallbackDenylist: [/^\/admin/, /^\/ios/],
      },
      manifest: {
        name: "Boris+",
        short_name: "Boris+",
        // O default do plugin é "en" — o app é inteiro em PT-BR, e o manifesto
        // é o que o macOS/Windows leem ao instalar como app.
        lang: "pt-BR",
        dir: "ltr",
        // Brand Book v2 — subtítulo da loja + tagline, nesta ordem.
        description: "Treine com mercado real. Aprenda a operar sem pôr dinheiro em risco.",
        // --bg do tema escuro (Brand Book v2); antes era o #0b0e14 da era Boris+.
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
    //
    // PORT só entra quando quem sobe o servidor ATRIBUI a porta — um segundo
    // worktree rodando em paralelo, ou o harness com `autoPort`. Isso não
    // afrouxa a regra acima: continua não existindo fallback silencioso (sem
    // PORT é 5174 ou erro), o que muda é poder haver escolha explícita de
    // quem chama. Sem isto, dois worktrees do mesmo projeto não sobem juntos.
    port: Number(process.env.PORT) || 5174,
    strictPort: true,
    proxy: {
      "/api": { target: "http://localhost:8787", changeOrigin: true },
    },
  },
});
