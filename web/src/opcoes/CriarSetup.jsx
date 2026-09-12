/**
 * CriarSetup.jsx — aba-opcoes F5 (ADR-027, plano 24-04, 2026-09-11).
 *
 * A seção que fecha o ciclo da aba: até aqui os setups que a tela mostrava
 * tinham nascido FORA do Boris. A partir desta seção, nascem dentro — a
 * pessoa escreve a condição em português, vê a interpretação do serviço e o
 * ensaio no histórico, e só então grava.
 *
 * Regras que este arquivo NÃO negocia:
 * · **a permissão esconde, o backend recusa.** O render condicionado em
 *   `OpcoesScreen` é conveniência; as três rotas respondem 403 sozinhas
 *   (ADR-013, provado no plano 24-03). Nunca "escondido só na UI";
 * · **nada é gravado sem o ensaio na tela.** O botão de confirmar só existe
 *   dentro do ramo `dry_run`, e manda de volta o MESMO objeto exibido — sem
 *   recompilar, sem LLM;
 * · **o backtest é contagem passada, nunca expectativa.** A ressalva fica
 *   FIXA junto dos números (não é tooltip), e nenhum desses números ganha
 *   cor de ganho ou de perda: não são P&L de posição, são contagem de
 *   histórico. Pintá-los de verde já seria uma promessa;
 * · **`problems` item a item, verbatim.** Quem valida indicador, operador e
 *   janela é o serviço; agregar a lista numa frase apagaria a única
 *   informação acionável que a pessoa tem;
 * · **nenhum vocabulário da DSL vive aqui** (ENG-06 aplicado ao front): as
 *   condições são renderizadas por varredura das chaves que CHEGARAM, nunca
 *   por uma lista de nomes de indicador copiada do serviço. Copiar criaria a
 *   segunda cópia que diverge na primeira mudança do contrato;
 * · `null` vira travessão, nunca 0;
 * · ordem dos estados: carregando → erro → dados.
 *
 * Sem fetch próprio: estado e ações chegam por prop, como `SetupChart` e
 * `PayoffChart` já fazem. Zero import de `App.jsx` (seria ciclo) — o bloco de
 * tokens é local, mesmo padrão dos irmãos desta pasta.
 */
import { useState } from "react";

// Mesmos NOMES de variável CSS que `App.jsx` injeta em `:root`.
const VARKEY = (k) => "--" + k.replace(/[A-Z]/g, (c) => "-" + c.toLowerCase());
const TOKENS = ["bgBase", "bgPanel", "borderSubtle", "borderFaint", "textPrimary",
  "textSecondary", "textMuted", "textFaint", "accent", "accentTint10", "negative", "scrim"];
const T = Object.fromEntries(TOKENS.map((k) => [k, `var(${VARKEY(k)})`]));

const ehNum = (v) => typeof v === "number" && isFinite(v);
const fmt = (v, casas = 2) => (ehNum(v) ? v.toFixed(casas).replace(".", ",") : "—");
const pct = (v, casas = 2) => (ehNum(v) ? fmt(v, casas) + "%" : "—");
const txt = (v) => (typeof v === "string" && v ? v : "—");
const inteiro = (v) => (ehNum(v) ? String(Math.trunc(v)) : "—");

// Mínimo de caracteres para habilitar o disparo. Não é capricho de forma:
// cada compilação gasta uma chamada de LLM paga (chave do servidor no
// caminho gerenciado) mais duas do cap do dia. "oi" não é uma condição, e
// deixar que ela vire uma chamada é cobrar da pessoa por nada.
const MIN_DESCRICAO = 15;

