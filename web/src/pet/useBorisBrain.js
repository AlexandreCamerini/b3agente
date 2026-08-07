/**
 * useBorisBrain.js — F5: estado de uma conversa MULTI-TURNO com o Boris.
 *
 * Não é o `useBorisBrain` do anexo original (Downloads/BorisWidget.jsx): aquele
 * falava um protocolo próprio (`POST {message,history,client} -> {reply,react}`)
 * que não bate com o `/api/assistente` real. Este fala com `store.assistente`
 * de verdade — o MESMO contrato que `AssistenteBox` (pergunta única) já usa,
 * só que agora carregando `historico` a cada pergunta nova.
 *
 * O histórico que sobe é só o que JÁ foi trocado nesta conversa — as últimas
 * `MAX_HISTORICO` mensagens (pergunta + resposta, intercaladas). O backend
 * (`server/app/assistente.py: _historico_txt`) aplica o MESMO teto e um teto
 * de caracteres por cima; mandar mais daqui não adianta e só infla o corpo.
 */
import { useCallback, useRef, useState } from "react";
import { store } from "../persistence.js";

const MAX_HISTORICO = 6;

export function useBorisBrain({ tela, snapshot } = {}) {
  const [mensagens, setMensagens] = useState([]); // { papel: "usuario"|"boris", texto, fonte?, restanteHojeBRL? }
  const [pensando, setPensando] = useState(false);
  const [erro, setErro] = useState("");
  // ref espelha `mensagens` para montar o histórico sem depender do closure
  // stale da última renderização (a pergunta e a resposta anterior já
  // precisam estar aqui quando a PRÓXIMA pergunta sai).
  const mensagensRef = useRef(mensagens);
  mensagensRef.current = mensagens;

  const enviar = useCallback(async (perguntaBruta) => {
    const pergunta = String(perguntaBruta || "").trim();
    if (!pergunta || pensando) return null;
    setErro("");
    setMensagens((m) => [...m, { papel: "usuario", texto: pergunta }]);
    setPensando(true);
    // Só os turnos JÁ trocados ANTES desta pergunta — ela mesma entra no
    // corpo como `pergunta`, não como último item do histórico.
    const historico = mensagensRef.current
      .slice(-MAX_HISTORICO)
      .map((m) => ({ papel: m.papel, texto: m.texto }));
    try {
      const res = await store.assistente({ tela, snapshot: snapshot || {}, pergunta, historico });
      const resposta = {
        papel: "boris",
        texto: (res && res.texto) || "",
        fonte: res && res.fonte,
        restanteHojeBRL: res && res.restanteHojeBRL,
      };
      setMensagens((m) => [...m, resposta]);
      return resposta;
    } catch (e) {
      setErro((e && e.message) || String(e));
      return null;
    } finally {
      setPensando(false);
    }
  }, [tela, snapshot, pensando]);

  const limpar = useCallback(() => { setMensagens([]); setErro(""); }, []);

  return { mensagens, enviar, pensando, erro, limpar };
}
