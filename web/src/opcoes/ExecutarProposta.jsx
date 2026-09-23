/**
 * ExecutarProposta.jsx — Quick 260923-ndy (Task 2), achado ao vivo do Alex
 * (2026-09-23): em Opções → Analisar, a estrutura que o PRÓPRIO usuário
 * monta ("Montar estrutura" → `proposta.dados.estruturas[0]`) era só
 * leitura — não existia caminho de execução. Este componente fecha o
 * buraco reusando o MESMO despacho já em produção no bloco de curadoria
 * (`ctx.A.executarCandidatoCurado` → `executarCandidato.js`).
 *
 * Espelha o padrão de estado de `CuradoriaEstruturas.jsx` (busy/erro/ok,
 * erro verbatim — princípio 4 do CLAUDE.md, T-J5L-03; consentimento de
 * liquidez por IDENTIDADE, nunca truthiness — T-J5L-04), com uma diferença
 * de forma: aqui há UMA proposta só (não uma lista por `idCandidato`), então
 * o estado amarra à IDENTIDADE de `dados` (premissa 8 do plano da quick) em
 * vez de um dicionário indexado.
 *
 * ZERO conta de negócio neste arquivo: `tipo`/`contractSymbol`/`expiration`/
 * `contratos`/`qtyAcoes` chegam PRONTOS em `dados.execucao`, derivados no
 * backend por `_execucao_da_proposta` (princípio 5 do CLAUDE.md, premissa 2
 * do plano — `contratos` é número de CONTRATOS e o lote do Analisar é em
 * AÇÕES; converter aqui seria a segunda versão da conta que o repositório
 * proíbe).
 *
 * O botão é CONTORNADO (borda `T.accent`, texto `T.accent`, fundo
 * transparente), não preenchido: a Fase 35 (D-04) trava exatamente 3 CTAs
 * preenchidos em Opções (`test_opcoes_jornada_ui.mjs` §11), e este não é um
 * deles — mesmo desenho do botão "narrar" de `CuradoriaEstruturas.jsx`.
 *
 * Pós-sucesso não dispara nova chamada paga (premissa 8): o estado fica
 * amarrado à identidade de `dados` — montar OUTRA estrutura produz um novo
 * objeto `dados.execucao` e o bloco volta ao estado inicial sozinho, sem
 * `useEffect`.
 */
import { useState } from "react";
import { Aviso } from "./uiOpcoes.jsx";

const VARKEY = (k) => "--" + k.replace(/[A-Z]/g, (c) => "-" + c.toLowerCase());
const TOKENS = ["textMuted", "textSecondary", "accent", "warn"];
const T = Object.fromEntries(TOKENS.map((k) => [k, `var(${VARKEY(k)})`]));

// Fonte única do prefixo que o servidor usa na recusa de liquidez DIFÍCIL
// (`server/app/main.py`, `options_lastreada_abrir`/`comprar_put_protecao`/
// `abrir_collar`) — o texto do servidor É o aviso lido, verbatim, antes do
// checkbox de consentimento nascer (premissa 4 do plano da quick). Recusa
// "Liquidez SEM MERCADO" é terminal (sem checkbox) — não começa com este
// prefixo, então cai fora daqui por desenho, não por exceção.
export const PREFIXO_LIQUIDEZ_DIFICIL = "Liquidez DIFÍCIL";

export function ehRecusaLiquidezDificil(msg) {
  return typeof msg === "string" && msg.length > 0 && msg.startsWith(PREFIXO_LIQUIDEZ_DIFICIL);
}

// Estado inicial — constante de MÓDULO (não recriada a cada render), usada
// tanto para o `useState` inicial quanto para o fallback quando `st.ref`
// não bate mais com `dados` (a estrutura mudou, o bloco reseta sozinho).
const INICIAL = { ref: null, busy: false, erro: null, ok: false, aceite: false };