const BOTAO = {
  minHeight: "44px", padding: "10px 14px", borderRadius: "11px",
  border: `1px solid ${T.borderSubtle}`, background: "transparent",
  color: T.textSecondary, fontWeight: 700, fontSize: "13px",
};
const desabilitado = (cond) => (cond ? { opacity: 0.45, cursor: "not-allowed" } : null);
const CAIXA = {
  border: `1px solid ${T.borderSubtle}`, borderRadius: "12px",
  padding: "12px 14px", background: T.bgPanel,
};
const AJUDA = { fontSize: "11px", color: T.textMuted, marginTop: "6px", lineHeight: 1.45 };
const ROTULO = { display: "block", fontSize: "12.5px", color: T.textSecondary, margin: "0 0 4px" };
const CAMPO_TEXTO = {
  width: "100%", boxSizing: "border-box", minHeight: "88px", padding: "10px",
  borderRadius: "10px", border: `1px solid ${T.borderSubtle}`,
  background: T.bgBase, color: T.textPrimary, fontSize: "14px",
  lineHeight: 1.45, fontFamily: "inherit", resize: "vertical",
};
// O `cru` da LLM é texto de TERCEIRO renderizado na página. Nó de texto, com
// `pre-wrap` para preservar as quebras — React escapa sozinho. Nunca
// `dangerouslySetInnerHTML`: a resposta de um modelo não é HTML confiável.
const CRU = {
  whiteSpace: "pre-wrap", wordBreak: "break-word", margin: "8px 0 0",
  padding: "10px", borderRadius: "10px", background: T.bgBase,
  border: `1px solid ${T.borderFaint}`, color: T.textSecondary,
  fontSize: "12px", lineHeight: 1.5, fontFamily: "inherit",
};

function Aviso({ children, tom }) {
  return (
    <div style={{ border: `1px solid ${tom === "forte" ? T.negative : T.borderSubtle}`, borderRadius: "12px", padding: "12px", background: T.bgPanel, color: T.textSecondary, fontSize: "12.5px", whiteSpace: "pre-wrap", lineHeight: 1.5 }}>
      {children}
    </div>
  );
}

function Linha({ rotulo, valor }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", gap: "12px", padding: "7px 0", borderBottom: `1px solid ${T.borderFaint}` }}>
      <span style={{ fontSize: "12.5px", color: T.textSecondary }}>{rotulo}</span>
      <span style={{ fontSize: "12.5px", color: T.textPrimary, fontVariantNumeric: "tabular-nums" }}>{valor}</span>
    </div>
  );
}

// Valor de um campo de condição, seja ele escalar ou o objeto de referência.
// Um nível de profundidade cobre o contrato (`reference: {indicator, window}`)
// e o resto cai num JSON legível — melhor um `[object Object]` nunca aparecer
// do que a tela adivinhar a forma de um campo que ainda não existe.
function valorDeCampo(v) {
  if (v === null || v === undefined || v === "") return "—";
  if (typeof v === "number") return ehNum(v) ? String(v).replace(".", ",") : "—";
  if (typeof v === "boolean") return v ? "sim" : "não";
  if (typeof v === "string") return v;
  if (Array.isArray(v)) return v.map(valorDeCampo).join(", ");
  if (typeof v === "object") {
    return Object.entries(v).map(([k, x]) => k + " " + valorDeCampo(x)).join(" ");
  }
  return String(v);
}

// Uma condição, campo a campo, na ORDEM em que o serviço a mandou. Os nomes
// (`indicator`, `operator`, `window`, `pattern`…) saem como vieram: são o
// vocabulário DELE, e traduzi-los aqui criaria um segundo dicionário que
// diverge do contrato vivo na primeira tool nova (ENG-06).
function condicaoEmTexto(c) {
  if (!c || typeof c !== "object") return "—";
  const partes = Object.entries(c)
    .filter(([, v]) => v !== null && v !== undefined && v !== "")
    .map(([k, v]) => k + ": " + valorDeCampo(v));
  return partes.length ? partes.join(" · ") : "—";
}

