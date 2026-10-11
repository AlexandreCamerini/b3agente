// Atualização best-effort do service worker antes de abrir uma página estática
// da mesma origem (/site/app/*) — quick 261011-l5x.
//
// Evidência (2026-10-11): em produção o sw.js já tem navigateFallbackDenylist com
// /^\/site/, mas um navegador com um SW ANTIGO ainda ativo serviu a casca do app
// em /site/app/guia.html. fetch() direto devolvia o HTML certo (só a NAVEGAÇÃO era
// interceptada); registration.update() + navegação nova resolveu. A query ?v= no
// destino não muda a regra do denylist, só fura o cache HTTP.
//
// Contrato: nunca lança e nunca espera mais que `ms` — a abertura da página não
// pode depender do SW. Retorna "sem-sw" | "atualizado" | "timeout" | "erro".
export async function atualizarServiceWorker(
  sw = globalThis.navigator && globalThis.navigator.serviceWorker,
  ms = 1500,
) {
  let timer = null;
  try {
    if (!sw || typeof sw.getRegistration !== "function") return "sem-sw";
    const trabalho = (async () => {
      const reg = await sw.getRegistration();
      if (!reg) return "sem-sw";
      await reg.update();
      if (reg.installing || reg.waiting) {
        await new Promise((resolve) => {
          sw.addEventListener("controllerchange", resolve, { once: true });
        });
      }
      return "atualizado";
    })();
    trabalho.catch(() => {}); // evita rejeição não tratada se o timeout vencer
    const limite = new Promise((resolve) => { timer = setTimeout(() => resolve("timeout"), ms); });
    return await Promise.race([trabalho, limite]);
  } catch {
    return "erro";
  } finally {
    if (timer) clearTimeout(timer);
  }
}
