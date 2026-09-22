// Fase 37 (37-02) — hook de módulo ESM que permite `node` PURO importar um
// `.jsx` real (sem `vite build`, sem DOM). Existe porque `node` não conhece
// a extensão `.jsx` (`ERR_MODULE_NOT_FOUND`/"Unknown file extension" mesmo
// para arquivo sem sintaxe JSX nenhuma — a falha é de extensão, não de
// conteúdo, confirmado empiricamente antes de escrever este arquivo).
//
// Usado só por testes que precisam EXECUTAR de verdade uma função pura
// declarada dentro de um `.jsx` (ex.: `formatarRazao` em `uiOpcoes.jsx`,
// `montarTexto` em `ExplicacaoPayoff.jsx`) — o padrão dominante da casa
// (139 arquivos em `web/tests/`) é inspeção estática de fonte via
// `readFileSync`+regex, que não exige isto. Este hook só entra quando o
// `<behavior>` do plano pede asserção de valor de retorno real (TDD), não
// forma de código.
//
// `esbuild` já é dependência transitiva do Vite (`web/node_modules/esbuild`)
// — nenhuma dependência nova foi adicionada para isto.
import { transformSync } from "esbuild";

export async function load(url, context, nextLoad) {
  if (url.endsWith(".jsx")) {
    const result = await nextLoad(url, { ...context, format: "module" });
    const source = typeof result.source === "string"
      ? result.source
      : Buffer.from(result.source).toString("utf8");
    const { code } = transformSync(source, {
      loader: "jsx",
      format: "esm",
      jsx: "automatic",
      jsxImportSource: "react",
    });
    return { format: "module", source: code, shortCircuit: true };
  }
  return nextLoad(url, context);
}
