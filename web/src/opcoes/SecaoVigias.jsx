/**
 * SecaoVigias.jsx — Fase 33 (33-01), extração de OpcoesScreen.jsx.
 *
 * Job 2 do PROJECT.md ("gerenciar vigias") — hoje inline em OpcoesScreen.jsx
 * (`blocoVigias`, `CartaoDeVigia`). Comportamento idêntico, zero
 * funcionalidade nova (D-03 do 33-CONTEXT.md). Recebe TUDO por prop; não
 * não lê o estado bruto nem chama hook de dado nenhum diretamente — só o
 * orquestrador (OpcoesScreen) faz isso (padrão Emenda 3 do ADR-027, já
 * replicado por OportunidadesOpcoes.jsx/CuradoriaEstruturas.jsx na Fase 32).
 */
import { Kicker, Aviso, ErroDoMcp } from "./uiOpcoes.jsx";

// Mesmos NOMES de variável CSS que o núcleo do app injeta em `:root` —
// espelho declarado, mesmo padrão de `OportunidadesOpcoes.jsx:23-25`. Zero
// import do núcleo do app (seria ciclo, ADR-027 Decisão 3).
const VARKEY = (k) => "--" + k.replace(/[A-Z]/g, (c) => "-" + c.toLowerCase());
const TOKENS = ["textSecondary", "textMuted", "accent", "borderSubtle", "accentTint10", "textPrimary", "textFaint"];
const T = Object.fromEntries(TOKENS.map((k) => [k, `var(${VARKEY(k)})`]));

const ehNum = (v) => typeof v === "number" && isFinite(v);
const txt = (v) => (typeof v === "string" && v ? v : "—");

// aba-opcoes F3 (plano 24-02). Alvo de toque de 44 px — espelho declarado de
// OpcoesScreen.jsx (constantes de estilo NÃO saem de lá: guardiões ancoram
// nelas por ser a categoria de espelho aceita neste diretório).
const BOTAO = {
  minHeight: "44px", padding: "10px 14px", borderRadius: "11px",
  border: `1px solid ${T.borderSubtle}`, background: "transparent",
  color: T.textSecondary, fontWeight: 700, fontSize: "13px",
};
// Botão desabilitado FICA VISÍVEL, em vez de sumir: a pessoa precisa ver que
// a ação existe.
const desabilitado = (cond) => (cond ? { opacity: 0.45, cursor: "not-allowed" } : null);

// Fase 27 (27-05) — a SEGUNDA LINHA do botão, onde o custo é declarado. DENTRO
// do botão, não ao lado: o custo tem de viajar junto do alvo de toque.
const CUSTO_NO_BOTAO = {
  display: "block", fontSize: "11px", fontWeight: 600,
  color: T.textMuted, marginTop: "3px",
};

// Fase 27 (27-02) — um cartão do bloco "Seus vigias".
//
// O nome exibido é SEMPRE o nome que a pessoa escreveu (`nome` no índice de
// custo zero, `name` na listagem do dia). O `nomeNoServico` — que carrega os 8
// hexadecimais do hash da conta — NUNCA chega à tela: ele é endereço no
// armazém compartilhado do serviço, não rótulo. Exibi-lo é exatamente o dano
// que a injeção nº 4 do 27-01 mediu ("o hash vira o nome que a pessoa lê").
//
// O cartão é um `<button>` de verdade, e não uma `div` com `onClick`: ele
// navega, e navegação precisa de foco, de Enter e de alvo de toque.
function CartaoDeVigia({ vigia, temEstado, selecionado, naCarteira, onIr, cp }) {
  const v = vigia || {};
  const c = cp || {};
  const nome = txt(v.nome || v.name);
  const alvo = txt(v.ticker);

  // Três estados, e a diferença entre eles é O QUE FOI MEDIDO:
  //  (a) o serviço não conhece mais este vigia → motivo do backend, VERBATIM.
  //      Sumir do armazém é FATO a mostrar, não item a esconder;
  //  (b) o estado do dia foi pedido → `armed`/`streak` como o serviço mediu;
  //  (c) só o índice respondeu → travessão COM motivo. Nunca leitura negativa:
  //      ausência de medição não é medição de ausência — a mesma simetria que
  //      este arquivo já aplica aos setups do ticker.
  const estado = v.motivo ? (
    <span style={{ display: "block", fontSize: "12.5px", color: T.textSecondary, marginTop: "6px", whiteSpace: "pre-wrap", lineHeight: 1.5 }}>
      {v.motivo}
    </span>
  ) : temEstado ? (
    <span style={{ display: "block", fontSize: "12.5px", color: T.textSecondary, marginTop: "6px" }}>
      {"armado: " + (v.armed === true ? "sim" : v.armed === false ? "não" : "—")}
      {" · sequência: " + (ehNum(v.streak) ? v.streak : "—")
        + "/" + (ehNum(v.required_streak) ? v.required_streak : "—")}
    </span>
  ) : (
    <span style={{ display: "block", fontSize: "12.5px", color: T.textMuted, marginTop: "6px", whiteSpace: "pre-wrap", lineHeight: 1.5 }}>
      {c.opcoesVigiasSemEstado || "—"}
    </span>
  );

  return (
    <button
      onClick={() => { if (onIr) onIr(v.ticker); }}
      aria-pressed={!!selecionado}
      aria-label={"Abrir " + alvo + " — vigia " + nome}
      style={{
        display: "block", width: "100%", textAlign: "left", minHeight: "44px",
        border: `1px solid ${selecionado ? T.accent : T.borderSubtle}`,
        borderRadius: "12px", padding: "12px 14px",
        background: selecionado ? T.accentTint10 : T.bgPanel,
      }}
    >
      <span style={{ display: "flex", justifyContent: "space-between", gap: "10px", alignItems: "baseline" }}>
        <span style={{ fontSize: "14px", fontWeight: 700, color: selecionado ? T.accent : T.textPrimary }}>{nome}</span>
        <span style={{ fontSize: "12px", fontWeight: 700, color: T.textMuted }}>{alvo}</span>
      </span>
      {estado}
      {/* Vigia de ativo que saiu da carteira NÃO some: ele existe e continua
          sendo avaliado pelo serviço. Escondê-lo repetiria o defeito desta
          fase — o vigia invisível que parece nunca ter sido gravado. */}
      {naCarteira ? null : (
        <span style={{ display: "block", fontSize: "11.5px", color: T.textMuted, marginTop: "6px", whiteSpace: "pre-wrap", lineHeight: 1.5 }}>
          {c.opcoesVigiaForaDaCarteira || ""}
        </span>
      )}
      {/* Data do índice. Sem data, o motivo do backend — nunca a data de hoje
          no lugar (princípio 4 do CLAUDE.md). */}
      {v.criadoEm || v.motivoCriadoEm ? (
        <span style={{ display: "block", fontSize: "11px", color: T.textFaint, marginTop: "6px" }}>
          {v.criadoEm ? "criado em " + v.criadoEm : v.motivoCriadoEm}
        </span>
      ) : null}
    </button>
  );
}

