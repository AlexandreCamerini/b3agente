/**
 * entendimento.jsx — Fase 38 (38-02), extração de App.jsx.
 *
 * Camada de entendimento do Boris+: a folha de explicação (`ConceitoSheet`),
 * o registro de setor tocável (`SetorAlvo`), o assistente de pergunta única
 * dentro da folha (`AssistenteBox`) e o marcador mínimo de conteúdo de IA
 * (`AiNote`) — REFATORAÇÃO PURA, zero mudança de comportamento (código movido
 * verbatim de `web/src/App.jsx`).
 *
 * Por que saiu de App.jsx: ROADMAP SC#4 e KB-02 exigem que `SetorAlvo`/
 * `ConceitoSheet` sejam importáveis também por `web/src/opcoes/OpcoesScreen.jsx`
 * — que não pode importar `App.jsx` (ADR-027, isolamento de duas vias).
 *
 * Este módulo NÃO importa `App.jsx` nem `OpcoesScreen.jsx` — seria ciclo e
 * quebraria o isolamento do ADR-027.
 *
 * Regra de duplicação aceita (mesmo padrão de `web/src/opcoes/uiOpcoes.jsx`,
 * Fase 33): token de tema é espelho declarado local — `T` aqui aponta para as
 * MESMAS variáveis CSS que `App.jsx` injeta em `:root`, nenhum uso de um
 * token muda de valor.
 */
import { useState, useEffect } from "react";
import { store } from "./persistence.js";
import { Markdown } from "./markdown.jsx";
// Fase 38 (38-03): ponte kb×conceito — helper puro que resolve um verbete do
// catálogo da KB já em memória (sem fetch nenhum, ver ConceitoSheet abaixo).
import { verbeteDoCatalogo } from "./glossario.js";

const VARKEY = (k) => "--" + k.replace(/[A-Z]/g, (c) => "-" + c.toLowerCase());
const TOKENS = ["textFaint", "textMuted", "textSecondary", "textPrimary", "borderSubtle",
  "borderFaint", "bgBase", "bgPanel", "scrim", "accent", "accentTint10", "negative"];
const T = Object.fromEntries(TOKENS.map((k) => [k, `var(${VARKEY(k)})`]));

// Marcador MÍNIMO junto ao conteúdo de IA (o texto completo vive em "Sobre").
// FIX-C01 (Plano 04-05): `source` rotula a origem real do texto — "ia"
// (default, comportamento inalterado) ou "deterministico" (fallback do
// backend quando a IA está indisponível, sem chamada de LLM nenhuma). Nunca
// afirmar "conteúdo de IA" sobre texto que não passou por LLM (princípio 7
// do CLAUDE.md) — o rótulo é status do app, por isso NÃO bifurca por modo.
export const AiNote = ({ at, source = "ia" }) => (
  <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "10px", color: T.textFaint, marginTop: "10px" }}>
    <span aria-hidden style={{ fontWeight: 700 }}>ⓘ</span>
    <span>{source === "deterministico"
      ? "Explicação automática do app (sem IA) · baseada no setup/indicador detectado" + (at ? " · " + at : "")
      : "Conteúdo educacional de IA · não é recomendação" + (at ? " · " + at : "")}</span>
  </div>
);

// ---- Camada de entendimento: a FOLHA de explicação ------------------------
// Por que folha (bottom sheet) e não um bloco dentro do card: o AtivoCard já
// afirma 18 coisas (docs/didatica-inventario.md) e o TimingBadge sozinho ocupa
// 3 linhas, entre a manchete de decisão e os chips. Não cabe mais bloco no
// fluxo vertical — e conteúdo que cresce debaixo do polegar de um iniciante,
// numa lista de 6 cards, faz ele tocar no botão errado. A folha abre SOBRE o
// card: não reflui a lista, comporta as três perguntas com folga, e é o mesmo
// gesto para todos os conceitos (uma afordância, não dezoito).
const CONCEITO_BLOCOS = [
  // Ordem deliberada: quem acabou de ver "condição atingida" pergunta antes de
  // tudo se o app comprou alguma coisa. Essa resposta não pode ser a terceira.
  ["naoAcontece", "O QUE O APP NÃO FAZ"],
  ["oQueE", "O QUE É"],
  ["oQueAcontece", "O QUE ACONTECE"],
];

