import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// ADR-011 / qa/47: servido pelo MESMO backend do app consumidor, em subpath
// /admin/* (mesmo container, sem infra nova — decisão do Alex, 2026-08-14).
// `base: "/admin/"` é o que faz os assets buildados resolverem sob esse
// subpath em vez da raiz (onde o app consumidor já está montado).
export default defineConfig({
  base: "/admin/",
  plugins: [react()],
  server: {
    // Porta própria — 5173 é de outro projeto (~/dev/Bora/web), 5174 é do
    // web/ deste repo (ver web/vite.config.js).
    port: Number(process.env.PORT) || 5175,
    strictPort: true,
    proxy: {
      "/api": { target: "http://localhost:8787", changeOrigin: true },
    },
  },
});
