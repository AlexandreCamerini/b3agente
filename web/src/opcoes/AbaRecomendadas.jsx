/**
 * AbaRecomendadas.jsx — Fase 39 (NAV-01, D-03/D-05), partição de
 * SecaoDescobrir.jsx.
 *
 * Aba 2 das 3 abas fixas: o motor SEM gate de liquidez (Bloco B da extração
 * da Fase 33), com execução INLINE — é aqui que a ação de executar mora
 * depois que a sub-aba "Operar" foi dissolvida (D-05, ver o fork 1 do
 * <objective> de 39-04-PLAN.md). `CuradoriaEstruturas` continua sendo o
 * ÚNICO call site desta pasta (`handleExecutar`/`abertoId`/consentimento de
 * liquidez DIFÍCIL/gate `!operador` seguem intactos dentro dela — nada
 * disso é reimplementado aqui).
 *
 * REORG-07: `curadoria.top`/`curadoria.meta` são consumidos por REFERÊNCIA,
 * nenhuma reordenação/recorte neste arquivo — a seleção é do motor
 * determinístico.
 *
 * A frase-ponte (`cp.duasLeiturasIntro`) NÃO entra aqui: ver o comentário
 * equivalente em `AbaOportunidades.jsx`. `curadoriaSubtitulo` (Plano 39-02)
 * já carrega a negação de hierarquia entre os dois motores, agora dentro da
 * própria aba.
 */
import CuradoriaEstruturas from "./CuradoriaEstruturas.jsx";
import { CarimboFrescor } from "./uiOpcoes.jsx";

export default function AbaRecomendadas({
  curadoria, onAbrir, onExecutar, onNarrar, onRecarregar, operador, palette, cp, infoBotao,
}) {
  const meta = curadoria && curadoria.meta;
  return (
    <>
      <CarimboFrescor at={meta && meta.at} source={meta && meta.source} cp={cp} />
      <CuradoriaEstruturas
        top={(curadoria && curadoria.top) || []}
        meta={meta}
        carregando={!!(curadoria && curadoria.carregando)}
        erro={!!(curadoria && curadoria.erro)}
        concluido={!!(curadoria && curadoria.concluido)}
        narrativa={curadoria && curadoria.narrativa}
        narrando={!!(curadoria && curadoria.narrando)}
        erroNarrativa={curadoria && curadoria.erroNarrativa}
        onNarrar={onNarrar}
        onRecarregar={onRecarregar}
        cp={cp}
        onAbrir={onAbrir}
        onExecutar={onExecutar}
        operador={operador}
        palette={palette}
        infoBotao={infoBotao}
      />
    </>
  );
}
