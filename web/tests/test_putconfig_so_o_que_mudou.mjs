// Guardião (2026-08-17): o `putConfig` do deviceStore manda SÓ o campo que o
// chamador mexeu — nunca o `appMode` de carona.
//
// O BUG QUE ISTO IMPEDE (aconteceu em produção, dois dias seguidos):
// o sync mandava sempre o trio {appMode, operadorTermo, initialBudget}. Editar
// o ORÇAMENTO com o aparelho em Estudo enviava `appMode:"estudo"`; o servidor
// lê isso como SAÍDA do Modo Operador e, em `store.set_config`, reescreve
// `agent.mode` de "executar" para "sinalizar" (migração silenciosa). Voltar
// para Operador NÃO restaura — `test_entrar_no_operador_nao_mexe_no_mode_
// sinalizar` (backend) garante que entrar não migra nada.
//
// Resultado para o usuário: o gatilho do Operador AVISA e a ordem nunca
// executa, com o app mostrando "executar" porque local-first ele está. Nada
// no app acusa — por isso o guardião é estático, sobre a FORMA do payload.
//
// Roda sem build: `node web/tests/test_putconfig_so_o_que_mudou.mjs`.
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const here = dirname(fileURLToPath(import.meta.url));
const persistence = readFileSync(join(here, "..", "src", "persistence.js"), "utf8");
const storePy = readFileSync(join(here, "..", "..", "server", "app", "store.py"), "utf8");

let fails = 0;
const ok = (name, cond) => { console.log((cond ? "ok " : "FALHOU ") + name); if (!cond) fails++; };

// A razão do guardião ainda existe? Se o servidor parar de rebaixar o agente
// ao sair do Operador, esta regra pode ser relaxada CONSCIENTEMENTE — mas aí
// é para atualizar este arquivo com nota, não para apagá-lo.
ok("servidor ainda rebaixa agent.mode ao sair do Operador (a razão desta regra)",
   /if cfg\["appMode"\] != "operador":/.test(storePy) && /ag\["mode"\] = "sinalizar"/.test(storePy));

// O payload é montado condicionalmente, campo a campo.
ok("monta o payload só com o que veio no patch",
   /const enviar = \{\};/.test(persistence)
   && /if \(patch\.appMode === "estudo" \|\| patch\.appMode === "operador"\) enviar\.appMode = c\.appMode;/.test(persistence)
   && /if \("operadorTermo" in patch\) enviar\.operadorTermo = c\.operadorTermo;/.test(persistence)
   && /if \(typeof patch\.initialBudget === "number"\) enviar\.initialBudget = c\.initialBudget;/.test(persistence));

// NOTA (quick task 260824-kc2, 2026-08-24) — `notif` ENTROU no payload, e a
// regra do "sem carona" não foi relaxada: foi ESTENDIDA para dentro do campo.
//
// Por que entrou: as três classes do push do servidor (radar/execucao/protecao)
// passaram a ser controle da CONTA, e o web monta o corpo do `syncPushPrefs` a
// partir do `config.notif` DO SERVIDOR. Sem o `notif` subindo, esse config
// ficaria eternamente no default e o web reenviaria as três LIGADAS por cima do
// que o aparelho desligou.
//
// Por que CHAVE A CHAVE: `c.notif` é o objeto MERGED do aparelho, e o
// deviceStore nunca lê `config` do servidor. Mandar o objeto inteiro faria
// desligar `radar` no web e, depois, tocar em QUALQUER controle no iPhone
// reverter a escolha do web — em silêncio, e valendo também para os cinco
// controles locais. É exatamente o defeito do `appMode` de carona, uma camada
// abaixo.
ok("`notif` sobe condicionado ao patch, CHAVE A CHAVE",
   /if \(patch\.notif && typeof patch\.notif === "object"\) \{/.test(persistence)
   && /const nEnviar = \{\};/.test(persistence)
   && /for \(const k of Object\.keys\(patch\.notif\)\) if \(k in c\.notif\) nEnviar\[k\] = c\.notif\[k\];/.test(persistence)
   && /if \(Object\.keys\(nEnviar\)\.length\) enviar\.notif = nEnviar;/.test(persistence));
ok("NÃO manda o objeto `notif` inteiro de carona",
   !/enviar\.notif = c\.notif/.test(persistence));

// O defeito exato: enviar appMode junto de tudo, incondicionalmente.
ok("NÃO manda o trio fixo {appMode, operadorTermo, initialBudget}",
   !/putConfig\(\{\s*appMode: c\.appMode,\s*operadorTermo: c\.operadorTermo,/.test(persistence));

// Nada de chamada sem payload montado.
ok("só chama putConfig com o objeto `enviar`",
   /await api\.putConfig\(enviar\);/.test(persistence)
   && (persistence.match(/api\.putConfig\(/g) || []).length === 1);

// Não manda requisição vazia quando o patch não tocou nenhum dos três.
ok("não chama o servidor quando nada relevante mudou",
   /if \(Object\.keys\(enviar\)\.length\) await api\.putConfig\(enviar\);/.test(persistence));

// Ligar "operador" exige o termo no mesmo patch quando o servidor ainda não o
// tem (store.set_config: sem termo, o modo NÃO muda, silenciosamente).
ok("appMode=operador nunca vai sem operadorTermo",
   /if \(enviar\.appMode === "operador" && !enviar\.operadorTermo && c\.operadorTermo\)/.test(persistence));

console.log(fails === 0 ? "\nTUDO OK" : `\n${fails} FALHA(S)`);
process.exit(fails === 0 ? 0 : 1);
