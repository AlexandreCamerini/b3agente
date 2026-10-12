// Folha de tela cheia do guia das telas (quick 261011-l5x). Vive DENTRO do bundle: offline no
// iOS (Capacitor carrega o bundle local, sem server.url) e sem abrir janela externa.
//
// Dados: os MESMOS de site/js/telas-data.js (guiaTelas.js). Toda a lógica de navegação, progresso
// e layout está em guiaNav.js (puro, testado); aqui só há apresentação. Fechamento: o App monta
// esta folha em perfilView === "guia", então o voltar do sistema e o swipe de borda (Onda B/J)
// já a fecham via subirNivel; Esc e o botão ✕ chamam onClose.
//
// Guia ÚNICO de treinamento (quick 261012-09v). Três entradas, mesma folha:
//  - Perfil → Ajuda → Guia de treinamento: sem `abertura` (primeira tela não concluída).
//  - Bóris ("Me mostra esta tela"): `abertura` = {id, visao:true, n} — abre na tela
//    correspondente, começando pelo cartão "Visão geral" (ponto -1); id sem tour mostra o
//    aviso "Esta tela ainda não tem tour." (nunca falha calado). O App liga `key` a `n`
//    para remontar a folha a cada toque, mesmo com o guia já aberto.
//  - 1º uso: o App monta a folha na camada "tour" (tourOpen) com ABERTURA_PRIMEIRO_USO
//    (Boas-vindas, sem Visão geral); fechar grava `tourSeen` (A.closeTour).
// Texto só como nó React (nenhum HTML injetado). Sem import de App.jsx.
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { GUIA_TELAS, urlDaCaptura } from "./guiaTelas.js";
import {
  proximo, anterior, irParaTela, rotuloSeletor, carregarProgresso, serializarProgresso, telaConcluida,
  layoutGuia, enquadrar, ehSwipeHorizontal, estadoInicialGuia, TOPO_PX, RODAPE_PX, CHAVE_PROGRESSO,
} from "./guiaNav.js";
import { useDialogA11y } from "./useDialogA11y.js";
import { DISCLAIMERS } from "./disclaimers.js";

const FOCAVEIS = 'button:not([disabled]), select:not([disabled]), input:not([disabled]), [tabindex]:not([tabindex="-1"])';

function lerProgresso() {
  try { return carregarProgresso(globalThis.localStorage && globalThis.localStorage.getItem(CHAVE_PROGRESSO)); } catch { return carregarProgresso(null); }
}
function gravarProgresso(p) {
  try { globalThis.localStorage && globalThis.localStorage.setItem(CHAVE_PROGRESSO, serializarProgresso(p)); } catch { /* segue sem persistir */ }
}
function dimensoesNaturais(t) {
  return t.kind === "w" ? { natW: 800, natH: t.nh || 500 } : { natW: 780, natH: t.nh || 1688 };
}

const btnSeta = (desab) => ({
  width: "44px", height: "44px", borderRadius: "10px", border: "1px solid var(--border-subtle)",
  background: "var(--bg-panel)", color: "var(--text-primary)", fontSize: "22px", lineHeight: 1,
  opacity: desab ? 0.4 : 1, display: "flex", alignItems: "center", justifyContent: "center",
});

