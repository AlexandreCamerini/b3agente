---
quick_id: 261009-0rv
status: complete
---
# Quick 261009-0rv — Site estático do Boris+

Entregue em `site/`: home, tour do produto (9 passos em snapshots mobile 390x844 + 3 snapshots web 800x500), treinamento interativo (10 módulos, 6 laboratórios, 20 perguntas, progresso em localStorage), suporte e privacidade/termos (estrutura com placeholders).

Desvios do fluxo: PLAN escrito pelo orquestrador e execução inline (sem planner/executor), porque a captura de snapshots depende do browser da sessão principal.

Snapshots: app local (Vite 5174 + API local 8787 já em execução), conta de teste local nova (`@local.test`), saldo virtual R$ 10.000; uma ordem virtual pendente de PETR4 criada nessa conta de teste local (efeito colateral restrito ao banco de dev). Tela de login descartada para não expor e-mail de teste.

Verificação: 0 URLs externas, 0 links/âncoras/recursos quebrados (script), sem overflow horizontal em 390px nas 5 páginas, JS sem erros de console, treinamento percorrido programaticamente (10/10, contas conferidas: R:R 2:1, qtd 50, E=+R$60, equilíbrio 25%).

Pendências: placeholders jurídicos/comerciais; revisão jurídica de privacidade/termos; hospedagem e domínio; recaptura quando a UI mudar; snapshots mostram tickers/sinais reais do dia (rotulados como educacionais, datados).
