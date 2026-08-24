// 260823-x55 (Task 2) — guardião source-grep (mesmo padrão de test_radar.mjs)
// do campo de busca textual do Radar: existência do input acessível, filtro
// client-side só por r.ticker (payload de scanner.py não expõe nome/setor,
// CLAUDE.md princípio 4) e tratamento de estado vazio quando a busca não
// encontra nada.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const src = (f) => readFileSync(join(here, "..", "src", f), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

const appSrc = src("App.jsx");
const radarChunk = appSrc.slice(appSrc.indexOf("function RadarScreen"), appSrc.indexOf("function ConfigScreen"));
ok("trecho da RadarScreen localizado", radarChunk.length > 500);

// 1) campo de busca existe, acessível
ok("campo de busca (useState busca) declarado", /const \[busca, setBusca\] = useState\(""\)/.test(radarChunk));
ok("input de busca com aria-label", /aria-label="Buscar ticker no Radar"/.test(radarChunk));
ok("input de busca controlado (value={busca})", /value=\{busca\}/.test(radarChunk));

// 2) filtro é só por r.ticker (não inventa campo de nome/setor)
ok("filtro usa r.ticker.toUpperCase().includes", /r\.ticker\.toUpperCase\(\)\.includes\(/.test(radarChunk));

// 3) estado vazio tratado
ok("mensagem de estado vazio presente", /Nenhum ativo encontrado/.test(radarChunk));

// 4) o grid usa o resultado FILTRADO, não o results cru
ok("resultsFiltrados usado no .map() do grid", /resultsFiltrados\.map\(\(r\)/.test(radarChunk));
ok("resultsFiltrados declarado como filtro de results", /const resultsFiltrados = buscaNorm \? results\.filter/.test(radarChunk));

console.log("\n" + (fails === 0 ? "TODOS OS TESTES DE BUSCA DO RADAR PASSARAM" : fails + " TESTE(S) FALHARAM"));
process.exit(fails === 0 ? 0 : 1);