// Fase 27 (27-02): o bloco que corrige o defeito da fase original. Ele existe
// FORA de qualquer ticker: é isso que faz o vigia gravado aparecer ao abrir a
// aba, em vez de só aparecer com o ativo dele selecionado (27-CONTEXT,
// defeito 2). SEMPRE renderizado pelo orquestrador, com ou sem ativo
// escolhido — é o que faz a aba abrir com conteúdo (D4 da Fase 27).
//
// `listaDeVigias`/`temEstado`/`tickersEmCarteira` chegam PRONTOS por prop: a
// régua de ordenação é do backend (`_ordem_dos_vigias`/`opcoes_vigias.listar`)
// — recalculá-la aqui criaria uma segunda implementação que divergiria da
// primeira em silêncio (mesma razão do comentário original em
// OpcoesScreen.jsx).
export default function SecaoVigias({
  vigias, vigiasVivos, atualizarVigias, listaDeVigias, temEstado,
  tickersEmCarteira, ticker, onIr, custos, cp,
}) {
  const c = cp || {};
  return (
    <div>
      <Kicker>{c.opcoesVigiasTitulo || "SEUS VIGIAS"}</Kicker>
      {/* carregando → erro → vazio com motivo → dados, a mesma cascata do
          resto da tela: lista vazia pintada durante a consulta afirmaria
          "você não tem vigia" sem ninguém ter medido. */}
      {vigias.carregando ? (
        <Aviso>{c.opcoesCarregando || "Consultando o serviço de opções…"}</Aviso>
      ) : vigias.erro ? (
        <ErroDoMcp erro={vigias.erro} cp={cp} />
      ) : listaDeVigias.length === 0 ? (
        <Aviso>{c.opcoesVigiasVazio || "Nenhum vigia gravado nesta conta ainda."}</Aviso>
      ) : (
        <div style={{ display: "grid", gap: "10px" }}>
          {listaDeVigias.map((v, i) => (
            <CartaoDeVigia
              key={(v && v.nomeNoServico ? v.nomeNoServico : "vigia") + "-" + i}
              vigia={v}
              temEstado={temEstado}
              selecionado={!!(v && v.ticker) && v.ticker === ticker}
              naCarteira={!!(v && v.ticker) && tickersEmCarteira.includes(v.ticker)}
              onIr={onIr}
              cp={cp}
            />
          ))}
        </div>
      )}

      {/* O custo vai DENTRO do controle, não ao lado: descobrir que o clique
          custou 2 depois de gastá-las não é aviso, é recibo. `custos` desce do
          orquestrador (`CUSTO_DA_ACAO`) — nunca um `2` digitado aqui. */}
      <button
        onClick={atualizarVigias}
        disabled={vigiasVivos.carregando}
        style={{ ...BOTAO, width: "100%", marginTop: "10px", ...desabilitado(vigiasVivos.carregando) }}
      >
        <span style={{ display: "block" }}>{c.opcoesVigiasAtualizar || "Atualizar o estado dos vigias"}</span>
        <span style={CUSTO_NO_BOTAO}>
          {(c.opcoesCustoChamadas || ((n) => String(n)))(custos.listarVigias)}
        </span>
      </button>

      {vigiasVivos.carregando ? (
        <div style={{ marginTop: "10px" }}>
          <Aviso>{c.opcoesCarregando || "Consultando o serviço de opções…"}</Aviso>
        </div>
      ) : vigiasVivos.erro ? (
        <div style={{ marginTop: "10px" }}>
          <ErroDoMcp erro={vigiasVivos.erro} cp={cp} />
        </div>
      ) : null}
    </div>
  );
}
