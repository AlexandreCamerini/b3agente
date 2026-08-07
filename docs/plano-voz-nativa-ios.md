# Plano — voz do Boris no app nativo iOS

Origem: Alex reportou que a voz do Boris não toca no app nativo
(TestFlight/App Store), e perguntou se estamos usando o "objeto certo".
Status: **aguardando aprovação**.

## Causa raiz — confirmada no próprio código, não suposta

`web/src/pet/Boris.jsx` (o componente que a F1 portou do PoC original do
Alex) já documenta isso na cabeça do arquivo:

> A FALA é DESACOPLADA da animação (**WKWebView iOS não confia no
> speechSynthesis**):
> - PWA/browser: `boris.speak(texto)` — usa Web Speech API
> - iOS Capacitor: plugue um TTS nativo e dirija a boca: `boris.talk()`;
>   `await TextToSpeech.speak({text, lang:'pt-BR'})`; `boris.stop()`

A F1 portou o componente mas manteve `falarTexto` — a função ANTIGA, escrita
para a coruja emoji, que chama `window.speechSynthesis` direto — e só
amarrou `boris.talk()/.stop()` em volta dela para mexer a boca. Ou seja: no
app nativo, hoje usamos exatamente o objeto que o próprio autor do
componente já tinha documentado como não confiável ali. Isto explica o
sintoma sem precisar de mais nenhuma hipótese.

`@capacitor-community/text-to-speech` (o plugin que o comentário do Boris
pede) **não está instalado** no projeto — confirmado em `web/package.json`.

## O que fazer

1. **Instalar o plugin**: `npm install @capacitor-community/text-to-speech`
   em `web/`.
2. **Novo helper** `web/src/pet/vozBoris.js` (ou dentro de `App.jsx`, perto
   de `falarTexto` — decidir na hora, seguindo o padrão de onde `falarTexto`
   já mora) que expõe UMA função, ex. `falarComBoris(boris, texto, {onEnd})`,
   e por dentro decide a rota:
   - `Capacitor.isNativePlatform()` (mesmo import que `persistence.js`,
     `social.js` e `main.jsx` já usam — `import { Capacitor } from "@capacitor/core"`)
     `true` → `boris.talk()`; `await TextToSpeech.speak({text, lang:"pt-BR"})`;
     `boris.stop()`.
   - `false` (PWA/browser/desktop) → comportamento ATUAL, sem mudança:
     `falarTexto(texto, {onStart, onEnd})` continua dona da voz ali — não
     mexe no que já funciona no navegador.
3. **Trocar os DOIS call sites** que hoje chamam `falarTexto` diretamente
   para passar pelo helper novo: `PetSheet.ouvir()` (App.jsx) e
   `BorisChat.enviarAgora()`. `calarVoz()` também precisa de um equivalente
   nativo (`TextToSpeech.stop()`) para a regra "fechar a folha cala a voz"
   continuar valendo dos dois lados.
4. **`cap sync ios`** (roda no CLONE PRINCIPAL — só ele tem `web/ios`) para
   o plugin nativo entrar no bundle do Xcode. Conferir se o plugin exige
   algo em `Info.plist` (TTS normalmente não pede permissão, ao contrário
   de microfone/STT — mas confirmar lendo o README do plugin instalado em
   `node_modules/@capacitor-community/text-to-speech` antes de assumir).

## O que NÃO muda

- PWA/browser continua exatamente como está (`falarTexto`/`window.speechSynthesis`,
  já funciona lá — não há indício de problema nesse lado).
- STT (microfone, `useSTT` em `BorisChat.jsx`) não é afetado — é caminho
  separado, já opcional/degradado com elegância.

## Testes

`web/tests/test_boris_voz_nativa.mjs` (novo, guardião estático): confirma
que o plugin aparece em `package.json`; confirma que existe a checagem
`Capacitor.isNativePlatform()` na rota de voz; confirma que os DOIS call
sites (`PetSheet`/`BorisChat`) passam pelo helper novo, não mais por
`falarTexto` direto; confirma que existe um caminho de `stop`/`calarVoz`
nativo equivalente.

## O limite honesto desta entrega

**Eu não tenho como testar áudio de verdade no WKWebView** — não tenho
iPhone nem TestFlight. Consigo garantir que o código compila, que o plugin
está instalado, que a lógica de branch (nativo vs. web) está correta e
testada estaticamente, e que `cap sync ios`/build do Xcode não quebram. A
prova de que o SOM sai de verdade no aparelho é sua, depois do rebuild —
mesma pendência que já estava registrada na memória do projeto
("medir a voz no WKWebView real"). Isto não é uma entrega "verificada ao
vivo" como as anteriores desta sessão; é uma entrega que só fecha o loop
com você testando no iPhone.

## Entrega

Como toca `web/ios`, só roda do CLONE PRINCIPAL (mesma razão de sempre —
este worktree não tem `web/ios`). Ao final: `entregar.sh` completo, e você
faz Clean Build Folder + Run no Xcode + confirma no aparelho.
