// Loader Vite do guia das telas (quick 261011-l5x). ÚNICO arquivo Vite-específico do guia.
//
// Fonte única: o MESMO site/js/telas-data.js que o site (site/app/guia.html) executa como
// script. Aqui entra como texto (?raw) e passa por parseTelasData; nenhum dado é copiado
// para web/src (web/tests/test_guia_dados.mjs trava isso). As capturas entram pelo glob
// com ?url: o Vite as emite com hash no bundle, então abrem offline no iOS (Capacitor
// carrega o bundle local). Custo aceito: ~2,4 MB, fora do precache do Workbox.
import bruto from "../../site/js/telas-data.js?raw";
import { parseTelasData } from "./guiaDados.js";

export const GUIA_TELAS = parseTelasData(bruto);

const CAPTURAS = import.meta.glob(
  ["../../site/img/[0-9][0-9]-*.{jpg,png}", "../../site/img/web-*.jpg"],
  { eager: true, query: "?url", import: "default" },
);

// "img/01-boas-vindas.jpg" -> URL emitida pelo Vite, ou null se a captura não existir.
export function urlDaCaptura(img) {
  return CAPTURAS["../../site/" + img] || null;
}