export default function ExecutarProposta({ dados, operador, onExecutar, cp }) {
  const [st, setSt] = useState(INICIAL);

  const ex = dados && dados.execucao;
  if (!ex) return null;

  // Modo Estudo: nenhum botão — o 403 do servidor é a defesa real, esta
  // linha é só a leitura honesta do estado (mesmo gate de
  // CuradoriaEstruturas.jsx:229-236, T-14-23).
  if (!operador) {
    return (
      <div style={{ marginTop: "10px", fontSize: "12px", color: T.textMuted, lineHeight: 1.5, fontStyle: "italic" }}>
        {cp.curadoriaEstudoNaoExecuta}
      </div>
    );
  }

  // Não executável: motivo do backend, verbatim — nenhuma causa composta
  // aqui (princípio 4 do CLAUDE.md, T-NDY-05). Sem `motivo` nenhum, nada
  // é renderizado (silêncio é o estado normal, nunca um travessão mudo
  // inventado).
  if (ex.executavel !== true) {
    if (!ex.motivo) return null;
    return (
      <div style={{ marginTop: "10px" }}>
        <Aviso>{ex.motivo}</Aviso>
      </div>
    );
  }

  // `atual` é o estado, RESETADO em silêncio quando `dados` mudou (nova
  // montagem) — a identidade de `dados` é a chave, não um id explícito.
  const atual = st.ref === dados ? st : INICIAL;

  const cand = {
    tipo: ex.tipo,
    ticker: dados.ticker,
    contractSymbol: ex.contractSymbol,
    expiration: ex.expiration,
    contratos: ex.contratos,
    qtyAcoes: ex.qtyAcoes,
  };

  const handleExecutar = async () => {
    setSt({ ref: dados, busy: true, erro: null, ok: false, aceite: atual.aceite });
    try {
      // `aceitaLiquidezDificil` só entra por IDENTIDADE (`=== true`) — um
      // valor truthy acidental não pode virar consentimento de liquidez
      // DIFÍCIL (T-NDY-04).
      await onExecutar(cand, { aceitaLiquidezDificil: atual.aceite === true });
      setSt({ ref: dados, busy: false, erro: null, ok: true, aceite: atual.aceite });
    } catch (e) {
      // e.message VERBATIM — sem composição/adivinhação de causa (T-NDY-05).
      // Sem reenvio automático: o próximo clique é decisão do usuário.
      setSt({ ref: dados, busy: false, erro: (e && e.message) || String(e), ok: false, aceite: false });
    }
  };

  const recusaLiquidez = ehRecusaLiquidezDificil(atual.erro);
  const travado = atual.busy || (recusaLiquidez && atual.aceite !== true);

  return (
    <div style={{ marginTop: "10px" }}>
      <div style={{ fontSize: "11px", color: T.textMuted, lineHeight: 1.5 }}>
        {cp.opcoesExecucaoSimulada}
      </div>
      {atual.ok ? (
        <div style={{ marginTop: "8px", fontSize: "12px", color: T.textMuted, fontWeight: 700 }}>
          {cp.curadoriaExecutada}
        </div>
      ) : (
        <>
          {recusaLiquidez && (
            <label style={{ display: "flex", alignItems: "flex-start", gap: "8px", marginTop: "8px", fontSize: "11.5px", color: T.textSecondary, lineHeight: 1.5 }}>
              <input
                type="checkbox"
                checked={atual.aceite === true}
                onChange={(e) => setSt({ ref: dados, busy: false, erro: atual.erro, ok: false, aceite: e.target.checked })}
                style={{ marginTop: "2px" }}
              />
              <span>{atual.erro} {cp.curadoriaLiquidezConsentir}</span>
            </label>
          )}
          {!recusaLiquidez && atual.erro && (
            <div style={{ marginTop: "8px", padding: "9px 10px", borderRadius: "8px", border: `1px solid ${T.warn}`, fontSize: "11.5px", color: T.warn, lineHeight: 1.5 }}>
              {atual.erro}
            </div>
          )}
          <button
            type="button"
            onClick={handleExecutar}
            disabled={travado}
            style={{
              marginTop: "8px", minHeight: "44px", width: "100%", padding: "10px 14px",
              borderRadius: "11px", border: `1px solid ${T.accent}`, background: "transparent",
              color: T.accent, fontWeight: 700, fontSize: "13px",
              opacity: travado ? 0.55 : 1, cursor: travado ? "default" : "pointer",
            }}
          >
            {atual.busy ? cp.curadoriaExecutando : cp.curadoriaExecutarCta}
          </button>
        </>
      )}
    </div>
  );
}
