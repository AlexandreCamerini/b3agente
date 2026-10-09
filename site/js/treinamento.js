/* Boris+ — treinamento interativo. Vanilla JS, sem dependências, sem rede.
   Todos os números são fictícios e didáticos. Progresso em localStorage (opcional). */
(function () {
  "use strict";
  document.documentElement.classList.add("js");

  var KEY = "boris-treino-v1";
  var mem = { done: {}, q: {} };
  function load() {
    try { var r = localStorage.getItem(KEY); if (r) { var o = JSON.parse(r); if (o && typeof o === "object") mem = { done: o.done || {}, q: o.q || {} }; } }
    catch (e) { var n = document.getElementById("saveNote"); if (n) n.textContent = "Seu navegador bloqueou o armazenamento: o progresso vale só nesta visita."; }
  }
  function save() { try { localStorage.setItem(KEY, JSON.stringify(mem)); } catch (e) {} }

  var $ = function (id) { return document.getElementById(id); };
  var fmt = function (n, d) { d = d == null ? 2 : d; return n.toLocaleString("pt-BR", { minimumFractionDigits: d, maximumFractionDigits: d }); };
  var brl = function (n) { return "R$ " + fmt(n); };
  var pct = function (n, d) { return fmt(n, d == null ? 1 : d) + "%"; };

  function rng(seed) { // mulberry32
    var a = seed >>> 0;
    return function () { a |= 0; a = (a + 0x6D2B79F5) | 0; var t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  }
  function normal(r) { var u = 0, v = 0; while (!u) u = r(); while (!v) v = r(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); }
  function svg(tag, attrs, txt) {
    var e = document.createElementNS("http://www.w3.org/2000/svg", tag);
    for (var k in attrs) e.setAttribute(k, attrs[k]);
    if (txt != null) e.textContent = txt;
    return e;
  }
  function clear(el) { while (el.firstChild) el.removeChild(el.firstChild); }
  function html(el, s) { el.innerHTML = s; } // somente strings montadas aqui, nunca entrada do usuário
  function num(id, fb) { var v = parseFloat(String($(id).value).replace(",", ".")); return isFinite(v) ? v : fb; }

  /* ---------------- quizzes ---------------- */
  var QUIZ = {
    m1: [
      { q: "O que acontece quando você confirma uma compra no Boris+?", o: ["A ordem é enviada à corretora.", "A ordem é simulada com dinheiro virtual; nada é enviado a corretora.", "O Bóris compra por você."], a: 1, why: "Todo o saldo é fictício e a execução é simulada. Nenhuma ordem chega a corretora, bolsa ou conta bancária." },
      { q: "Quem calcula saldo, preço médio, lucro e prejuízo?", o: ["A IA (Bóris).", "A corretora.", "Regras determinísticas do app."], a: 2, why: "Números financeiros nunca vêm da IA. A IA só explica o que o motor já calculou." }
    ],
    m2: [
      { q: "A fonte de cotações ficou indisponível. O comportamento correto é:", o: ["Estimar o valor pela última tendência.", "Mostrar o estado de erro e bloquear operações que dependem do dado.", "Esconder o aviso para não assustar o usuário."], a: 1, why: "Nunca se inventa valor. O estado real é mostrado e a operação dependente de dado inválido é impedida." },
      { q: "Um dado rotulado como “atrasado” é:", o: ["Um valor errado.", "Um valor real, de alguns minutos atrás.", "Um valor inventado pelo sistema."], a: 1, why: "Atrasado não é errado: é real, mas defasado. Por isso o horário e o rótulo ficam sempre visíveis." }
    ],
    m3: [
      { q: "Aumentar a janela de uma média móvel a torna:", o: ["Mais rápida e mais ruidosa.", "Mais lenta e mais suave.", "Igual; a janela não importa."], a: 1, why: "Janela maior dilui mais candles: a média reage devagar e filtra ruído, ao custo de atraso." },
      { q: "Preço acima de uma média móvel em alta indica:", o: ["Que o preço vai subir amanhã.", "Um regime de alta nessa janela: leitura de contexto, não garantia.", "Que é hora de comprar."], a: 1, why: "Indicadores descrevem o que já aconteceu. Contexto não é previsão nem recomendação." }
    ],
    m4: [
      { q: "Um rompimento acima da resistência é:", o: ["Prova de que o preço vai continuar subindo.", "Um sinal de venda.", "Uma hipótese que precisa de confirmação e de um ponto de invalidação."], a: 2, why: "Rompimentos falham com frequência. O plano diz onde a ideia deixa de valer." },
      { q: "Suporte é:", o: ["O preço mínimo histórico absoluto.", "Uma região onde o preço costuma encontrar demanda.", "O stop de quem está comprado."], a: 1, why: "É uma região, não uma linha exata, e não é garantia de que o preço vai segurar." }
    ],
    m5: [
      { q: "Maior volatilidade significa:", o: ["Mais retorno garantido.", "Oscilações maiores para os dois lados, logo mais risco por posição.", "Tendência de alta."], a: 1, why: "Volatilidade mede amplitude, não direção." },
      { q: "Com oscilação diária típica de 3%, uma posição de R$ 10.000 oscila tipicamente cerca de:", o: ["R$ 30", "R$ 3.000", "R$ 300"], a: 2, why: "3% de R$ 10.000 = R$ 300 por dia, para cima ou para baixo, em um dia típico." }
    ],
    m6: [
      { q: "Entrada 40, stop 38, alvo 46. Qual a relação risco-retorno (R:R)?", o: ["1,5 : 1", "3 : 1", "6 : 1"], a: 1, why: "Risco = 40 − 38 = 2. Ganho potencial = 46 − 40 = 6. R:R = 6 ÷ 2 = 3 : 1." },
      { q: "O tamanho da posição deve partir principalmente de:", o: ["Quanto eu quero ganhar.", "Quanto aceito perder se o stop for atingido.", "O preço do papel."], a: 1, why: "Primeiro o risco aceito, depois a quantidade: quantidade = risco em R$ ÷ (entrada − stop)." }
    ],
    m7: [
      { q: "Acerto de 70%, ganho médio R$ 50, perda média R$ 200. A expectativa por operação é:", o: ["Positiva: + R$ 25", "Negativa: − R$ 25", "Zero"], a: 1, why: "0,7 × 50 − 0,3 × 200 = 35 − 60 = − R$ 25. Acertar muito não compensa perdas grandes." },
      { q: "Acertar menos da metade das operações impede de lucrar?", o: ["Sim, sempre.", "Não: depende do tamanho médio dos ganhos e das perdas.", "Só em mercado de alta."], a: 1, why: "Com ganho médio 3× a perda média, até 30% de acerto já fecha positivo." }
    ],
    m8: [
      { q: "Uma carteira perdeu 50%. Para voltar ao valor inicial precisa ganhar:", o: ["50%", "100%", "150%"], a: 1, why: "50 ÷ (100 − 50) = 100%. Metade do capital precisa dobrar para recompor." },
      { q: "Por que limitar o drawdown importa tanto?", o: ["Porque perdas e ganhos são simétricos.", "Porque quanto maior a queda, desproporcionalmente maior o ganho para recuperar.", "Não importa se a taxa de acerto for alta."], a: 1, why: "A recuperação cresce mais rápido que a perda. Por isso o risco por operação é limitado." }
    ],
    m9: [
      { q: "Diversificar ajuda a reduzir:", o: ["Todo tipo de risco.", "O risco específico de cada papel, não o risco de mercado.", "O custo de corretagem."], a: 1, why: "Se o mercado inteiro cai, uma carteira diversificada também cai." },
      { q: "Uma oferta promete retorno alto e sem risco. O raciocínio certo é:", o: ["Aproveitar logo.", "Desconfiar: risco e retorno andam juntos.", "Investir só um pouco."], a: 1, why: "Promessa de ganho sem risco é sinal de alerta. O Boris+ nunca faz esse tipo de promessa." }
    ],
    m10: [
      { q: "Qual a ordem correta de uma decisão simulada?", o: ["Enviar a ordem → montar o plano → ler o dado.", "Ler o dado → contexto → plano e tamanho → ordem virtual → revisão.", "Enviar a ordem → revisar → montar o plano."], a: 1, why: "O plano vem antes da ordem. A revisão fecha o ciclo e alimenta a próxima decisão." },
      { q: "No Modo Estudo, quem decide a operação?", o: ["O Bóris.", "Você.", "A corretora."], a: 1, why: "No Estudo a IA orienta e você decide. Automações ficam para o Modo Operador, também com execução simulada." }
    ]
  };

  var mods = Array.prototype.slice.call(document.querySelectorAll(".mod"));
  var ids = mods.map(function (m) { return m.id; });

  function renderQuiz(box) {
    var id = box.getAttribute("data-quiz"), qs = QUIZ[id] || [];
    mem.q[id] = mem.q[id] || {};
    html(box, "<h3>Verifique o que aprendeu</h3>");
    qs.forEach(function (it, i) {
      var fs = document.createElement("fieldset"); fs.className = "q";
      var lg = document.createElement("legend"); lg.textContent = (i + 1) + ". " + it.q; fs.appendChild(lg);
      it.o.forEach(function (txt, j) {
        var lb = document.createElement("label"), inp = document.createElement("input");
        inp.type = "radio"; inp.name = id + "-" + i; inp.value = j;
        lb.appendChild(inp); lb.appendChild(document.createTextNode(" " + txt)); fs.appendChild(lb);
        inp.addEventListener("change", function () { answer(id, i, j, fs); });
      });
      var why = document.createElement("p"); why.className = "why"; why.hidden = true; why.setAttribute("role", "status"); fs.appendChild(why);
      box.appendChild(fs);
      if (mem.q[id][i]) { // já respondida corretamente
        var radios = fs.querySelectorAll("input"); radios[it.a].checked = true; mark(fs, it, it.a); why.hidden = false; why.className = "why ok"; why.textContent = "Correto. " + it.why;
      }
    });
    var sc = document.createElement("p"); sc.className = "score"; sc.setAttribute("aria-live", "polite"); box.appendChild(sc);
    var nav = document.createElement("div"); nav.className = "modnav";
    var idx = ids.indexOf(id);
    var prev = document.createElement("button"); prev.type = "button"; prev.className = "btn ghost small"; prev.textContent = "← Anterior"; prev.disabled = idx === 0; prev.addEventListener("click", function () { go(ids[idx - 1], true); });
    var next = document.createElement("button"); next.type = "button"; next.className = "btn small"; next.textContent = idx === ids.length - 1 ? "Concluir" : "Próximo módulo →"; next.addEventListener("click", function () { if (idx === ids.length - 1) { $("finish").scrollIntoView({ behavior: "smooth", block: "start" }); } else go(ids[idx + 1], true); });
    nav.appendChild(prev); nav.appendChild(next); box.appendChild(nav);
    updateScore(id);
  }
  function mark(fs, it, chosen) {
    var labels = fs.querySelectorAll("label");
    Array.prototype.forEach.call(labels, function (l, k) { l.classList.remove("ok", "bad"); if (k === chosen) l.classList.add(chosen === it.a ? "ok" : "bad"); });
  }
  function answer(id, i, j, fs) {
    var it = QUIZ[id][i], why = fs.querySelector(".why"), right = j === it.a;
    mark(fs, it, j); why.hidden = false;
    why.className = "why " + (right ? "ok" : "bad");
    why.textContent = (right ? "Correto. " : "Ainda não. ") + (right ? it.why : "Releia o módulo e tente outra opção.");
    if (right) { mem.q[id][i] = true; }
    var all = QUIZ[id].every(function (_, k) { return mem.q[id][k]; });
    if (all && !mem.done[id]) { mem.done[id] = true; }
    save(); updateScore(id); refreshProgress();
  }
  function updateScore(id) {
    var box = document.querySelector('[data-quiz="' + id + '"]'); if (!box) return;
    var n = QUIZ[id].filter(function (_, k) { return mem.q[id][k]; }).length;
    box.querySelector(".score").textContent = n === QUIZ[id].length ? "Módulo concluído ✓" : "Acertos: " + n + " de " + QUIZ[id].length;
  }

  /* ---------------- navegação e progresso ---------------- */
  var toc = $("toc"), current = null;
  function buildToc() {
    clear(toc);
    mods.forEach(function (m, i) {
      var li = document.createElement("li"), b = document.createElement("button");
      b.type = "button"; b.setAttribute("data-id", m.id);
      var dot = document.createElement("span"); dot.className = "dot"; dot.setAttribute("aria-hidden", "true"); dot.textContent = i + 1;
      var t = document.createElement("span"); t.textContent = m.getAttribute("data-title");
      var st = document.createElement("span"); st.className = "sr"; st.style.cssText = "position:absolute;left:-999px";
      b.appendChild(dot); b.appendChild(t); b.appendChild(st);
      b.addEventListener("click", function () { go(m.id, true); });
      li.appendChild(b); toc.appendChild(li);
    });
  }
  function refreshProgress() {
    var n = ids.filter(function (id) { return mem.done[id]; }).length;
    $("progTxt").textContent = n + " de " + ids.length + " módulos";
    $("barFill").style.width = (n / ids.length * 100) + "%";
    $("bar").setAttribute("aria-valuenow", String(Math.round(n / ids.length * 100)));
    Array.prototype.forEach.call(toc.querySelectorAll("button"), function (b) {
      var id = b.getAttribute("data-id"), done = !!mem.done[id];
      b.classList.toggle("done", done);
      b.querySelector(".dot").textContent = done ? "✓" : String(ids.indexOf(id) + 1);
      b.querySelector(".sr").textContent = done ? " (concluído)" : "";
      if (id === current) b.setAttribute("aria-current", "step"); else b.removeAttribute("aria-current");
    });
    $("finish").hidden = n !== ids.length;
  }
  function go(id, focus) {
    if (ids.indexOf(id) < 0) id = ids[0];
    current = id;
    mods.forEach(function (m) { m.classList.toggle("on", m.id === id); });
    if (location.hash !== "#" + id) { try { history.replaceState(null, "", "#" + id); } catch (e) {} }
    refreshProgress();
    if (focus) { var h = $(id).querySelector("h2"); h.setAttribute("tabindex", "-1"); h.focus({ preventScroll: true }); $("treino").scrollIntoView({ behavior: "smooth", block: "start" }); }
    labs[id] && labs[id]();
  }

  /* ---------------- laboratórios ---------------- */
  var labs = {};

  // M2 — estado do dado
  var ESTADOS = {
    rt: ["Tempo real", "Fonte e horário visíveis. Análises e simulação de ordens seguem normalmente, sempre com o carimbo do dado.", "ok"],
    atraso: ["Atrasado", "O dado é real, mas defasado. O app mostra o aviso de atraso e a hora do dado, e as análises informam que usam dado atrasado.", "warn"],
    hist: ["Histórico", "Serve para estudo do passado. É rotulado como histórico, e qualquer análise diz que se baseia em dados históricos.", "warn"],
    falha: ["Fonte indisponível", "Nenhum valor é exibido: nada é estimado nem inventado. O app mostra o estado de erro, diz “Não há dados suficientes para concluir.” e impede operações que dependem desse dado.", "bad"]
  };
  function setEstado(v) {
    var e = ESTADOS[v], c = e[2] === "ok" ? "pos" : e[2] === "bad" ? "neg" : "warn";
    html($("estadoOut"), '<strong class="' + c + '">' + e[0] + "</strong><br>" + e[1]);
    Array.prototype.forEach.call(document.querySelectorAll('[data-lab="estado"] .seg button'), function (b) { b.setAttribute("aria-pressed", String(b.getAttribute("data-v") === v)); });
  }
  Array.prototype.forEach.call(document.querySelectorAll('[data-lab="estado"] .seg button'), function (b) { b.addEventListener("click", function () { setEstado(b.getAttribute("data-v")); }); });
  setEstado("rt");

  // M3 — tendência
  var trend = (function () { var r = rng(11), p = 50, a = []; for (var i = 0; i < 120; i++) { p *= 1 + 0.0012 + normal(r) * 0.012; a.push(p); } return a; })();
  function drawTrend() {
    var w = parseInt($("smaWin").value, 10); $("smaOut").textContent = w;
    var s = $("trendSvg"); clear(s);
    var sma = trend.map(function (_, i) { if (i < w - 1) return null; var t = 0; for (var k = i - w + 1; k <= i; k++) t += trend[k]; return t / w; });
    var vals = trend.concat(sma.filter(Boolean)), lo = Math.min.apply(null, vals), hi = Math.max.apply(null, vals), pad = (hi - lo) * 0.08; lo -= pad; hi += pad;
    var X = function (i) { return 40 + i * (590 / (trend.length - 1)); }, Y = function (v) { return 200 - (v - lo) / (hi - lo) * 180; };
    for (var g = 0; g < 4; g++) { var gy = 20 + g * 60; s.appendChild(svg("line", { x1: 40, x2: 630, y1: gy, y2: gy, stroke: "#2c3245", "stroke-width": 1 })); s.appendChild(svg("text", { x: 4, y: gy + 4 }, fmt(hi - (hi - lo) * (gy - 20) / 180, 0))); }
    s.appendChild(svg("polyline", { points: trend.map(function (v, i) { return X(i) + "," + Y(v); }).join(" "), fill: "none", stroke: "#c9d1e6", "stroke-width": 1.8 }));
    var pts = []; sma.forEach(function (v, i) { if (v != null) pts.push(X(i) + "," + Y(v)); });
    s.appendChild(svg("polyline", { points: pts.join(" "), fill: "none", stroke: "#f2a93b", "stroke-width": 2.6 }));
    s.appendChild(svg("text", { x: 46, y: 14 }, "Preço fictício (cinza) e média móvel (âmbar)"));
    var last = trend[trend.length - 1], m1 = sma[sma.length - 1], m0 = sma[sma.length - 6];
    var acima = last > m1, sobe = m1 > m0;
    var txt = "Último preço " + (acima ? "acima" : "abaixo") + " da média, e a média " + (sobe ? "subindo" : "caindo") + " nos últimos 5 candles. ";
    txt += acima && sobe ? "Leitura de contexto: regime de alta nesta janela." : !acima && !sobe ? "Leitura de contexto: regime de baixa nesta janela." : "Sinais mistos: sem tendência clara nesta janela.";
    txt += w <= 10 ? " Janela curta: reage rápido, mas gera mais falsos sinais." : w >= 30 ? " Janela longa: filtra ruído, mas reage com atraso." : "";
    $("smaDesc").textContent = txt;
  }
  $("smaWin").addEventListener("input", drawTrend);
  labs.m3 = drawTrend;

  // M4 — faixa
  function drawFaixa() {
    var px = parseFloat($("faixaPx").value); $("faixaOut").textContent = fmt(px);
    var s = $("faixaSvg"); clear(s);
    var X = function (v) { return 30 + (v - 44) / 18 * 580; };
    s.appendChild(svg("rect", { x: X(50), y: 30, width: X(56) - X(50), height: 60, fill: "rgba(79,140,255,.14)", stroke: "none" }));
    s.appendChild(svg("line", { x1: X(50), x2: X(50), y1: 24, y2: 96, stroke: "#34d399", "stroke-width": 2.5 }));
    s.appendChild(svg("line", { x1: X(56), x2: X(56), y1: 24, y2: 96, stroke: "#f26d6d", "stroke-width": 2.5 }));
    s.appendChild(svg("text", { x: X(50) - 4, y: 114, "text-anchor": "end" }, "suporte 50,00"));
    s.appendChild(svg("text", { x: X(56) + 4, y: 114 }, "resistência 56,00"));
    s.appendChild(svg("circle", { cx: X(px), cy: 60, r: 9, fill: "#f2a93b", stroke: "#10121a", "stroke-width": 3 }));
    var t;
    if (px > 56) t = "Preço acima da resistência: rompimento para cima. É uma hipótese; o plano precisa dizer onde ela se invalida (por exemplo, o retorno para dentro da faixa).";
    else if (px < 50) t = "Preço abaixo do suporte: rompimento para baixo. Quem estava comprado já deveria ter definido a saída.";
    else if (px >= 55 || px <= 51) t = "Testando " + (px >= 55 ? "a resistência" : "o suporte") + ": região onde costuma haver reação, sem garantia de que o nível segure.";
    else t = "Dentro da faixa: sem rompimento. Aqui, o contexto pesa mais do que qualquer nível isolado.";
    $("faixaDesc").textContent = t;
  }
  $("faixaPx").addEventListener("input", drawFaixa);
  labs.m4 = drawFaixa;

  // M5 — volatilidade
  var zs = (function () { var r = rng(5), a = []; for (var i = 0; i < 30; i++) a.push(normal(r)); return a; })();
  function drawVol() {
    var sg = parseFloat($("volPct").value); $("volOut").textContent = fmt(sg, 1);
    var s = $("volSvg"); clear(s);
    var scale = 70 / 12; // ±12% cabe na tela
    s.appendChild(svg("line", { x1: 30, x2: 630, y1: 80, y2: 80, stroke: "#2c3245" }));
    s.appendChild(svg("text", { x: 2, y: 84 }, "0%"));
    var mx = 0;
    zs.forEach(function (z, i) { var v = Math.max(-12, Math.min(12, z * sg)); mx = Math.max(mx, Math.abs(z * sg)); var h = Math.abs(v) * scale; s.appendChild(svg("rect", { x: 36 + i * 19.6, y: v >= 0 ? 80 - h : 80, width: 13, height: Math.max(h, 1), rx: 2, fill: v >= 0 ? "#34d399" : "#f26d6d" })); });
    html($("volDesc"), "Em um dia típico, uma posição de <strong>R$ 10.000</strong> oscila cerca de <strong>±" + brl(10000 * sg / 100) + "</strong>. Nestes 30 dias fictícios, o maior movimento foi de <strong>" + pct(mx, 1) + "</strong>.");
  }
  $("volPct").addEventListener("input", drawVol);
  labs.m5 = drawVol;

  // M6 — plano
  function drawPlano() {
    var cap = num("pCap", 0), rk = num("pRisk", 0), e = num("pEnt", 0), st = num("pStop", 0), al = num("pAlvo", 0), o = $("planoOut");
    if (!(cap > 0 && rk > 0 && e > 0 && st > 0 && al > 0)) { o.textContent = "Preencha valores positivos em todos os campos."; return; }
    if (st >= e) { html(o, '<span class="neg">Numa compra, o stop precisa ficar abaixo da entrada.</span> Sem isso não há risco definido.'); return; }
    if (al <= e) { html(o, '<span class="neg">Numa compra, o alvo precisa ficar acima da entrada.</span>'); return; }
    var rpu = e - st, rr = (al - e) / rpu, risk$ = cap * rk / 100, qty = Math.floor(risk$ / rpu), custo = qty * e;
    var s = '<span class="k">Risco por unidade: <strong>' + brl(rpu) + "</strong></span>" +
      '<span class="k">R:R: <strong>' + fmt(rr, 2) + " : 1</strong></span>" +
      '<span class="k">Risco aceito: <strong>' + brl(risk$) + "</strong></span><br>" +
      '<span class="k">Quantidade: <strong>' + fmt(qty, 0) + "</strong></span>" +
      '<span class="k">Custo da posição: <strong>' + brl(custo) + "</strong></span>" +
      '<span class="k">Perda no stop: <strong class="neg">' + brl(qty * rpu) + '</strong></span>' +
      '<span class="k">Ganho no alvo: <strong class="pos">' + brl(qty * (al - e)) + "</strong></span>";
    if (qty < 1) s += '<br><span class="warn">O risco aceito não comporta nem 1 unidade com este stop. Reduza a distância do stop ou aceite mais risco.</span>';
    if (custo > cap) s += '<br><span class="warn">A posição custaria mais que o capital: o limite real é o caixa, não o risco.</span>';
    if (rr < 1) s += '<br><span class="warn">R:R abaixo de 1 : 1 — você arrisca mais do que pode ganhar. Só se compensa com taxa de acerto muito alta (módulo 7).</span>';
    s += '<br><span class="note">Didático: não inclui custos, spread nem slippage. No mercado fracionário compra-se de 1 em 1; no lote padrão, de 100 em 100.</span>';
    html(o, s);
  }
  ["pCap", "pRisk", "pEnt", "pStop", "pAlvo"].forEach(function (id) { $(id).addEventListener("input", drawPlano); });
  labs.m6 = drawPlano;

  // M7 — expectativa
  var seed = 21;
  function drawExp() {
    var p = parseInt($("eWin").value, 10), g = parseInt($("eGain").value, 10), l = parseInt($("eLoss").value, 10);
    $("eP").textContent = p; $("eG").textContent = g; $("eL").textContent = l;
    var r = rng(seed), eq = 10000, a = [eq], pk = eq, mdd = 0;
    for (var i = 0; i < 100; i++) { eq += r() < p / 100 ? g : -l; a.push(eq); pk = Math.max(pk, eq); mdd = Math.max(mdd, (pk - eq) / pk); }
    var s = $("expSvg"); clear(s);
    var lo = Math.min.apply(null, a.concat([10000])), hi = Math.max.apply(null, a.concat([10000])), pad = (hi - lo) * 0.08 || 100; lo -= pad; hi += pad;
    var X = function (i) { return 60 + i * 5.7; }, Y = function (v) { return 200 - (v - lo) / (hi - lo) * 180; };
    s.appendChild(svg("line", { x1: 60, x2: 630, y1: Y(10000), y2: Y(10000), stroke: "#2c3245", "stroke-dasharray": "4 4" }));
    s.appendChild(svg("text", { x: 2, y: Y(10000) + 4 }, "início"));
    s.appendChild(svg("text", { x: 2, y: 24 }, brl(hi).replace(",00", "")));
    s.appendChild(svg("text", { x: 2, y: 200 }, brl(lo).replace(",00", "")));
    var end = a[a.length - 1];
    s.appendChild(svg("polyline", { points: a.map(function (v, i) { return X(i) + "," + Y(v); }).join(" "), fill: "none", stroke: end >= 10000 ? "#34d399" : "#f26d6d", "stroke-width": 2.4 }));
    var E = p / 100 * g - (1 - p / 100) * l, be = l / (g + l) * 100;
    html($("expOut"),
      '<span class="k">Expectativa por operação: <strong class="' + (E >= 0 ? "pos" : "neg") + '">' + (E >= 0 ? "+" : "−") + brl(Math.abs(E)) + "</strong></span>" +
      '<span class="k">Acerto de equilíbrio: <strong>' + pct(be, 1) + "</strong></span>" +
      '<span class="k">Capital final: <strong>' + brl(end) + "</strong></span>" +
      '<span class="k">Maior drawdown: <strong>' + pct(mdd * 100, 1) + "</strong></span><br>" +
      (E >= 0 ? "Expectativa positiva, mas repare nas sequências ruins no caminho." : "Expectativa negativa: com o tempo, o resultado tende ao prejuízo mesmo com sorte no meio.") +
      ' <span class="note">Sequência fictícia sorteada com semente fixa; “Sortear outra” mostra que o caminho muda e a expectativa não.</span>');
  }
  ["eWin", "eGain", "eLoss"].forEach(function (id) { $(id).addEventListener("input", drawExp); });
  $("expNew").addEventListener("click", function () { seed = (seed * 7 + 13) % 100000; drawExp(); });
  labs.m7 = drawExp;

  // M8 — drawdown
  function drawDD() {
    var d = parseInt($("ddPct").value, 10); $("ddOut").textContent = d;
    var need = d / (100 - d) * 100;
    html($("ddDesc"), "Uma queda de <strong class=\"neg\">" + d + "%</strong> exige um ganho de <strong class=\"pos\">" + pct(need, 1) + "</strong> só para voltar ao ponto de partida. Com R$ 10.000, você cairia para <strong>" + brl(10000 * (100 - d) / 100) + "</strong> e precisaria chegar de volta a R$ 10.000.");
    var rows = "";
    [10, 20, 30, 40, 50, 60, 70, 80, 90].forEach(function (x) {
      var n = x / (100 - x) * 100;
      rows += '<div class="row"' + (x === d ? ' style="color:#eef1f8;font-weight:800"' : "") + "><span>Queda " + x + "%</span><span class=\"tr\"><i class=\"g\" style=\"width:" + (n / 900 * 100).toFixed(1) + '%"></i></span><span>+' + fmt(n, 0) + "%</span></div>";
    });
    html($("ddBars"), rows);
  }
  $("ddPct").addEventListener("input", drawDD);
  labs.m8 = drawDD;

  // M9 — diversificação
  function drawDiv() {
    var n = parseInt($("dvN").value, 10); $("dvOut").textContent = n;
    var base = 30, r = base / Math.sqrt(n), r1 = base, rn = n < 20 ? base / Math.sqrt(n + 1) : r;
    html($("dvDesc"), '<span class="k">Peso por ativo: <strong>' + pct(100 / n, 1) + '</strong></span><span class="k">Risco específico estimado: <strong>' + pct(r, 1) + ' a.a.</strong> (com 1 ativo: ' + pct(r1, 0) + ')</span><span class="k">Redução com mais um ativo: <strong>' + (n < 20 ? pct(r - rn, 1) : "—") + "</strong></span><br>" +
      (n < 5 ? "Poucos ativos: cada um pesa muito, e um mau resultado individual pode dominar a carteira." : n < 12 ? "Os ganhos de diversificar já diminuem a cada ativo novo." : "Retornos decrescentes: o risco de mercado continua, e acompanhar muitos ativos também custa atenção.") +
      " <span class=\"note\">Suposição: cada ativo com 30% a.a. de volatilidade, independentes. Valores ilustrativos.</span>");
  }
  $("dvN").addEventListener("input", drawDiv);
  labs.m9 = drawDiv;

  // M10 — checklist
  var boxes = Array.prototype.slice.call(document.querySelectorAll("#cicloList input"));
  function drawCiclo() {
    var n = boxes.filter(function (b) { return b.checked; }).length;
    $("cicloOut").textContent = n === boxes.length ? "Ciclo completo. Repita em cada decisão, ganhando ou perdendo." : n + " de " + boxes.length + " etapas marcadas.";
  }
  boxes.forEach(function (b) { b.addEventListener("change", drawCiclo); });
  drawCiclo();
  labs.m1 = null; labs.m2 = null; labs.m10 = drawCiclo;

  /* ---------------- início ---------------- */
  $("reset").addEventListener("click", function () {
    if (!window.confirm("Apagar o progresso deste treinamento neste navegador?")) return;
    mem = { done: {}, q: {} }; save();
    Array.prototype.forEach.call(document.querySelectorAll("[data-quiz]"), renderQuiz);
    go(ids[0], true);
  });
  load();
  buildToc();
  Array.prototype.forEach.call(document.querySelectorAll("[data-quiz]"), renderQuiz);
  window.addEventListener("hashchange", function () { var h = location.hash.slice(1); if (ids.indexOf(h) >= 0 && h !== current) go(h, false); });
  var start = location.hash.slice(1);
  if (ids.indexOf(start) < 0) { start = ids.filter(function (id) { return !mem.done[id]; })[0] || ids[0]; }
  go(start, false);
})();