export default function GuiaTelas({ onClose, abertura = null }) {
  const painelRef = useDialogA11y(true, onClose);
  const raizRef = useRef(null);
  const medidaRef = useRef(null);
  const [prog, setProg] = useState(lerProgresso);
  // Estado inicial lido UMA vez (a abertura nova chega por `key`, que remonta a folha).
  const [inicial] = useState(() => estadoInicialGuia(GUIA_TELAS, lerProgresso(), abertura));
  const [e, setE] = useState({ tela: inicial.tela, ponto: inicial.ponto });
  const [avisoSemTour, setAvisoSemTour] = useState(inicial.semTour);
  const [medida, setMedida] = useState({ vw: 375, vh: 600 });
  const [escolha, setEscolha] = useState({}); // {idTela: índice da opção marcada}
  const reduzMovimento = useMemo(
    () => typeof window !== "undefined" && !!window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches,
    [],
  );

  // Mede a área útil (já descontando safe-area) — o layout é calculado em px por guiaNav.
  useLayoutEffect(() => {
    const el = medidaRef.current;
    if (!el) return undefined;
    const ler = () => setMedida({ vw: el.clientWidth, vh: el.clientHeight });
    ler();
    let ro = null;
    if (typeof ResizeObserver !== "undefined") { ro = new ResizeObserver(ler); ro.observe(el); }
    window.addEventListener("resize", ler);
    return () => { if (ro) ro.disconnect(); window.removeEventListener("resize", ler); };
  }, []);

  const t = GUIA_TELAS[e.tela];
  const n = t.pontos.length;
  const naPratica = e.ponto >= n;
  const visaoGeral = e.ponto < 0;
  const ponto = naPratica || visaoGeral ? null : t.pontos[e.ponto];
  const L = layoutGuia(medida.vw, medida.vh);
  const { natW, natH } = dimensoesNaturais(t);
  const cam = enquadrar(ponto, natW, natH, L.captura.width, L.captura.height);
  const src = urlDaCaptura(t.img);
  const ultimo = e.tela === GUIA_TELAS.length - 1 && naPratica;
  const primeiro = e.tela === 0 && e.ponto <= 0;

  // Primeira navegação limpa o aviso "sem tour".
  const ir = useCallback((fn) => { setAvisoSemTour(false); setE((x) => fn(x, GUIA_TELAS)); }, []);

  // Trap de Tab dentro da folha (useDialogA11y não prende Tab).
  const aoTeclar = (ev) => {
    if (ev.key !== "Tab" || !raizRef.current) return;
    const lista = Array.from(raizRef.current.querySelectorAll(FOCAVEIS)).filter((x) => x.offsetParent !== null || x === document.activeElement);
    if (!lista.length) return;
    const primeiroEl = lista[0], ultimoEl = lista[lista.length - 1];
    if (ev.shiftKey && (document.activeElement === primeiroEl || document.activeElement === raizRef.current)) { ev.preventDefault(); ultimoEl.focus(); }
    else if (!ev.shiftKey && document.activeElement === ultimoEl) { ev.preventDefault(); primeiroEl.focus(); }
  };

  const toque = useRef(null);
  const aoComecarToque = (ev) => {
    const tg = ev.target;
    if (ev.touches.length !== 1 || (tg && tg.closest && tg.closest("input,label,select,textarea"))) { toque.current = null; return; }
    toque.current = { x0: ev.touches[0].clientX, y0: ev.touches[0].clientY };
  };
  const aoTerminarToque = (ev) => {
    const ini = toque.current; toque.current = null;
    if (!ini || !ev.changedTouches[0]) return;
    const r = ehSwipeHorizontal({ ...ini, x1: ev.changedTouches[0].clientX, y1: ev.changedTouches[0].clientY });
    if (r === "proximo") ir(proximo); else if (r === "anterior") ir(anterior);
  };

  // Ao trocar de tela/ponto, a folha volta ao topo.
  const folhaRef = useRef(null);
  useEffect(() => { if (folhaRef.current) folhaRef.current.scrollTop = 0; }, [e.tela, e.ponto]);

  const marcarMissao = (v) => {
    const novo = { ...prog, mis: { ...prog.mis, [t.id]: v } };
    setProg(novo); gravarProgresso(novo);
  };
  const responder = (j) => {
    setEscolha((x) => ({ ...x, [t.id]: j }));
    if (j === t.quiz.a) { const novo = { ...prog, q: { ...prog.q, [t.id]: true } }; setProg(novo); gravarProgresso(novo); }
  };
  const marcada = prog.q[t.id] ? t.quiz.a : escolha[t.id];

  const grupos = [];
  GUIA_TELAS.forEach((x, i) => {
    let g = grupos.find((y) => y.nome === x.grupo);
    if (!g) { g = { nome: x.grupo, itens: [] }; grupos.push(g); }
    g.itens.push([x, i]);
  });

  return (
    <div
      ref={(el) => { raizRef.current = el; painelRef.current = el; }}
      role="dialog" aria-modal="true" aria-label="Guia das telas" tabIndex={-1}
      onKeyDown={aoTeclar}
      style={{ position: "fixed", inset: 0, zIndex: 1100, background: "var(--bg-base)", color: "var(--text-primary)", outline: "none" }}
    >
      <div ref={medidaRef} style={{ position: "absolute", left: 0, right: 0, top: "env(safe-area-inset-top)", bottom: "env(safe-area-inset-bottom)" }}>
        {/* Topo (44px): seletor "3/22 ▾" + título + ✕ */}
        <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: `${TOPO_PX}px`, display: "flex", alignItems: "center", gap: "8px", padding: "0 4px 0 8px", borderBottom: "1px solid var(--border-subtle)" }}>
          <div style={{ position: "relative", minWidth: "72px", height: "44px", flex: "none" }}>
            <span aria-hidden style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 800, fontSize: "14px", color: "var(--accent)", border: "1px solid var(--border-subtle)", borderRadius: "10px", background: "var(--bg-panel)" }}>
              {rotuloSeletor(e, GUIA_TELAS)} ▾
            </span>
            <select
              aria-label="Escolher tela" value={e.tela}
              onChange={(ev) => { setAvisoSemTour(false); setE((x) => irParaTela(x, Number(ev.target.value), GUIA_TELAS)); }}
              style={{ position: "absolute", inset: 0, width: "100%", height: "100%", opacity: 0, fontSize: "16px" }}
            >
              {grupos.map((g) => (
                <optgroup key={g.nome} label={g.nome}>
                  {g.itens.map(([x, i]) => (
                    <option key={x.id} value={i}>{(i + 1) + ". " + x.titulo + (telaConcluida(prog, x.id) ? " ✓" : "")}</option>
                  ))}
                </optgroup>
              ))}
            </select>
          </div>
          <div style={{ flex: 1, minWidth: 0, fontWeight: 700, fontSize: "15px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{t.titulo}</div>
          <button type="button" aria-label="Fechar guia" onClick={onClose}
            style={{ width: "44px", height: "44px", flex: "none", border: "none", background: "transparent", color: "var(--text-secondary)", fontSize: "20px" }}>✕</button>
        </div>

        {/* Captura: a câmera dá zoom no ponto; o resto escurece. Sem cartão de vidro por cima. */}
        <div style={{ position: "absolute", top: L.captura.top, left: L.captura.left, width: L.captura.width, height: L.captura.height, overflow: "hidden", background: "var(--bg-panel)" }}
          onTouchStart={aoComecarToque} onTouchEnd={aoTerminarToque}>
          {src ? (
            <img src={src} alt={t.alt} draggable={false}
              style={{ position: "absolute", left: 0, top: 0, width: cam.w, height: cam.h, maxWidth: "none", transform: `translate(${cam.tx}px, ${cam.ty}px)`, transition: reduzMovimento ? "none" : "transform .35s ease", userSelect: "none" }} />
          ) : (
            <div style={{ padding: "16px", color: "var(--text-muted)", fontSize: "13px" }}>Captura indisponível.</div>
          )}
          {cam.spot && (
            <div aria-hidden style={{ position: "absolute", left: cam.spot.left, top: cam.spot.top, width: cam.spot.width, height: cam.spot.height, borderRadius: "8px", border: "2px solid var(--accent)", boxShadow: "0 0 0 9999px rgba(0,0,0,.55)", pointerEvents: "none", transition: reduzMovimento ? "none" : "all .35s ease" }} />
          )}
        </div>

        {/* Folha: ponto atual ou cartão "Na prática" */}
        <div ref={folhaRef} style={{ position: "absolute", top: L.folha.top, left: L.folha.left, width: L.folha.width, height: L.folha.height, overflowY: "auto", padding: "12px 16px", borderTop: L.lado ? "none" : "1px solid var(--border-subtle)", borderLeft: L.lado ? "1px solid var(--border-subtle)" : "none", background: "var(--bg-base)" }}
          onTouchStart={aoComecarToque} onTouchEnd={aoTerminarToque}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "8px", marginBottom: "6px" }}>
            <div style={{ fontSize: "11px", fontWeight: 800, letterSpacing: "0.05em", color: "var(--text-muted)" }}>
              {visaoGeral ? "VISÃO GERAL" : naPratica ? "NA PRÁTICA" : `PONTO ${e.ponto + 1} DE ${n}`}
            </div>
            <div style={{ display: "flex", gap: "8px" }}>
              <button type="button" aria-label="Ponto anterior" disabled={primeiro} onClick={() => ir(anterior)} style={btnSeta(primeiro)}>‹</button>
              <button type="button" aria-label="Próximo ponto" disabled={ultimo} onClick={() => ir(proximo)} style={btnSeta(ultimo)}>›</button>
            </div>
          </div>

          {avisoSemTour && (
            <div role="status" style={{ marginBottom: "10px", padding: "8px 10px", borderRadius: "8px", border: "1px solid var(--border-subtle)", fontSize: "13px", lineHeight: 1.45, color: "var(--text-secondary)" }}>
              <b style={{ color: "var(--text-primary)" }}>Esta tela ainda não tem tour.</b>{" "}Use o seletor no topo para escolher outra.
            </div>
          )}

          {visaoGeral ? (
            <div aria-live="polite">
              <div style={{ fontWeight: 800, fontSize: "17px", marginBottom: "6px" }}>{t.titulo}</div>
              <p style={{ margin: 0, fontSize: "14px", lineHeight: 1.55, color: "var(--text-secondary)" }}>{t.visao}</p>
            </div>
          ) : !naPratica ? (
            <div aria-live="polite">
              <div style={{ fontWeight: 800, fontSize: "17px", marginBottom: "6px" }}>{ponto.titulo}</div>
              <p style={{ margin: 0, fontSize: "14px", lineHeight: 1.55, color: "var(--text-secondary)" }}>{ponto.texto}</p>
            </div>
          ) : (
            <div>
              <div style={{ fontWeight: 800, fontSize: "15px", marginBottom: "4px" }}>{t.objetivo}</div>
              <label style={{ display: "flex", alignItems: "flex-start", gap: "10px", minHeight: "44px", padding: "8px 0", fontSize: "14px", lineHeight: 1.45, color: "var(--text-secondary)" }}>
                <input type="checkbox" checked={!!prog.mis[t.id]} onChange={(ev) => marcarMissao(ev.target.checked)} style={{ width: "22px", height: "22px", flex: "none", marginTop: "1px" }} />
                <span><b style={{ color: "var(--text-primary)" }}>Missão: </b>{t.missao}</span>
              </label>
              <fieldset style={{ border: "none", padding: 0, margin: "6px 0 0" }}>
                <legend style={{ fontWeight: 700, fontSize: "14px", padding: 0, marginBottom: "4px" }}>{t.quiz.q}</legend>
                {t.quiz.o.map((txt, j) => (
                  <label key={j} style={{ display: "flex", alignItems: "center", gap: "10px", minHeight: "44px", fontSize: "14px", color: "var(--text-secondary)" }}>
                    <input type="radio" name={"q-" + t.id} checked={marcada === j} onChange={() => responder(j)} style={{ width: "20px", height: "20px", flex: "none" }} />
                    <span>{txt}</span>
                  </label>
                ))}
                <div role="status" style={{ fontSize: "13px", lineHeight: 1.45, minHeight: "20px", color: marcada === t.quiz.a ? "var(--positive)" : "var(--negative)" }}>
                  {marcada == null ? "" : marcada === t.quiz.a ? "Correto. " + t.quiz.why : "Ainda não. Releia os pontos e tente outra opção."}
                </div>
              </fieldset>
            </div>
          )}
        </div>

        {/* Rodapé único: o aviso do guia mora aqui, não em cada ponto. */}
        <div style={{ position: "absolute", top: L.rodape.top, left: 0, right: 0, height: `${RODAPE_PX}px`, display: "flex", alignItems: "center", justifyContent: "center", padding: "0 12px", fontSize: "11px", color: "var(--text-muted)", borderTop: "1px solid var(--border-subtle)", background: "var(--bg-base)" }}>
          {DISCLAIMERS.short}
        </div>
      </div>
    </div>
  );
}