// A AFORDÂNCIA ÚNICA é o padrão do Duolingo: termo explicável carrega um
// SUBLINHADO PONTILHADO e abre a explicação com um TOQUE simples. A versão
// anterior (toque longo) caiu no teste ao vivo por três defeitos que se
// compõem: sem indicação ninguém sabia onde segurar; segurando em qualquer
// lugar, fora dos setores quem respondia era a SELEÇÃO DE TEXTO do sistema;
// e toque longo só funciona com alvo óbvio — num card de texto, nunca é.
// O tap resolve os três: a indicação mora no próprio termo, o gesto é o mais
// universal que existe, e tap não seleciona texto nem compete com rolagem.
//
// SETOR É REGIÃO DECLARADA, não inferência: cada bloco do card se envolve num
// SetorAlvo com um `setorId`; o QUE cada id explica vem do REGISTRO servido
// pelo backend (didatica.setores) — repontear um setor é deploy do Railway,
// não build de iOS. O setor mais interno sob o dedo vence (stopPropagation
// no click: o de fora nem vê o toque).
//
// A convenção visual, aplicada UMA vez por setor (só no termo-âncora):
export const SUBLINHADO = { textDecorationLine: "underline", textDecorationStyle: "dotted", textDecorationColor: T.textFaint, textUnderlineOffset: "3px", textDecorationThickness: "1px" };

// Caminho ACESSÍVEL nomeado: cada setor carrega um botão só-para-leitor
// ("O que é X?") — o VoiceOver lê a pergunta, não o número sublinhado.
const SR_ONLY = { position: "absolute", width: "1px", height: "1px", padding: 0, margin: "-1px", overflow: "hidden", clipPath: "inset(50%)", whiteSpace: "nowrap", border: 0 };

export function SetorAlvo({ setorId, dados, rotulo, A, didatica, ativo = true, style, children }) {
  const cid = (didatica && didatica.ligada && didatica.setores) ? didatica.setores[setorId] : null;
  // Sem registro (camada desligada, backend antigo) ou sem condição a
  // explicar (`ativo`), o setor vira um contêiner comum — toque desarmado.
  if (!cid || !A || !ativo) return <div style={style}>{children}</div>;
  const abrir = (origem) => A.abrirSetor(setorId, cid, dados, origem);
  const onClick = (e) => {
    // setor mais interno vence; o toque não vaza para o card por baixo
    e.stopPropagation();
    abrir("toque");
  };
  return (
    // `userSelect: none` fica: impede o toque duplo apressado de virar
    // seleção. `touchAction` NÃO é tocado — a rolagem segue do sistema.
    <div onClick={onClick}
      style={{ position: "relative", cursor: "pointer", ...style, WebkitTouchCallout: "none", WebkitUserSelect: "none", userSelect: "none" }}>
      {children}
      <button onClick={(e) => { e.stopPropagation(); abrir("botao"); }}
        aria-label={"O que é " + rotulo + "?"} style={SR_ONLY}>?</button>
    </div>
  );
}

