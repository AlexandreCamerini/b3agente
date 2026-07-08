# QA 22 — FASE 8B: P1–P4 (relay Apple · termo · ícone · cérebro por modo)
*08/07/2026 · baseline verde antes de mexer (18 backend + 19 web)*

## P1 — E-mail @privaterelay da Apple
- **Não é bug:** é o recurso "Ocultar e-mail" da Apple — o relay É o e-mail da
  conta (nossas mensagens chegam no real por ele) e não dá para trocá-lo por
  API. **Correção de produto:** toda a UI passa a preferir o NOME; sem nome,
  mostra "Conta Apple (e-mail oculto)" em vez do relay; o modal da conta
  explica o relay e ensina o caminho para compartilhar o e-mail verdadeiro
  (Ajustes → ID Apple → Início de Sessão e Segurança → BolsIA → parar de usar
  → entrar de novo com "Compartilhar meu e-mail"). Aplicado no AuthModal, no
  PerfilHub e no Welcome.

## P2 — Termo do Modo Operador travado
- **Causa-raiz:** o aceite exigia rolar até o fim, mas quando o texto CABE no
  contêiner (tela grande/fonte pequena) o `onScroll` nunca dispara — checkbox
  bloqueado para sempre. **Correção:** ao montar (e no resize, com re-check em
  250ms para o reflow do WebView), se não há overflow o termo já conta como
  lido; e apareceu a dica "role o texto até o fim" enquanto bloqueado.

## P3 — Ícone do app errado
- **Causa-raiz:** o `AppIcon.appiconset` do projeto iOS ainda continha o ícone
  padrão do template Capacitor (hash ≠ `resources/icon-1024.png`) — o
  `gen-assets.sh` nunca chegou a valer (recriar `ios/` descarta assets).
- **Correção:** arte do BolsIA aplicada no AppIcon (1024×1024, RGB SEM alpha —
  exigência da App Store, achatada sobre o fundo da marca), splash 2732
  reflatten e ícones web/PWA (180/192/512) regenerados da mesma fonte.
- **Guardião novo:** `test_ios_assets.mjs` (parser PNG puro: dimensões, alpha,
  integridade — 8 asserções).

## P4 (B3) — Cérebro por modo + revisão dos defaults
- **Servidor (`llm.py`):** persona `OPERADOR_PRO` (mesma metodologia 1–9 do
  educacional; item 10 vira vocabulário de DECISÃO obrigatoriamente COERENTE
  com o plano determinístico; item 11 tranca os limites regulatórios),
  `GUARDRAILS_PRO` (mesa: risco primeiro, sem aula, fecho com UMA das 4
  conclusões canônicas da persona), `FORMAT_PRO` e `PRO_DEEP_FORMAT` — MESMAS
  chaves JSON dos formatos educacionais (zero mudança de contrato/parse/UI);
  muda vocabulário, tom e semântica.
- **Roteamento por modo:** N1 (`analyze_deep`) e N2 (`analyze_structured`)
  escolhem persona/formato pelo `appMode` (iOS manda no corpo/query,
  local-first; web usa a config do escopo; capturado ANTES do managed recriar
  a config). Validação pós-parse por modo: rótulo fora do conjunto vira o
  neutro DO MODO — vocabulário de um nunca vaza no outro.
- **Plano determinístico no pacote do deep:** `planoOperacional` entra no
  payload de setups — a mesa é obrigada a ser coerente com ele (regra 10).
- **Cache por modo:** a chave do cache do deep ganhou o modo (mesa × professor
  são textos diferentes do MESMO snapshot); `estimate` idem, com `?appMode`.
- **Revisão de eficiência dos defaults:** instrução de concisão no FORMAT
  educacional (corpo ≤ 12 linhas) e nos formatos PRO (corpo ≤ 10 linhas,
  abrindo com resumo executivo) — leitura de celular nos dois comportamentos.
- **Guardrail regulatório estendido:** `test_guardrail_imperativo.py` agora
  varre TAMBÉM as fontes PRO (imperativos de pressão seguem proibidos na
  mesa; 'COMPRAR'/'VENDER' são rótulos de decisão, não ordens "compre agora").
- **Testes novos:** +5 em `test_llm_errors.py` (is_operador, contrato
  FORMAT_PRO/PRO_DEEP_FORMAT, conclusões canônicas, limites regulatórios),
  +1 em `test_scan_deep.py` (cache não vaza entre modos) — que também ganhou
  o mini-runner `__main__` que não tinha.

## Evidência
- Backend: **19 suítes offline verdes** (scan_deep entrou no portão) · llm/
  guardrail validados via stub (14 testes) — rodam completos no pytest do venv.
- Web: **20/20 suítes** (novo: test_ios_assets) · JSX OK.
- Pendente no aparelho: ícone/splash aparecem após reinstalar pelo Xcode;
  termo desbloqueado; leitura do Aprofundar no modo operador com voz de mesa.

## O que falta da Parte B (próximas rodadas)
B1 (migração das telas para copy.js) + B2 (tema por modo) — aguardam suas
respostas às 5 decisões do mock `qa/mocks/dois-apps-em-um.html`; B4
(tratamento/notificações por modo); N3 stop/alvo PRO entra com B4.
