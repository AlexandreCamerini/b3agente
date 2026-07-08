import type { CapacitorConfig } from "@capacitor/cli";

const config: CapacitorConfig = {
  // Troque para o seu identificador (formato reverse-DNS). Use algo único e
  // estável — depois de publicado/instalado, mudar o appId cria "outro app".
  appId: "com.alexandrecamerini.bolsia",
  appName: "BolsIA",
  webDir: "dist",
  backgroundColor: "#0b0e14",
  ios: {
    contentInset: "always",
  },
  plugins: {
    // FASE 8 (A1 — CAUSA-RAIZ das notificações locais "mudas" em foreground):
    // no @capacitor/local-notifications 8.x, o willPresent só reconhece
    // "banner" | "list" | "badge" | "sound" — a opção "alert" cai em
    // "Unrecognized" e a notificação chega SEM apresentação visual com o app
    // aberto (só som/badge). O push mapeia "alert" → banner+list, mas o local
    // NÃO (assimetria do plugin upstream, conferida no fonte instalado).
    // Por isso: sempre "banner" + "list" explícitos, nos DOIS plugins.
    LocalNotifications: {
      presentationOptions: ["banner", "list", "sound", "badge"],
    },
    PushNotifications: {
      presentationOptions: ["banner", "list", "sound", "badge"],
    },
    // Faz o fetch() usar HTTP nativo no iPhone, ignorando CORS — necessário
    // para chamar a API da brapi.dev direto do app. No navegador (PWA desktop)
    // o fetch normal continua valendo e o CORS pode bloquear; nesse caso o app
    // exibe um aviso e segue no modo simulado.
    CapacitorHttp: { enabled: true },
  },
};

export default config;
