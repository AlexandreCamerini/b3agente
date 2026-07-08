# QA 26 — Matriz de re-validação (Etapa 1 da FASE 9)
*Pré-condição CONFIRMADA: rodapé do Perfil = build F8B-20260709-3.*
*Marque cada item com OK ou FALHA (+ 1 linha do que viu). As FALHAS viram a Etapa 2.*

## A · Notificações (qa/21, qa/25)
| # | Passo | Esperado |
|---|---|---|
| A1 | Central (Perfil → Conta & preferências → Notificações) → **Pedir permissão** | iOS pergunta; ao conceder, o BolsIA volta a aparecer em Ajustes → Notificações |
| A2 | Ligar o toggle mestre | Liga e mostra "Notificações ativadas" |
| A3 | **Testar notificação** com o app ABERTO | Banner nativo aparece NA HORA (fix do "alert") |
| A4 | **Testar agendada (30s)** e FECHAR o app | Banner do sistema chega em ~30s |
| A5 | **Ativar push neste aparelho** (logado) | "push ativo ✓" sem timeout (callbacks reaplicados) |
| A6 | **Testar push** com app em 2º plano | Banner chega; se falhar, a mensagem diz o reason exato |

## B · Identidade / Modo Operador (qa/23, qa/24, qa/25)
| # | Passo | Esperado |
|---|---|---|
| B1 | Perfil → Modo de trabalho → **Operador** (aceitar termo se 1ª vez; rolagem libera o aceite mesmo se o texto couber) | Aterrissa na HOME com TUDO trocado: fundo grafite, verde #22c55e, chip sólido MODO OPERADOR, "Mesa aberta", abas Mesa/Monitoramento/Posições |
| B2 | Olhar os GRÁFICOS (Acompanhar/sparklines) | Verdes, não azuis |
| B3 | Watchlist → filtros | "Compra / Venda" (não "Estudar alta/baixa") |
| B4 | Radar: card com plano | Decisão colorida + entrada/stop/alvos/R:R + posição sugerida |
| B5 | Fechar e REABRIR o app | Continua no Operador (não volta a estudo) |
| B6 | Sair da conta e entrar de novo | Modo do aparelho preservado |
| B7 | Voltar ao **Estudo** | Tudo restaura (âmbar/azul, professor, Simular compra) |

## C · IA nas duas vozes (qa/22, qa/25)
| # | Passo | Esperado |
|---|---|---|
| C1 | Operador → "Plano da mesa (IA)" num ativo | Voz de mesa: decisão direta, plano coerente com o card, conclusão canônica; chip colorido |
| C2 | Estudo → "Aprofundar com IA" no MESMO ativo | Voz de professor (e repaga a 1ª chamada — cache por modo) |
| C3 | Posições → Stop/alvo (IA) nos DOIS modos | Nota e texto mudam (mesa × professor) |
| C4 | Perfil → Skills | Seletor pelo NOME mostra as duas; badge "EM USO"; editar/salvar/restaurar cada uma |
| C5 | Perfil → Prompts | "Stop/alvo · Modo Estudo" e "· Modo Operador" editáveis separados |

## D · Conta / Login (qa/24, qa/25)
| # | Passo | Esperado |
|---|---|---|
| D1 | Welcome e modal da conta | MESMO formulário (e-mail lembrado nos dois) |
| D2 | Sair | Limpa tudo e REABRE o portão de entrada; reabrir o app não restaura a sessão |
| D3 | Login Apple | Entra; perfil mostra NOME (ou "Conta Apple (e-mail oculto)") + explicação do relay |
| D4 | (Opcional) Refazer consentimento Apple compartilhando o e-mail real → relogar | Perfil passa a mostrar o e-mail verdadeiro |

## E · Plataforma (qa/19–21)
| # | Passo | Esperado |
|---|---|---|
| E1 | Ícone na home + splash | Arte do BolsIA |
| E2 | Focar um campo de texto | SEM zoom automático da tela |
| E3 | Boot sem tocar em nada | Servidor de produção já configurado ("em uso agora: …railway…") |
| E4 | Observabilidade → Logs do servidor | Requests aparecendo com duração |

**Como reportar:** só as FALHAS, ex.: `A5 FALHA — timeout aos 15s` ou
`B2 FALHA — gráfico do Acompanhar continua azul`. O restante assumo OK.
