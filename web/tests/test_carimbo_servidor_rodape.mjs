// Quick 260911-k9g — guardião do rodapé do Perfil com os DOIS carimbos (app +
// servidor).
//
// Por que existe: o rodapé (`web/src/App.jsx`, `PerfilHub`) mostrava só o
// `BUILD_ID` do FRONT. Num deploy SÓ-backend (aconteceu 5x em 10-11/09/26) o
// app parece desatualizado e não há como ver, do aparelho, qual servidor está
// respondendo — isso confundiu o Alex três vezes nesta mesma sessão. O
// comentário antigo ("se não bater, aparelho com código antigo") é FALSO
// nesse caso.
//
// A REGRESSÃO PERIGOSA que este guardião existe para pegar: quando a consulta
// ao servidor falhar, o rodapé cair de volta no `BUILD_ID` do front — isso
// faria a tela AFIRMAR uma versão de servidor que ninguém mediu. O contrato é
// `serverBuildId` null (falha) => travessão, nunca `BUILD_ID` como fallback.
//
// Roda sem build: `node web/tests/test_carimbo_servidor_rodape.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const src = (f) => readFileSync(join(here, "..", "src", f), "utf8");

const app = src("App.jsx");
const api = src("api.js");
const persistence = src("persistence.js");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// Sem comentários: para os testes de CÓDIGO (não os que checam o texto do
// comentário em si). Evita que um comentário explicando o defeito antigo
// faça a regex do "não voltou" casar sozinha.
const semComentario = (s) => s
  .replace(/\/\*[\s\S]*?\*\//g, "")
  .split("\n").filter((l) => !/^\s*\/\//.test(l)).join("\n");
const appSemComentario = semComentario(app);

// ---- 1) api.js: método serverBuild existe, sem exceção, timeout curto ------
ok("api.serverBuild existe dentro do objeto `api`", /serverBuild:\s*async\s*\(\)\s*=>/.test(api));
ok("api.serverBuild bate em /api/health", /serverBuild:[\s\S]{0,400}\/api\/health/.test(api));
ok("api.serverBuild usa timeout curto (8000ms), não o TIMEOUT_MS/TIMEOUT_LLM padrão",
   /serverBuild:[\s\S]{0,400}fetchWithTimeout\([^)]*,\s*8000\)/.test(api));
ok("api.serverBuild nunca propaga exceção — catch devolve null",
   /serverBuild:[\s\S]{0,300}catch\s*\{\s*return null;\s*\}/.test(api));
ok("api.serverBuild devolve null quando o corpo não tem `build` string",
   /serverBuild:[\s\S]{0,600}typeof j\.build !== "string"\)\s*return null;/.test(api));

// ---- 2) persistence.js: paridade nos DOIS stores (guardrail do CLAUDE.md) --
ok("serverStore delega serverBuild direto para api.serverBuild()",
   /serverBuild:\s*\(\)\s*=>\s*api\.serverBuild\(\)/.test(persistence));
ok("deviceStore expõe serverBuild com ensure() antes da delegação (aplica setApiBase no nativo)",
   /async serverBuild\(\)\s*\{\s*ensure\(\);\s*return api\.serverBuild\(\);\s*\}/.test(persistence));

// ---- 3) App.jsx: PerfilHub busca ao montar, três estados corretos ----------
ok("PerfilHub declara estado serverBuildId nascendo `undefined` (carregando)",
   /const \[serverBuildId, setServerBuildId\] = useState\(undefined\);/.test(appSemComentario));
ok("busca acontece em useEffect (ao montar a tela do Perfil, não no boot do app)",
   /useEffect\(\(\) => \{\s*let ativo = true;\s*store\.serverBuild\(\)\.then/.test(appSemComentario));
ok("o efeito descarta resposta em voo se o componente desmontou (`if (ativo)`)",
   /store\.serverBuild\(\)\.then\(\(b\) => \{ if \(ativo\) setServerBuildId\(b\); \}\);/.test(appSemComentario));

// ---- 4) a regressão perigosa: falha NUNCA cai no BUILD_ID do front ---------
const iRodape = appSemComentario.indexOf("app {BUILD_ID}");
ok("linha do rodapé com os dois carimbos encontrada", iRodape >= 0);
const linhaRodape = iRodape >= 0 ? appSemComentario.slice(iRodape, iRodape + 200) : "";
ok("estado de carregando (undefined) NÃO renderiza o segmento do servidor (sem flash de travessão)",
   /serverBuildId !== undefined && /.test(linhaRodape));
ok("estado de sucesso/falha mostra `servidor` com travessão como único fallback",
   /servidor \{serverBuildId \|\| "—"\}/.test(linhaRodape));
ok('defeito NÃO existe: o segmento do servidor nunca cai em `serverBuildId || BUILD_ID`',
   !/serverBuildId \|\| BUILD_ID/.test(appSemComentario));
ok('defeito NÃO existe: nenhuma variante do carimbo do servidor usa `BUILD_ID` como fallback de falha',
   !/servidor \{[^}]*BUILD_ID[^}]*\}/.test(appSemComentario));

// ---- 5) sanidade: a regex do defeito pega o padrão perigoso quando existe --
// Sem isto, um typo na regex faria o assert "defeito não existe" passar
// SEMPRE, mesmo com a regressão de volta.
const TRECHO_COM_BUG = 'app {BUILD_ID} · servidor {serverBuildId || BUILD_ID}';
ok("sanidade: a regex do defeito pega o padrão perigoso quando ele existe",
   /serverBuildId \|\| BUILD_ID/.test(TRECHO_COM_BUG));

// ---- 6) comentário FASE 8B atualizado — não afirma mais que toda divergência
// é "aparelho com código antigo" (falso no deploy só-backend) -----------------
const iComentario = app.indexOf("FASE 8B (260911-k9g): DOIS carimbos");
ok("comentário FASE 8B foi atualizado (marca 260911-k9g)", iComentario >= 0);
const comentario = iComentario >= 0 ? app.slice(iComentario, app.indexOf("*/", iComentario)) : "";
ok("o comentário novo explica que os carimbos divergem POR DESENHO no deploy só-backend",
   /POR DESENHO/.test(comentario) && /só-backend/.test(comentario));
ok("o comentário novo NÃO reafirma a regra antiga sem qualificação (\"instalado — se não bater, código antigo\")",
   !/carimbo do build instalado — se não bater com a entrega,\s*\n\s*\/\/\s*o aparelho está rodando código antigo/.test(app));

console.log(fails === 0 ? "\ntodos os testes passaram" : `\n${fails} FALHA(S)`);
process.exit(fails === 0 ? 0 : 1);
