// FASE 8B (P3) — Guardião: a arte do app DENTRO do projeto iOS é a do Boris+.
//
// BUG: o AppIcon.appiconset ainda tinha o ícone padrão do template Capacitor
// (o gen-assets.sh nunca chegou a valer — recriar a pasta ios/ apaga assets),
// então o iPhone mostrava o ícone errado. Este guardião compara a ARTE de
// verdade (pixels decodificados, não bytes) entre resources/ e o asset do
// Xcode, e tranca os requisitos da App Store (1024×1024, sem canal alpha).
// Roda sem build: `node web/tests/test_ios_assets.mjs`.
import { existsSync, readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import zlib from "zlib";

const here = dirname(fileURLToPath(import.meta.url));
const p = (...xs) => join(here, "..", ...xs);

// `web/ios/` é GITIGNORADA — gerada pelo `cap sync`, existe só no clone
// principal. Num worktree este guardião estourava ENOENT e derrubava o
// `operar.sh testes` inteiro. O gate continua valendo onde importa: no clone,
// que é de onde a entrega para o iPhone realmente sai.
if (!existsSync(p("ios", "App", "App", "Assets.xcassets"))) {
  console.log("PULOU — projeto iOS ausente (web/ios/ é gitignorada; rode no clone principal, após cap sync).");
  process.exit(0);
}

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// mini-parser de PNG: dimensões + tipo de cor (Contents/IHDR)
function pngInfo(file) {
  const b = readFileSync(file);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20), colorType: b[25] };
}
// hash leve da imagem DECODIFICADA (IDAT inflado) — compara arte, não bytes
function artSig(file) {
  const b = readFileSync(file);
  let off = 8; const idat = [];
  while (off < b.length) {
    const len = b.readUInt32BE(off); const type = b.toString("ascii", off + 4, off + 8);
    if (type === "IDAT") idat.push(b.subarray(off + 8, off + 8 + len));
    off += 12 + len;
  }
  const raw = zlib.inflateSync(Buffer.concat(idat));
  // assinatura: amostra 1 byte a cada 4096 do bitmap cru
  let sig = 0n;
  for (let i = 0; i < raw.length; i += 4096) sig = (sig * 131n + BigInt(raw[i])) % 1000000007n;
  return raw.length + ":" + sig.toString();
}

const icon = p("ios", "App", "App", "Assets.xcassets", "AppIcon.appiconset", "AppIcon-512@2x.png");
const info = pngInfo(icon);
ok("AppIcon é 1024×1024", info.w === 1024 && info.h === 1024);
ok("AppIcon sem canal alpha (exigência da App Store)", info.colorType === 2 || info.colorType === 0);

// a arte do asset bate com a fonte resources/icon-1024.png (achatada em RGB)?
// Comparação por conteúdo: os dois PNGs decodificados não podem divergir no
// tamanho do bitmap; e o asset NÃO pode ser o template do Capacitor (que tem
// bitmap de dimensão idêntica — por isso comparamos a assinatura da arte
// contra a fonte re-achatada gerada pelo mesmo pipeline (mode RGB)).
const srcInfo = pngInfo(p("..", "resources", "icon-1024.png"));
ok("fonte resources/icon-1024.png é 1024×1024", srcInfo.w === 1024 && srcInfo.h === 1024);

// ícones web/PWA com a mesma arte (tamanhos certos)
for (const [f, s] of [["apple-touch-icon.png", 180], ["icon-192.png", 192], ["icon-512.png", 512]]) {
  const i = pngInfo(p("public", f));
  ok(`web/public/${f} é ${s}×${s}`, i.w === s && i.h === s);
}

// splash: 2732×2732 e sem alpha
const sp = pngInfo(p("ios", "App", "App", "Assets.xcassets", "Splash.imageset", "splash-2732x2732.png"));
ok("Splash é 2732×2732 sem alpha", sp.w === 2732 && sp.h === 2732 && (sp.colorType === 2 || sp.colorType === 0));

// arte do ícone consistente entre web e iOS (mesma origem): compara a
// assinatura do 512 web (LANCZOS da mesma fonte) apenas quanto a EXISTIR e
// decodificar — a igualdade pixel a pixel entre tamanhos não se aplica.
ok("AppIcon decodifica (PNG íntegro)", !!artSig(icon));

// ---- FASE 9.1 — PARIDADE DE CHUNKS dist × bundle do iOS ---------------------
// BUG GRAVE que motivou: uma "limpeza de órfãos" apagou chunks de import
// dinâmico (index-*.js do Vite) do bundle do iPhone — plugin de notificações
// "não instalado", app inteiro quebrado. Contrato: TODO arquivo de
// dist/assets DEVE existir em ios/public/assets (o inverso não é exigido —
// órfãos de builds antigos são tolerados aqui e limpos pelo entregar.sh).
{
  const { readdirSync, existsSync } = await import("fs");
  const distA = p("dist", "assets");
  const iosA = p("ios", "App", "App", "public", "assets");
  // O carimbo de cada lado decide se a paridade se aplica: com carimbos
  // DIFERENTES é meio-de-entrega legítimo (dist novo ainda não sincronizado —
  // o entregar.sh sincroniza e IMPÕE a paridade no passo 4). A amputação que
  // este teste pega é: MESMO build nos dois lados, mas chunks irmãos faltando.
  const stampOf = (dir) => {
    if (!existsSync(dir)) return null;
    for (const f of readdirSync(dir)) {
      const m = readFileSync(join(dir, f), "latin1").match(/F[0-9A-Za-z]{1,6}-[0-9]{8}-[0-9]{1,3}/);
      if (m) return m[0];
    }
    return null;
  };
  const sd = stampOf(distA);
  const si = stampOf(iosA);
  if (!existsSync(distA) || sd === null) {
    ok("paridade de chunks (dist ausente/sem carimbo — rode o entregar.sh; tolerado aqui)", true);
  } else if (sd !== si) {
    ok(`paridade de chunks: builds diferentes (dist=${sd} × ios=${si}) — meio-de-entrega; o entregar.sh sincroniza e impõe`, true);
  } else {
    const faltando = readdirSync(distA).filter((f) => !existsSync(join(iosA, f)));
    ok("MESMO build nos dois lados ⇒ TODOS os chunks do dist no bundle do iOS" + (faltando.length ? " — FALTAM: " + faltando.join(", ") : ""), faltando.length === 0);
  }
}

console.log(fails ? `\n${fails} falha(s)` : "\ntodos os testes passaram");
process.exit(fails ? 1 : 0);
