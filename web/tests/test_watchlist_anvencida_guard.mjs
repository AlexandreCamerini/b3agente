// Guardião: crash real capturado pelo ErrorBoundary (main.jsx) em produção —
// "Algo saiu do lugar" / "undefined is not an object (evaluating 'A.snapshotId')".
//
// CAUSA: em MercadoScreen, `anVencida` lia `sc.snapshotId` sem checar se `sc`
// (scanBy[t]) existia. Toda outra leitura de `sc` na mesma função guarda com
// `sc &&` (tierOf(sc && sc.confluencia), `sc ? {...} : undefined` no buyMeta)
// — só esta ficou de fora. Quando o usuário tinha uma análise cacheada
// (an.snapshotId) para um ticker que ainda não apareceu no scan corrente
// (sc undefined — scan não rodou pra esse ticker ainda, ou ainda está em
// voo), a leitura de `sc.snapshotId` lançava TypeError e derrubava a árvore
// inteira — intermitente por natureza (depende de timing scan × cache).
//
// Roda sem build: `node web/tests/test_watchlist_anvencida_guard.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const app = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");

let fails = 0;
const ok = (name, cond, extra) => {
  console.log((cond ? "ok " : "FALHOU ") + name + (cond || !extra ? "" : " — " + extra));
  if (!cond) fails++;
};

const linha = app.split("\n").find((l) => l.includes("const anVencida ="));
ok("a linha de anVencida existe em App.jsx", !!linha, "procure por 'const anVencida =' em MercadoScreen");
ok("anVencida guarda `sc` ANTES de qualquer leitura de sc.snapshotId (curto-circuito do && protege o resto da expressão — mesmo padrão de tierOf/buyMeta nesta função)",
  !!linha && (() => {
    const iGuarda = linha.indexOf("sc &&");
    const iLeitura = linha.indexOf("sc.snapshotId");
    return iGuarda >= 0 && iLeitura >= 0 && iGuarda < iLeitura;
  })());

console.log(fails ? `\n${fails} falha(s)` : "\ntodos os testes passaram");
process.exit(fails ? 1 : 0);
