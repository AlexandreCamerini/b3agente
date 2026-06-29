# Estado — UI: welcome = login + layout fixo enxuto

## O que mudou (web/src/App.jsx)
- **Tela de abertura = login** (`WelcomeAuthScreen`): na 1ª abertura mostra
  criar conta / entrar, com **"usar sem conta"** discreto no rodapé. Mantém a
  decisão A (local-first): "usar sem conta" leva ao onboarding anônimo
  (orçamento/risco) como antes. Quem cria conta/entra pula direto pro app.
  Componente self-contained e undefined-safe (não acessa campos de `data`).
- **Layout fixo enxuto**:
  - **Ticker removido** (faixa de 38px no topo). O status "ao vivo" virou um
    **ponto** ao lado do nome do app no Topbar.
  - **Topbar compacto numa linha só**: nome do app + ponto ao vivo + (nome do
    usuário) à esquerda; PATR./DIA/CAIXA à direita; padding menor, sem wrap.
  - **Espaçamentos internos** do conteúdo: `24/18/34` → `14/14/26`.

## Observação de gate (device)
Mudança de UI no `App.jsx` — validei aqui o que dá (balance + node --check +
suítes), mas **render só dá pra confirmar no aparelho/navegador**. Por favor
olhe no device:
- [ ] 1ª abertura mostra a tela de login com "usar sem conta".
- [ ] "usar sem conta" abre o onboarding (orçamento/risco) e entra no app.
- [ ] Criar conta / entrar pela tela de abertura entra direto, sem tela branca.
- [ ] Topbar numa linha, ponto ao vivo aparece; sem o ticker; mais área útil.
- [ ] Patrimônio grande não estoura a faixa (se estourar, eu abrevio os números).