// Fase 4 — o ASSISTENTE, dentro da folha do conceito.
// Duas camadas com custos diferentes: a explicação acima é determinística e
// grátis; isto aqui chama LLM. Por isso é opt-in por toque, mostra o que sobra
// do teto do dia, e qualquer falha degrada para "a explicação acima continua
// valendo" — nunca deixa a pessoa sem resposta.
export function AssistenteBox({ cid, dados, setor, tela }) {
  const [aberto, setAberto] = useState(false);
  const [q, setQ] = useState("");
  const [r, setR] = useState(null);
  const [busy, setBusy] = useState(false);
  const [erro, setErro] = useState("");
  const perguntar = async () => {
    const pergunta = q.trim();
    if (!pergunta || busy) return;
    setBusy(true); setErro(""); setR(null);
    try {
      // O snapshot é o MESMO view-model que ancorou a explicação — nada de
      // raspar a tela: o que vai é dado estruturado, auditável.
      // `tela` diz de ONDE a pessoa pergunta: o pet passa a dele pronta;
      // aberta pelo toque no setor é o setor (allowlist no backend); depois
      // de navegar a cadeia, o conceito.
      const res = await store.assistente({ tela: tela || (setor ? "setor:" + setor : "conceito:" + cid), snapshot: dados || {}, pergunta });
      setR(res);
    } catch (e) {
      setErro((e && e.message) || String(e));
    } finally { setBusy(false); }
  };
  if (!aberto) {
    return (
      <button onClick={() => setAberto(true)}
        style={{ width: "100%", minHeight: "44px", marginBottom: "10px", borderRadius: "11px", border: `1px dashed ${T.borderSubtle}`, background: "transparent", color: T.textMuted, fontWeight: 700, fontSize: "12.5px" }}>
        Ainda com dúvida? Pergunte à IA sobre estes números
      </button>
    );
  }
  return (
    <div style={{ marginBottom: "12px", padding: "12px", borderRadius: "11px", background: T.bgBase, border: `1px solid ${T.borderFaint}` }}>
      <div style={{ fontSize: "10px", fontWeight: 800, letterSpacing: "0.08em", color: T.textFaint, marginBottom: "8px" }}>PERGUNTE SOBRE ESTA TELA</div>
      <textarea value={q} onChange={(e) => setQ(e.target.value)} rows={2} maxLength={400}
        placeholder="Ex.: por que o gatilho está nesse preço e não em outro?"
        style={{ width: "100%", boxSizing: "border-box", padding: "10px", borderRadius: "9px", border: `1px solid ${T.borderSubtle}`, background: T.bgPanel, color: T.textPrimary, fontSize: "13px", resize: "vertical" }} />
      <button onClick={perguntar} disabled={busy || !q.trim()}
        style={{ width: "100%", minHeight: "40px", marginTop: "8px", borderRadius: "9px", border: "none", background: busy || !q.trim() ? T.bgPanel : T.accentTint10, color: busy || !q.trim() ? T.textFaint : T.accent, fontWeight: 800, fontSize: "12.5px" }}>
        {busy ? "pensando…" : "Perguntar"}
      </button>
      {erro && (
        <div style={{ marginTop: "9px", fontSize: "12px", color: T.textSecondary, lineHeight: 1.5 }}>
          {erro}
          <div style={{ color: T.textFaint, fontSize: "11px", marginTop: "4px" }}>A explicação acima continua valendo — ela não depende da IA.</div>
        </div>
      )}
      {r && r.texto && (
        <div style={{ marginTop: "10px" }}>
          {/* MESMA resposta de `/api/assistente` que o chat do Boris exibe, e
              ela vem em markdown. Aqui era renderizada crua — o `**negrito**`
              aparecia com os asteriscos. Corrigir só o chat deixou este ponto
              para trás porque são duas superfícies do mesmo endpoint. */}
          <div style={{ fontSize: "13px", color: T.textSecondary, lineHeight: 1.6 }}><Markdown text={r.texto} /></div>
          <AiNote />
          {r.restanteHojeBRL != null && (
            <div style={{ fontSize: "10px", color: T.textFaint, marginTop: "2px" }}>
              Resta hoje ≈ R$ {Number(r.restanteHojeBRL).toFixed(2).replace(".", ",")} de uso da IA.
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function ConceitoSheet({ cid, dados, setor, onClose, onTrocar, didatica, voltar, fonte = "conceito", kbCatalogo = null }) {
  const [c, setC] = useState(null);
  const [erro, setErro] = useState(false);
  useEffect(() => {
    setC(null); setErro(false);
    // Fase 38 (38-03): ramo kb resolve SÍNCRONO, do catálogo já em memória
    // (kb.py via o catálogo de 38-01) — sem rede, sem `store.conceito`. O
    // ramo conceito (fonte ausente ou "conceito") segue byte a byte como
    // antes, nunca refazendo a chamada quando o catálogo kb chega depois.
    if (fonte === "kb") {
      const v = verbeteDoCatalogo(kbCatalogo, cid);
      if (v) setC(v); else setErro(true);
      return;
    }
    let alive = true;
    store.conceito(cid, { dados })
      .then((r) => { if (alive) setC(r); })
      .catch(() => { if (alive) setErro(true); });
    return () => { alive = false; };
  }, [cid, dados, fonte, fonte === "kb" ? kbCatalogo : null]);
  return (
    // zIndex 86: acima de TODOS os outros overlays (tour 75, sobre 80, auth 82,
    // ajuda 84, portão de abertura 85). Esta é a única folha que abre SOZINHA,
    // e a via proativa é one-shot por conceito, para sempre — ficar por baixo
    // significaria queimar a estreia sem ninguém ler nada.
    <div onClick={onClose} role="dialog" aria-label="Explicação"
      style={{ position: "fixed", inset: 0, zIndex: 86, background: T.scrim, display: "flex", alignItems: "flex-end", justifyContent: "center" }}>
      <div onClick={(e) => e.stopPropagation()}
        style={{ width: "100%", maxWidth: "520px", background: T.bgPanel, borderTop: `1px solid ${T.borderSubtle}`, borderRadius: "18px 18px 0 0", padding: "16px 18px calc(18px + env(safe-area-inset-bottom))", maxHeight: "82vh", overflowY: "auto" }}>
        <div style={{ width: "38px", height: "4px", borderRadius: "999px", background: T.borderSubtle, margin: "0 auto 12px" }} aria-hidden />
        {/* A cadeia precisa de volta: quem segue stop → R → gatilho não pode
            ter como única saída fechar tudo e recomeçar. */}
        {voltar && (
          <button onClick={voltar} aria-label="Voltar ao conceito anterior"
            style={{ minHeight: "36px", padding: "0 12px 0 6px", marginBottom: "6px", borderRadius: "999px", border: "none", background: "transparent", color: T.textMuted, fontSize: "12px", fontWeight: 700 }}>‹ voltar</button>
        )}
        {/* Fase 38 (38-03): texto de erro próprio por fonte — do glossário
            não há card ancorando o número, então "o card continua válido"
            não se aplica. */}
        {erro && fonte !== "kb" && <p style={{ margin: 0, fontSize: "13px", color: T.textMuted }}>Não consegui carregar a explicação agora. O card continua válido.</p>}
        {erro && fonte === "kb" && <p style={{ margin: 0, fontSize: "13px", color: T.textMuted }}>Não consegui abrir este verbete agora.</p>}
        {!c && !erro && <div className="sk" style={{ height: "120px", width: "100%" }} />}
        {c && fonte !== "kb" && (
          <>
            <h2 style={{ margin: "0 0 4px", fontSize: "18px", fontWeight: 800, color: T.textPrimary }}>{c.titulo}</h2>
            <div style={{ fontSize: "10.5px", color: T.textFaint, marginBottom: "12px" }}>Explicação com os números deste ativo, agora.</div>
            {CONCEITO_BLOCOS.map(([chave, rotulo]) => (
              (c[chave] || []).length > 0 && (
                <div key={chave} style={{ marginBottom: "14px" }}>
                  <div style={{ fontSize: "10px", fontWeight: 800, letterSpacing: "0.08em", color: chave === "naoAcontece" ? T.negative : T.accent, marginBottom: "6px" }}>{rotulo}</div>
                  {c[chave].map((p, i) => (
                    <p key={i} style={{ margin: "0 0 8px", fontSize: "13.5px", lineHeight: 1.6, color: T.textSecondary }}>{p}</p>
                  ))}
                </div>
              )
            ))}
            {/* VEJA TAMBÉM. Os conceitos deste app se explicam em cadeia —
                gatilho precisa de R, R precisa de stop. Encadear aqui dentro
                evita encher o card de "?" (o inventário conta 18 afirmações) e
                mantém a pessoa no fio do raciocínio em vez de mandá-la caçar. */}
            {(c.veja || []).length > 0 && didatica && (
              <div style={{ display: "flex", flexWrap: "wrap", gap: "7px", margin: "2px 0 14px" }}>
                {c.veja.map((vid) => {
                  const alvo = ((didatica.conceitos || []).find((x) => x && x.id === vid));
                  if (!alvo) return null;
                  return (
                    <button key={vid} onClick={() => onTrocar(vid)}
                      style={{ fontSize: "11.5px", padding: "8px 12px", minHeight: "36px", borderRadius: "999px", border: `1px solid ${T.borderSubtle}`, background: T.bgBase, color: T.textSecondary, fontWeight: 700 }}>
                      {alvo.titulo} →
                    </button>
                  );
                })}
              </div>
            )}
            {/* ASSISTENTE (Fase 4) — a camada PAGA, dentro da folha: é aqui
                que a pessoa já está com a dúvida, e o snapshot é o mesmo que
                ancorou a explicação. Fica atrás de um toque para o custo ser
                sempre uma escolha, nunca um efeito de abrir a tela. */}
            {didatica && didatica.assistente && <AssistenteBox cid={cid} dados={dados} setor={setor} />}
            <button onClick={onClose} style={{ width: "100%", minHeight: "44px", borderRadius: "11px", border: `1px solid ${T.accent}`, background: T.accentTint10, color: T.accent, fontWeight: 800, fontSize: "13px" }}>Entendi</button>
          </>
        )}
        {/* Fase 38 (38-03): ramo GLOSSÁRIO (kb.py) — verbete genérico, sem
            números de nenhum ativo. Por isso: sem AssistenteBox (não há
            snapshot pra "pergunte sobre estes números" cobrar da IA; o chat
            do Boris continua disponível em qualquer aba) e o "veja também"
            resolve no catálogo kb, não em didatica.conceitos. */}
        {c && fonte === "kb" && (
          <>
            <h2 style={{ margin: "0 0 4px", fontSize: "18px", fontWeight: 800, color: T.textPrimary }}>{c.titulo}</h2>
            <div style={{ fontSize: "10.5px", color: T.textFaint, marginBottom: "12px" }}>Verbete do glossário — explicação geral, sem números de nenhum ativo.</div>
            <p style={{ margin: "0 0 8px", fontSize: "13.5px", lineHeight: 1.6, color: T.textSecondary }}>{c.texto}</p>
            {(c.veja || []).length > 0 && (
              <div style={{ display: "flex", flexWrap: "wrap", gap: "7px", margin: "2px 0 14px" }}>
                {c.veja.map((vid) => {
                  const alvo = verbeteDoCatalogo(kbCatalogo, vid);
                  if (!alvo) return null;
                  return (
                    <button key={vid} onClick={() => onTrocar(vid)}
                      style={{ fontSize: "11.5px", padding: "8px 12px", minHeight: "36px", borderRadius: "999px", border: `1px solid ${T.borderSubtle}`, background: T.bgBase, color: T.textSecondary, fontWeight: 700 }}>
                      {alvo.titulo} →
                    </button>
                  );
                })}
              </div>
            )}
            <button onClick={onClose} style={{ width: "100%", minHeight: "44px", borderRadius: "11px", border: `1px solid ${T.accent}`, background: T.accentTint10, color: T.accent, fontWeight: 800, fontSize: "13px" }}>Entendi</button>
          </>
        )}
      </div>
    </div>
  );
}
