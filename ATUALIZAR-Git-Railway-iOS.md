# ATUALIZAR — Git · Railway · iOS
**Entrega:** Fase 0 (proposta UX, gate) + Fase 1 (pipeline IA em 3 níveis, backend)
**Data:** 2026-07-02 · **Pré-requisito:** entrega anterior (fix SQLite threads) aplicada e validada.

## O que esta entrega contém
| Item | Arquivo(s) |
|---|---|
| Espec das análises (skill analise-tecnica-b3, determinístico × LLM) | `ESPEC-Analises-Tecnicas.md` |
| Proposta de UX ✋ GATE (aguarda sua aprovação) | `PROPOSTA-UX.md` |
| N1: deep scan do Radar | `server/app/scan_deep.py` (novo) + endpoints em `main.py` |
| N2: ADX/DI±, padrões de candle, famílias, dataQuality | `indicators.py`, `technical_models.py`, prompt em `llm.py` |
| N3: contexto técnico + cenários com memória de cálculo | `main.py` (stopalvo), `llm.py` |
| Testes novos (26) | `test_scan_deep.py`, `test_pipeline_n2_n3.py`, `test_guardrail_imperativo.py` |
| Estado e decisões (Apple paga → APNs liberado p/ F3) | `ESTADO-Fase0-Fase1-Pipeline-IA.md` |

**Frontend: INALTERADO** (a UI dos níveis entra na Fase 2, após o gate).
**iOS: nenhum passo nesta entrega** — sem plugin novo, sem `cap sync` necessário.

## PASSO ÚNICO — subir e validar o backend
```bash
./subir-git.sh   # ou git add -A && git commit -m "feat: pipeline IA 3 niveis (backend) + espec + proposta UX" && git push
```
Após o deploy (card verde), valide por API (Safari/terminal):
1. `GET /api/scan?period=6mo` → agora cada contexto de análise traz `families` e `dataQuality` (indireto).
2. `GET /api/scan/deep/estimate?period=6mo&topN=3` → `{topN, selecionados, novasChamadasIA, chamadas}`.
3. `POST /api/scan/deep` body `{"period":"6mo","topN":2}` (logado, gerenciada/BYOK) → leituras com `leituraSetups`, `cenarios`, `modelosUtilizados`; repetir a chamada → `cache: true` sem gastar cota.
4. `POST /api/carteira-stopalvo/PETR4` → resposta agora com `cenarios[3]` + `memoriaCalculo` (formato antigo continua aceito).

### ✋ HARD STOP — sua aprovação do PROPOSTA-UX.md
A Fase 2 (telas do flow oportunidade→carteira) e as migrações M1–M6 só
começam depois do seu OK (ou dos ajustes que pedir). A Fase 3 (agente
server-side + push/APNs) vem depois do hard stop de device da Fase 2.

## Validação executada antes do empacote
py_compile ✅ · suítes backend **111/111** ✅ · node --check ✅ · frontend
inalterado · grep de wiring ✅ · guardrail anti-imperativo ✅ (o teste
inclusive pegou e forçou o refinamento do próprio prompt durante o build).
<<<<<<< HEAD
=======

---

## NOVO — Scripts de um comando (raiz do projeto)

A partir desta entrega o fluxo inteiro tem três pontos de entrada:

| Comando | O que faz |
|---|---|
| `bash instalar.sh` | Ambiente local completo (venv+deps backend, npm web) e roda as suítes como prova. `--iphone` executa a cadeia completa do aparelho (build→sync→pod→Xcode); `--tudo` faz ambos. |
| `bash executar.sh` | Sobe DEV (backend :8787 + Vite :5173) com dica do endereço para o iPhone. Aceita `--prod`, `--stop`, `--status` e o novo `--testes` (só suítes). |
| `bash atualizar.sh files.zip "msg"` | **Aplica a entrega do Claude**: exige working tree limpa, extrai o b3-agente.zip, faz overlay aditivo protegendo `.git/ node_modules/ web/ios/ dist/ .venv/ data/ *.db`, valida (py_compile, node --check, suítes se houver venv) e só então deploya via `scripts/atualizar-servidor.sh`, verificando também `/api/scan/deep/estimate`. Flags: `--somente-aplicar` (sem git/deploy) e `--somente-deploy "msg"` (sem zip). |

Eles ORQUESTRAM os scripts existentes em `scripts/` (setup, run, test,
atualizar-servidor, instalar-iphone) — nada foi reescrito. **O fluxo de toda
entrega futura vira:** baixar o files.zip → `bash atualizar.sh ~/Downloads/files.zip "msg"`.
>>>>>>> 3ded4d0 (feat: pipeline IA 3 niveis (backend) + espec + proposta UX)
