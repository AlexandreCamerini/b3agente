// quick 261013-cqk (2026-10-13) — guardião estático da lista compacta de posições,
// da folha de detalhe e da camada "posicao" (opção B). Varre App.jsx como TEXTO.
// Cobre a forma (não o comportamento em runtime: Esc, foco, voltar, swipe, alça e
// z-index sobre compra/venda ficam para conferência no aparelho). Reversão
// deliberada atualiza este guardião com nota (CLAUDE.md).
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(here, "..", "src", "App.jsx"), "utf8");
const persist = readFileSync(join(here, "..", "src", "persistence.js"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

function functionBody(name) {
  const re = new RegExp(`function ${name}\\([^)]*\\)\\s*\\{`);
  const m = re.exec(src);
  if (!m) return null;
  let depth = 0, i = m.index + m[0].length - 1;
  for (; i < src.length; i++) {
    if (src[i] === "{") depth++;
    else if (src[i] === "}") { depth--; if (depth === 0) { i++; break; } }
  }
  return src.slice(m.index, i);
}
const semComentarios = (b) => (b || "").split("\n").filter((l) => !/^\s*\/\//.test(l.trim())).join("\n").replace(/\{\/\*[\s\S]*?\*\/\}/g, "");

const tela = functionBody("CarteiraScreen") || "";
ok("CarteiraScreen localizada", tela.length > 2000);

// --- CarteiraScreen: lista + folha ------------------------------------------
for (const s of ["ordenarLinhas(", "prioridadeAtencao(", "<LinhaPosicao", "<LinhaPernaAvulsa", "<BottomSheet zIndex={45}", "naFolha", "<CartaoPosicao", "<CartaoPernaAvulsa", 'id={"posicao-" + p.t}', "histFor === p.t", "editFor === p.t", "ctx.reportarNavPosicao", "ctx.registrarFecharPosicao", "<ChipsOrdenacaoPosicoes"]) {
  ok(`CarteiraScreen contém ${s}`, tela.includes(s));
}
ok("hero intacto (PATRIMÔNIO TOTAL / RESULTADO ABERTO / CAIXA DISPONÍVEL / EM POSIÇÕES)", ["PATRIMÔNIO TOTAL", "RESULTADO ABERTO", "CAIXA DISPONÍVEL", "EM POSIÇÕES"].every((s) => tela.includes(s)));
ok("pernas avulsas depois das posições na lista", tela.indexOf("<LinhaPosicao") > 0 && tela.indexOf("<LinhaPernaAvulsa") > tela.indexOf("<LinhaPosicao"));

// --- componentes novos: botões acessíveis, sem conta ------------------------
const chips = functionBody("ChipsOrdenacaoPosicoes") || "";
ok("ChipsOrdenacaoPosicoes tem aria-pressed, minHeight 44 e role=group", /aria-pressed=/.test(chips) && /minHeight: 44/.test(chips) && /role="group"/.test(chips));
const corpoLinha = functionBody("CorpoLinhaLista") || "";
ok("linha é <button type=button> com aria-label, aria-haspopup e minHeight 44", /<button type="button"/.test(corpoLinha) && /aria-label=/.test(corpoLinha) && /aria-haspopup="dialog"/.test(corpoLinha) && /minHeight: 44/.test(corpoLinha));
const novos = ["ChipsOrdenacaoPosicoes", "ChipAtencaoLista", "MiniReguaLista", "LinhaPosicao", "LinhaPernaAvulsa", "CorpoLinhaLista", "textoChipAtencao", "textoFaixaLista"].map((n) => semComentarios(functionBody(n))).join("\n");
ok("componentes novos localizados", novos.length > 3000);
ok("proximidade só do backend: nenhum componente novo lê distStopPct, posicaoNoPlano === nem faz conta com avg", !/distStopPct|posicaoNoPlano\s*===|\.avg\s+-|-\s+p\.avg/.test(novos));
ok("mini-régua posiciona só por dominioRegua + posRegua", /dominioRegua\(/.test(novos) && /posRegua\(/.test(novos));

// --- BottomSheet e CartaoPosicao --------------------------------------------
const folhaBase = functionBody("BottomSheet") || "";
ok("BottomSheet tem zIndex default 1000", /zIndex = 1000/.test(src.slice(src.indexOf("function BottomSheet("), src.indexOf("function BottomSheet(") + 120)) && folhaBase.length > 100);
const cartao = functionBody("CartaoPosicao") || "";
ok("CartaoPosicao: useState(!!naFolha) e onFecharFolha", /useState\(!!naFolha\)/.test(cartao) && /onFecharFolha/.test(cartao));
ok("CartaoPosicao: espaçador do FAB só fora da folha", /aberto && !naFolha && <div aria-hidden style=\{\{ height: FOLGA_FAB_PET \}\}/.test(cartao));

// --- anti-loop (hooks e efeitos) --------------------------------------------
ok("efeito de limpeza com guarda abertaT && !abertaExiste", tela.includes("if (abertaT && !abertaExiste) setAbertaT(null)") && tela.includes("}, [abertaT, abertaExiste]);"));
ok("efeito de relato com dep única abertaT", tela.includes("ctx.reportarNavPosicao(!!abertaT); }, [abertaT]);"));
ok("App: setter devolve o MESMO valor quando nada muda", src.includes("setPosicaoNav((v) => (v === !!aberta ? v : !!aberta))"));
{
  const iRet = tela.indexOf("  return (\n");
  const idx = [tela.indexOf('useState("atencao")'), tela.indexOf("const [abertaT, setAbertaT] = useState(null)"), tela.indexOf("useEffect(() => { if (abertaT && !abertaExiste)"), tela.indexOf("ctx.reportarNavPosicao(!!abertaT)"), tela.indexOf("ctx.registrarFecharPosicao(() => setAbertaT(null))")];
  ok("todos os hooks novos vêm antes do primeiro `return (` de CarteiraScreen", iRet > 0 && idx.every((i) => i > 0 && i < iRet));
}

// --- paridade por delegação (persistence.js não muda) -----------------------
ok("carteiraLeitura existe nos DOIS stores (delegação à mesma rota)", (persist.match(/carteiraLeitura/g) || []).length >= 2);

console.log(fails === 0 ? "\nTUDO OK" : `\n${fails} FALHA(S)`);
process.exit(fails === 0 ? 0 : 1);
