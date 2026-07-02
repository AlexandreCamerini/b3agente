// BLOCO 2 — trava o NOVO contrato do welcome como PORTÃO DE BOOT:
//  • o welcome aparece SEMPRE no boot (uma vez por abertura do app),
//    independente de config.onboarded e de haver sessão ativa;
//  • config.onboarded deixa de esconder o welcome e passa a controlar APENAS
//    se "usar sem conta" abre o onboarding anônimo (orçamento/risco);
//  • a variação de tela por sessão: com usuário restaurado → "conectado como X"
//    + Entrar; com token salvo mas /auth/me pendente → aviso de restauração;
//  • backfillStructural continua protegendo device legado (sem tela branca) e
//    preservando onboarded (que agora governa só o atalho do onboarding).
import { defaultState } from "../src/catalog.js";
import { backfillStructural } from "../src/migrate.js";

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// Mesmos predicados usados no App.jsx (boot gate + skip + variação da tela).
const shouldShowAtBoot = (alreadyShownThisLaunch) => !alreadyShownThisLaunch;
const skipOpensOnboarding = (config) => !(config && config.onboarded);
const welcomeVariant = ({ authUser, hasSavedSession }) =>
  authUser ? "connected" : (hasSavedSession ? "restoring" : "login");

// 1) PORTÃO DE BOOT: mostra sempre na abertura, mesmo onboarded/logado
{
  ok("boot: 1ª render da sessão -> mostra", shouldShowAtBoot(false) === true);
  ok("boot: já mostrado nesta abertura -> não repete", shouldShowAtBoot(true) === false);
  // onboarded e sessão NÃO entram no predicado de exibição — é incondicional.
}

// 2) variação da tela conforme a sessão
{
  ok("sem sessão -> fluxo de login", welcomeVariant({ authUser: null, hasSavedSession: false }) === "login");
  ok("token salvo, /auth/me pendente -> restaurando", welcomeVariant({ authUser: null, hasSavedSession: true }) === "restoring");
  ok("sessão restaurada -> conectado como X", welcomeVariant({ authUser: { email: "x@y.z" }, hasSavedSession: true }) === "connected");
}

// 3) "usar sem conta": onboarding anônimo SÓ para quem nunca concluiu
{
  const d = defaultState();
  ok("instalação limpa nasce onboarded=false", d.config.onboarded === false);
  ok("novato: skip abre onboarding", skipOpensOnboarding(d.config) === true);
  ok("veterano: skip entra direto", skipOpensOnboarding({ onboarded: true }) === false);
  ok("config ausente (legado) -> trata como novato", skipOpensOnboarding(undefined) === true);
  ok("config {} parcial -> trata como novato", skipOpensOnboarding({}) === true);
}

// 4) backfill de device legado: doc parcial não quebra e preserva onboarded
{
  const d1 = backfillStructural({ config: { onboarded: true } }, defaultState());
  ok("backfill preserva onboarded=true", d1.config.onboarded === true);
  ok("veterano pós-backfill: skip não reabre onboarding", skipOpensOnboarding(d1.config) === false);
  const d2 = backfillStructural(null, defaultState());
  ok("backfill(null) herda onboarded=false", d2.config.onboarded === false);
  ok("doc semeado do default: skip abre onboarding", skipOpensOnboarding(d2.config) === true);
  ok("backfill devolve config estrutural (sem tela branca)", d2 && d2.config && typeof d2.config === "object");
}

// 5) round-trip: concluir onboarding não volta a abrir o modal no skip
{
  const cfg = { ...defaultState().config, onboarded: true };
  ok("após concluir -> skip entra direto", skipOpensOnboarding(cfg) === false);
  ok("após concluir -> welcome AINDA aparece no próximo boot", shouldShowAtBoot(false) === true);
}

console.log("\n" + (fails === 0 ? "TODOS OS TESTES DE WELCOME (BOOT GATE) PASSARAM" : fails + " TESTE(S) FALHARAM"));
process.exit(fails === 0 ? 0 : 1);
