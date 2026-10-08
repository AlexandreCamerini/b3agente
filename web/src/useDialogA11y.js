// Onda A (quick 261008-16z, 2026-10-08) — acessibilidade de diálogos modais, no mesmo
// padrão do ConceitoSheet (entendimento.jsx, Fase 48): foco no painel ao abrir, Esc
// fecha, foco devolvido a quem abriu. Extraído aqui só para Buy/Sell/Catalog/Technical;
// ConceitoSheet e PetSheet seguem com a própria cópia (não refatorados de propósito).
//
// Uso: const painelRef = useDialogA11y(true, onClose);
//      <div role="dialog" aria-modal="true" aria-label="…"><div ref={painelRef} tabIndex={-1}>…</div></div>
//
// Pilha de diálogos: com dois abertos (ex.: Indicadores + Compra), o Esc fecha só o do topo.
import { useEffect, useRef } from "react";

const pilha = [];

export function useDialogA11y(aberto, onClose) {
  const painelRef = useRef(null);
  const fecharRef = useRef(onClose);
  fecharRef.current = onClose; // sempre o handler mais recente, sem re-registrar o listener
  useEffect(() => {
    if (!aberto || typeof document === "undefined") return undefined;
    const anterior = document.activeElement;
    const token = {};
    pilha.push(token);
    if (painelRef.current && typeof painelRef.current.focus === "function") painelRef.current.focus();
    const onKey = (e) => {
      if (e.key !== "Escape" || pilha[pilha.length - 1] !== token) return;
      e.stopPropagation();
      if (typeof fecharRef.current === "function") fecharRef.current();
    };
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("keydown", onKey);
      const i = pilha.indexOf(token);
      if (i >= 0) pilha.splice(i, 1);
      if (anterior && typeof anterior.focus === "function" && document.contains(anterior)) anterior.focus();
    };
  }, [aberto]);
  return painelRef;
}
