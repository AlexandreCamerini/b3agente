// Onda B (2026-10-08, decisão 2) — quick 261008-1ar: trocar de aba desmonta a tela
// anterior (render condicional); em vez de manter abas montadas, o estado que o usuário
// digitou/rodou sobe para uma memória de UI SÓ DA SESSÃO (Map em useRef no App).
// Sem disco (nem localStorage/sessionStorage), sem servidor, sem URL.
// O objeto restaurado é o que o backend entregou, com o carimbo/fonte que ele já
// carrega; nada é recalculado nem inventado.
import { useState, useEffect, useCallback } from "react";

export function lerMemo(memo, chave, inicial, restaurar) {
  if (memo && typeof memo.has === "function" && memo.has(chave)) {
    try {
      return restaurar ? restaurar(memo.get(chave)) : memo.get(chave);
    } catch {
      return inicial;
    }
  }
  return inicial;
}

export function useEstadoMemorizado(memo, chave, inicial, restaurar) {
  const [v, setV] = useState(() => lerMemo(memo, chave, inicial, restaurar));
  // Setter write-through: um scan que termina com a tela já desmontada ainda grava
  // o resultado na memória (o setState em componente desmontado é no-op).
  const set = useCallback((upd) => {
    if (typeof upd === "function") {
      setV((p) => {
        const n = upd(p);
        if (memo) memo.set(chave, n);
        return n;
      });
    } else {
      if (memo) memo.set(chave, upd);
      setV(upd);
    }
  }, [memo, chave]);
  useEffect(() => { if (memo) memo.set(chave, v); }, [memo, chave, v]);
  return [v, set];
}
