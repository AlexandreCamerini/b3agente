// Onda K (2026-10-10, quick 261010-f51): estado do cartão "Operador IA" (Portfólio + Acompanhar).
// Espelha a regra do card-herói do AgenteScreen (App.jsx): o front só lê data.agent / login / modo;
// nada é calculado aqui além do rótulo. Sem I/O, sem número. "ligado" descreve a CONFIGURAÇÃO
// (serverEnabled && logado), nunca "rodando" — kill-switch global e último ciclo só existem em
// /api/agent/status e ficam fora do cartão (decisão pendente).
export function estadoOperadorIA({ agent, logado, operador } = {}) {
  if (!agent || typeof agent !== "object") return { codigo: "indisponivel", modo: null };
  if (!logado) return { codigo: "semConta", modo: null };
  const bruto = operador ? (agent.mode || (agent.autonomous ? "executar" : "sinalizar")) : "sinalizar";
  const modo = bruto === "executar" ? "executar" : "sinalizar";
  return { codigo: agent.serverEnabled ? "ligado" : "desligado", modo };
}