export default function CriarSetup({ ticker, estado, onCompilar, onConfirmar, cp }) {
  const c = cp || {};
  const e = estado || {};
  const dados = e.dados;
  const [descricao, setDescricao] = useState("");
  const podeEnviar = descricao.trim().length >= MIN_DESCRICAO && !e.carregando;
  const idAjuda = "opcoes-criar-ajuda";

  return (
    <div style={CAIXA}>
      <label htmlFor="opcoes-criar-descricao" style={ROTULO}>
        {(c.opcoesCriarTitulo || "CRIAR UM SETUP") + (ticker ? " · " + ticker : "")}
      </label>
      <textarea
        id="opcoes-criar-descricao"
        value={descricao}
        onChange={(ev) => setDescricao(ev.target.value)}
        placeholder={c.opcoesCriarPlaceholder || ""}
        aria-describedby={idAjuda}
        style={CAMPO_TEXTO}
      />
      <div id={idAjuda} style={AJUDA}>{c.opcoesCriarAjuda || ""}</div>

      <button
        onClick={() => onCompilar && onCompilar({ descricao: descricao.trim() })}
        disabled={!podeEnviar}
        style={{ ...BOTAO, width: "100%", marginTop: "12px", ...desabilitado(!podeEnviar) }}
      >
        {c.opcoesCriarBotao || "Ver a interpretação e o ensaio"}
      </button>

      {/* carregando → erro → dados. Vazio não tem estado próprio aqui: antes
          do primeiro disparo não há nada a dizer além da ajuda acima, e uma
          caixa "nenhum resultado" antes de qualquer pedido afirmaria uma
          ausência que ninguém mediu. */}
      <div style={{ marginTop: "12px" }}>
        {e.carregando ? (
          <Aviso>{c.opcoesCarregando || "Consultando o serviço de opções…"}</Aviso>
        ) : e.erro ? (
          <>
            <ErroDaCriacao erro={e.erro} cp={c} />
            <RecusaCobradaNaCriacao erro={e.erro} cp={c} />
          </>
        ) : dados && dados.status === "dry_run" ? (
          <Ensaio dados={dados} cp={c} onConfirmar={onConfirmar} />
        ) : dados && dados.status === "inativo" ? (
          <Aviso>{(c.opcoesCriarDesativado || ((n) => "Setup " + n + " desativado."))(dados.name)}</Aviso>
        ) : dados ? (
          /* Qualquer outro status de sucesso é gravação: o contrato diz
             `ativo`, e cravar a string aqui faria a confirmação sumir em
             silêncio se o serviço passar a dizer outra coisa. O nome vem da
             resposta, não do que a tela supôs. */
          <Aviso>{(c.opcoesCriarGravado || ((n) => "Setup " + n + " gravado."))(dados.name)}</Aviso>
        ) : null}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// As duas peças que a cascata acima usa, declaradas DEPOIS do componente —
// mesmo motivo do `ErroDoMcp`/`CODIGOS_ACIONAVEIS` de `OpcoesScreen.jsx`: o
// guardião lê a ORDEM das primeiras ocorrências no fonte para provar que o
// botão de GRAVAR só existe dentro do ramo do ensaio bem-sucedido. Com o
// `Ensaio` declarado acima, o literal do botão apareceria antes do
// `"dry_run"` sem que nada tivesse mudado na tela. Declaração de função é
// içada, então a ordem física não muda a execução.

// 24-08: o aviso de que a recusa consumiu cota, na seção de criação — o
// "Deferred" que o 24-07 registrou por ter esta tela fora dos `files_modified`
// dele.
//
// **Por que a condição aqui NÃO é a mesma do `RecusaCobrada` de
// `OpcoesScreen.jsx`:** lá a regra exige `code === "mcp_erro_de_tool"` E
// `cobrado`, porque naquela tela os 422 de pedido torto (`kind_invalido`,
// `lote_invalido`) são recusa ANTES da rede. Aqui o débito chega por OUTROS
// códigos — `setup_invalido` e `setup_desconhecido` são a mesma viagem
// cobrada, e é justamente o caso comum desta seção. Filtrar por
// `mcp_erro_de_tool` deixaria de fora quase todo caso real.
//
// A regra passa a ser só `detail.cobrado === true`, e isso é seguro porque a
// marca é posta no PONTO DO DÉBITO (`_chamada_com_cap`, 24-07), não montada
// por código de erro: se ela está lá, o contador andou. Não afirmamos débito
// por dedução em lugar nenhum.
//
// Componente local em vez de import: `OpcoesScreen.jsx` importa este arquivo,
// então importar de lá seria ciclo. A duplicação é de 6 linhas e as duas
// regras são deliberadamente diferentes — unificá-las exigiria a condição
// mais frouxa nos dois lados, e o guardião de `test_opcoes_analisar_ui.mjs`
// trava a mais estrita lá por um motivo que continua válido.
function RecusaCobradaNaCriacao({ erro, cp }) {
  const d = (erro && erro.detail && typeof erro.detail === "object") ? erro.detail : {};
  if (d.cobrado !== true) return null;
  // Discreta: é contabilidade, não alarme. Quem precisa agir lê a mensagem
  // do serviço, logo acima.
  return (
    <div style={{ marginTop: "6px", fontSize: "11.5px", color: T.textMuted, lineHeight: 1.5 }}>
      {(cp || {}).opcoesRecusaCobrada
        || "Esta tentativa consumiu uma chamada da sua cota do dia."}
    </div>
  );
}

// A cascata de erro desta seção. Escolhe pelo `code` do backend, nunca
// raspando a mensagem — e cada código tem um estado próprio, porque cada um
// pede uma coisa diferente da pessoa.
function ErroDaCriacao({ erro, cp }) {
  if (!erro) return null;
  const c = cp || {};
  const d = (erro.detail && typeof erro.detail === "object") ? erro.detail : {};

  if (erro.code === "setup_invalido") {
    // VERBATIM, item a item: sem agregar numa frase, sem reordenar, sem
    // traduzir. A lista é do serviço e é o que diz o que corrigir.
    const problems = Array.isArray(d.problems) ? d.problems : [];
    return (
      <Aviso tom="forte">
        {c.opcoesCriarProblemas || "O serviço não aceitou este setup:"}
        {problems.length ? (
          <ul style={{ margin: "8px 0 0", paddingLeft: "18px" }}>
            {problems.map((p, i) => (
              <li key={i} style={{ padding: "2px 0", whiteSpace: "pre-wrap" }}>{String(p)}</li>
            ))}
          </ul>
        ) : (
          <div style={{ marginTop: "8px", whiteSpace: "pre-wrap" }}>{erro.message}</div>
        )}
      </Aviso>
    );
  }

  if (erro.code === "compilacao_invalida") {
    return (
      <Aviso tom="forte">
        {c.opcoesCriarCru || "A IA não devolveu um setup que dê para ler."}
        <pre style={CRU}>{typeof d.cru === "string" ? d.cru : erro.message}</pre>
      </Aviso>
    );
  }

  if (erro.code === "forma_invalida") {
    const faltando = Array.isArray(d.faltando) ? d.faltando : [];
    return (
      <Aviso tom="forte">
        {(c.opcoesCriarFaltando || ((f) => "Faltou: " + (f || []).join(", ")))(faltando)}
        {typeof d.cru === "string" && d.cru ? <pre style={CRU}>{d.cru}</pre> : null}
      </Aviso>
    );
  }

  if (erro.code === "dado_atrasado") {
    // Sem botão de confirmar em lugar nenhum deste ramo: o 409 é exatamente
    // a recusa de gravar, e oferecer o botão convidaria a insistir no que o
    // servidor já negou.
    const idade = ehNum(d.idadeHoras) ? fmt(d.idadeHoras, 0) + " h" : null;
    return (
      <Aviso tom="forte">
        {(c.opcoesDadoAtrasado || (() => erro.message))(idade, d.motivo)}
      </Aviso>
    );
  }

  if (erro.code === "mcp_cota" || erro.code === "mcp_teto_servico") {
    return (
      <Aviso>
        {(c.opcoesCota || ((r) => "Cota esgotada." + (r ? " Reinicia às " + r + "." : "")))(d.reinicia)}
      </Aviso>
    );
  }

  if (erro.code === "mcp_nao_configurado") {
    return <Aviso>{c.opcoesNaoConfigurado || "Serviço de opções não configurado."}</Aviso>;
  }

  if (erro.code === "mcp_indisponivel") {
    return <Aviso>{c.opcoesIndisponivel || "Serviço de opções sem resposta agora."}</Aviso>;
  }

  // Inclui `plano_analises`, `ia_gerenciada`, `descricao_longa`,
  // `setup_desconhecido` e o que mais vier: o backend já manda a mensagem
  // pronta, com "Como corrigir:"/"Dica:" quando existem. Vai CRUA, em nó de
  // texto com pre-wrap (React escapa).
  return <Aviso tom="forte">{erro.message}</Aviso>;
}

// O ensaio: o que o serviço ENTENDEU + o backtest. Nenhum número é
// recalculado aqui, e nenhum deles ganha cor — ver o cabeçalho do arquivo.
function Ensaio({ dados, cp, onConfirmar }) {
  const c = cp || {};
  const setup = (dados && dados.setup && typeof dados.setup === "object") ? dados.setup : {};
  const backtest = (dados && dados.backtest && typeof dados.backtest === "object") ? dados.backtest : null;
  const ensaio = (dados && dados.ensaio && typeof dados.ensaio === "object") ? dados.ensaio : null;
  const condicoes = Array.isArray(setup.conditions) ? setup.conditions : [];
  const periodo = (backtest && backtest.periodo && typeof backtest.periodo === "object") ? backtest.periodo : {};
  const retornos = (backtest && backtest.retorno_apos_disparo && typeof backtest.retorno_apos_disparo === "object")
    ? Object.entries(backtest.retorno_apos_disparo) : [];

  return (
    <div>
      <div style={{ ...CAIXA, padding: "4px 14px 10px" }}>
        <Linha rotulo="Nome" valor={txt(setup.name)} />
        <Linha rotulo="Ativo" valor={txt(setup.ticker)} />
        <Linha rotulo="logic" valor={txt(setup.logic)} />
        <Linha
          rotulo="consecutive_days"
          valor={ehNum(setup.consecutive_days) ? inteiro(setup.consecutive_days) : "—"}
        />
      </div>

      {condicoes.length ? (
        <ul style={{ margin: "10px 0 0", padding: 0, listStyle: "none" }}>
          {condicoes.map((cond, i) => (
            <li key={i} style={{ fontSize: "12.5px", color: T.textSecondary, padding: "4px 0", borderBottom: `1px solid ${T.borderFaint}`, wordBreak: "break-word" }}>
              {condicaoEmTexto(cond)}
            </li>
          ))}
        </ul>
      ) : (
        <div style={AJUDA}>O serviço devolveu este setup sem condição listada. Nada foi suposto no lugar.</div>
      )}

      {/* ACIMA dos números, nunca abaixo: quem lê "0 disparos" primeiro já
          formou a conclusão, e uma ressalva que chega depois disso chega
          tarde. */}
      <EnsaioInconclusivo ensaio={ensaio} cp={c} />

      {backtest ? (
        <div style={{ marginTop: "14px" }}>
          <div style={{ fontSize: "11px", fontWeight: 800, letterSpacing: ".06em", color: T.textMuted, marginBottom: "6px" }}>
            {c.opcoesBacktestTitulo || "ENSAIO NO HISTÓRICO"}
          </div>
          <div style={{ ...CAIXA, padding: "4px 14px 10px" }}>
            <Linha
              rotulo="Período"
              valor={txt(periodo.de) + " – " + txt(periodo.ate)
                + (ehNum(periodo.pregoes) ? " (" + inteiro(periodo.pregoes) + " pregões)" : "")}
            />
            <Linha rotulo="Pregões avaliáveis" valor={inteiro(backtest.pregoes_avaliaveis)} />
            <Linha rotulo="Pregões sem indicador" valor={inteiro(backtest.pregoes_sem_indicador)} />
          </div>
          <div style={{ fontSize: "12.5px", color: T.textSecondary, marginTop: "8px", lineHeight: 1.5 }}>
            {(c.opcoesBacktestDisparos || ((n, p) => n + " disparo(s), " + p + " a cada 100"))(
              ehNum(backtest.disparos) ? inteiro(backtest.disparos) : null,
              ehNum(backtest.disparos_por_100_pregoes_avaliaveis)
                ? fmt(backtest.disparos_por_100_pregoes_avaliaveis, 1)
                : null)}
          </div>
          {retornos.map(([passo, r]) => {
            const v = (r && typeof r === "object") ? r : {};
            return (
              <div key={passo} style={{ fontSize: "12.5px", color: T.textSecondary, marginTop: "6px", lineHeight: 1.5 }}>
                {(c.opcoesBacktestRetorno || ((p, m, md, cd) => p + ": " + m + " / " + md))(
                  passo,
                  ehNum(v.retorno_medio_pct) ? pct(v.retorno_medio_pct, 2) : null,
                  ehNum(v.retorno_mediano_pct) ? pct(v.retorno_mediano_pct, 2) : null,
                  ehNum(v.com_dado) ? inteiro(v.com_dado) : null)}
              </div>
            );
          })}
          {/* Ressalva FIXA, no mesmo bloco dos números — não é tooltip nem
              fica atrás de um toque. É ela que impede a leitura errada dos
              três números acima, e uma ressalva que precisa ser procurada
              não protege ninguém. */}
          <div style={{ ...AJUDA, marginTop: "10px" }}>{c.opcoesBacktestRessalva || ""}</div>
        </div>
      ) : (
        <div style={AJUDA}>O serviço não devolveu ensaio no histórico para este setup. Nada foi estimado no lugar.</div>
      )}

      <button
        onClick={() => onConfirmar && onConfirmar(dados.setup)}
        style={{ ...BOTAO, width: "100%", marginTop: "14px" }}
      >
        {c.opcoesCriarConfirmar || "Gravar este setup"}
      </button>
    </div>
  );
}

// 24-14 — a faixa que diz, ANTES dos números, que o ensaio não testou nada.
//
// Achado ao vivo (2026-09-11): um setup com média de 200 sobre 48 pregões
// devolve `disparos: 0` com `pregoes_avaliaveis: 31`. Os dois números estão
// certos; o que engana é a leitura — "testei e não disparou" quando a verdade
// é "nunca pôde disparar". E é pior que campo vazio (24-11): vazio se vê,
// número plausível não. O fim da linha é alguém GRAVAR um setup acreditando
// que ele foi validado contra o histórico.
//
// Três coisas que este componente não negocia:
// · a posição. Vem acima dos números, e não é tooltip nem fica atrás de um
//   toque — ressalva que precisa ser procurada não protege ninguém;
// · o motivo é do BACKEND e viaja verbatim, como ARGUMENTO da função de copy.
//   Reescrevê-lo aqui criaria a segunda cópia da frase, a que envelhece sem
//   ninguém notar (padrão do 24-11);
// · o botão de gravar CONTINUA existindo nos dois casos. Não é a tela que
//   decide o que a pessoa pode fazer com um setup que ela escreveu; o que a
//   tela deve é não deixá-la concluir errado. Bloquear trocaria um problema
//   de informação por um de autonomia.
//
// O veredito forte só sai com `indisparavel === true` — o backend o reserva
// ao caso demonstrável. Quando há condição listada sem veredito (lógica `OR`,
// ou janela curta para a sequência), a faixa é ressalva, em tom discreto.
function EnsaioInconclusivo({ ensaio, cp }) {
  const c = cp || {};
  const e = (ensaio && typeof ensaio === "object") ? ensaio : {};
  const itens = (Array.isArray(e.condicoes) ? e.condicoes : [])
    .filter((x) => x && typeof x === "object");
  // Sem `ensaio` no payload (servidor anterior a este plano) ou sem condição
  // problemática, nada é renderizado: o estado normal é silêncio, e uma caixa
  // vazia afirmaria uma ausência que ninguém mediu.
  if (!itens.length) return null;
  const veredito = e.indisparavel === true;
  return (
    <div style={{ marginTop: "12px" }}>
      <Aviso tom={veredito ? "forte" : undefined}>
        {veredito
          ? (c.opcoesEnsaioIndisparavel
            || "Este ensaio não testou o setup: uma das condições não pôde ser verificada no histórico.")
          : (c.opcoesEnsaioRessalva
            || "Uma condição deste setup não pôde ser verificada em todo o período do ensaio.")}
        <ul style={{ margin: "8px 0 0", paddingLeft: "18px" }}>
          {itens.map((x, i) => (
            <li key={i} style={{ padding: "2px 0", whiteSpace: "pre-wrap" }}>
              {(c.opcoesEnsaioCondicao
                || ((ind, jan, mot) => String(ind || "—") + ": " + String(mot || "—")))(
                x.indicador, x.janela, x.motivo)}
            </li>
          ))}
        </ul>
      </Aviso>
    </div>
  );
}

/**
 * Desativar em DOIS toques: o botão vira "confirmar a desativação" antes de
 * agir. Desativar é ação de estado sobre um vigia que já existe, e um toque
 * acidental na lista pararia a vigilância sem a pessoa perceber — o tipo de
 * falha que só se descobre no dia em que o setup deveria ter disparado.
 *
 * Mora neste arquivo (e não em `OpcoesScreen`) porque é a única outra ação de
 * ESCRITA de setup: as duas nascem e mudam juntas.
 */
export function BotaoDesativar({ nome, onDesativar, cp, ocupado }) {
  const c = cp || {};
  const [confirmando, setConfirmando] = useState(false);
  const rotulo = confirmando
    ? (c.opcoesCriarConfirmarDesativacao || "Confirmar a desativação")
    : (c.opcoesCriarDesativar || "Desativar este setup");
  return (
    <button
      onClick={() => {
        if (!confirmando) { setConfirmando(true); return; }
        setConfirmando(false);
        if (onDesativar) onDesativar(nome);
      }}
      disabled={!!ocupado}
      aria-label={rotulo + " " + (nome || "")}
      style={{ ...BOTAO, width: "100%", marginTop: "8px", ...desabilitado(!!ocupado), ...(confirmando ? { borderColor: T.negative, color: T.negative } : null) }}
    >
      {rotulo}
    </button>
  );
}
