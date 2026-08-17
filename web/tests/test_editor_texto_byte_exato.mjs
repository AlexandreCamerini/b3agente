// ADR-014 — Guardião do EDITOR PADRÃO do portal admin (web-admin/EditorTexto.jsx).
//
// A REGRA que este teste protege: o editor de texto longo NUNCA transforma o
// que o admin escreveu. Um único byte alterado quebra, EM SILÊNCIO, o
// mecanismo de migração de prompt do backend:
//
//     server/app/store.py:21  sha256(texto.encode()).hexdigest() in LEGACY_PROMPT_SHA256
//
// Esse hash decide se uma conta "nunca editou o prompt" (e pode receber o
// default novo) ou se aquilo é edição pessoal, intocável para sempre. Editor
// que normaliza aspas, apara espaço em fim de linha, converte CRLF ou fecha
// colchete sozinho muda o hash — e ninguém vê erro nenhum acontecer.
//
// Os prompts também carregam um bloco JSON LITERAL (o contrato de saída que a
// UI parseia): indentação e aspas ali são semânticas, não formatação.
//
// Roda sem build: `node web/tests/test_editor_texto_byte_exato.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const raiz = join(here, "..", "..");
const editor = readFileSync(join(raiz, "web-admin", "src", "EditorTexto.jsx"), "utf8");
const appAdmin = readFileSync(join(raiz, "web-admin", "src", "App.jsx"), "utf8");
const store = readFileSync(join(raiz, "server", "app", "store.py"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// O motivo do teste ainda existe? Se o backend parar de comparar sha256, esta
// regra pode ser relaxada CONSCIENTEMENTE — mas aí é para atualizar o guardião
// com nota, não para apagá-lo.
ok("backend ainda decide migração por sha256 do texto (a razão desta regra)",
   /sha256\(texto\.encode\(\)\)\.hexdigest\(\)/.test(store));

// ─── o texto sai como entrou ────────────────────────────────────────────────
// onChange repassa o documento CRU. Qualquer .trim()/.replace()/normalize()
// no caminho do valor é exatamente o defeito que este teste existe para pegar.
ok("onChange repassa o texto cru, sem transformar", /onChange=\{\(v\) => onChange\(v\)\}/.test(editor));

const transformacoes = [
  [/onChange\((?:v|valor)\s*\.\s*trim\(\)/, "trim() no valor"],
  [/onChange\((?:v|valor)\s*\.\s*replace\(/, "replace() no valor"],
  [/onChange\((?:v|valor)\s*\.\s*normalize\(/, "normalize() no valor"],
  [/setTexto\((?:v|valor)\s*\.\s*(?:trim|normalize)\(/, "normalização antes do estado"],
];
for (const [re, oque] of transformacoes) {
  ok("editor não aplica " + oque, !re.test(editor) && !re.test(appAdmin));
}

// ─── nada de WYSIWYG ────────────────────────────────────────────────────────
// Editor rich-text faz round-trip por AST: o texto é reserializado a partir da
// árvore e volta diferente do que entrou, mesmo "sem editar nada".
const wysiwyg = /@tiptap|slate-react|react-quill|draft-js|@mdxeditor|contentEditable/i;
ok("não usa editor WYSIWYG (round-trip por AST reescreve bytes)",
   !wysiwyg.test(editor) && !wysiwyg.test(appAdmin));

// CodeMirror é editor de TEXTO: realça, não reescreve.
ok("usa CodeMirror com realce markdown", /@uiw\/react-codemirror/.test(editor) && /@lezer\/markdown/.test(editor));

// A linguagem é montada do parser do @lezer/markdown de propósito. Voltar para
// `markdown()` do @codemirror/lang-markdown traz DE VOLTA o keymap que continua
// lista sozinho (Enter insere "- " que o admin não digitou) — além de 74KB gzip
// de gramática HTML/JS/CSS que nenhum prompt usa.
// Casa o IMPORT, não a menção: o próprio EditorTexto.jsx cita o pacote no
// comentário que explica por que ele NÃO é usado.
ok("não importa lang-markdown (keymap que auto-insere marcador de lista)",
   !/from\s+"@codemirror\/lang-markdown"/.test(editor));

// closeBrackets INSERE caractere que o admin não digitou — dentro do contrato
// JSON literal do prompt isso corrompe o texto.
ok("fechamento automático de colchete/aspas está desligado", /closeBrackets:\s*false/.test(editor));
ok("autocomplete está desligado", /autocompletion:\s*false/.test(editor));

// ─── a prévia é read-only ───────────────────────────────────────────────────
// O renderizador de markdown pode normalizar à vontade — desde que o resultado
// NUNCA volte para o texto salvo. Ele recebe `texto`, devolve JSX, e ponto.
ok("prévia só recebe o texto para renderizar", /<PreviaMarkdown texto=\{valor\} T=\{T\} \/>/.test(editor));
// Região do renderizador, delimitada: de PreviaMarkdown até o bloco do editor.
// (Fatiar por "export function EditorTexto" pegava o JSDoc dele, que cita
// `onChange` — falso positivo que este comentário existe para não repetir.)
const regiaoPrevia = editor.slice(
  editor.indexOf("export function PreviaMarkdown"),
  editor.indexOf("const temaDe ="),
);
ok("renderizador da prévia não escreve de volta (sem onChange na região)",
   regiaoPrevia.length > 200 && !/onChange/.test(regiaoPrevia));

// ─── o editor é o padrão do portal ──────────────────────────────────────────
// Se alguém acrescentar um <textarea> solto no App.jsx do admin, ele escapa de
// todas as garantias acima. Texto longo passa pelo EditorTexto.
ok("Prompts usa o EditorTexto padrão", /<EditorTexto/.test(appAdmin));
ok("nenhum <textarea> solto no App.jsx do admin (texto longo usa EditorTexto)",
   !/<textarea/.test(appAdmin));

// Carga sob demanda: o CodeMirror leva o bundle de 185KB para 810KB e o portal
// abre em rede móvel dentro do app nativo.
ok("editor carrega sob demanda (lazy), fora do bundle inicial",
   /lazy\(\(\) => import\("\.\/EditorTexto\.jsx"\)/.test(appAdmin));

console.log(fails === 0 ? "\nTUDO OK" : `\n${fails} FALHA(S)`);
process.exit(fails === 0 ? 0 : 1);
