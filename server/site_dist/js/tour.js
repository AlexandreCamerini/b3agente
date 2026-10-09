/* Boris+ — tour em canvas (estilo Figma, na web). Vanilla JS, sem dependências.
   Pan: arrastar / rolagem. Zoom: Ctrl|⌘ + rolagem, pinça, botões, + e −. Teclado: setas, 0 = ajustar. */
(function () {
  "use strict";
  var root = document.documentElement;
  root.classList.add("tour-js");
  var $ = function (id) { return document.getElementById(id); };
  var board = $("board"), world = $("world");
  if (!board || !world) return;

  var MW = 280, MH = Math.round(280 * 1688 / 780), WW = 520, WH = 325;
  var GAPX = 150;

  /* ---------- conteúdo: cada quadro, o que dá para fazer, e os marcadores ---------- */
  var F = [
    { id: "boas", row: 1, kind: "m", img: "img/01-boas-vindas.jpg", title: "Boas-vindas", sub: "Primeira abertura",
      alt: "Boas-vindas: orçamento simulado de R$ 10.000, perfil de risco e aviso educacional.",
      can: [
        ["Dizer como prefere ser chamado (opcional).", 50, 51],
        ["Definir o orçamento simulado inicial, em dinheiro virtual.", 50, 60],
        ["Escolher o perfil de risco: conservador, moderado ou agressivo.", 50, 69],
        ["Entrar na mesa e começar a treinar.", 50, 76]],
      guard: "Já na entrada: ferramenta educacional, nada é recomendação de investimento." },
    { id: "acomp", row: 1, kind: "m", img: "img/02-acompanhar.jpg", title: "Acompanhar", sub: "O resumo do seu dia",
      alt: "Tela Acompanhar: resumo do dia, patrimônio simulado e estado vazio da curva.",
      can: [
        ["Ver o saldo virtual e a variação do dia, sempre no topo.", 62, 7.5],
        ["Abrir perfil e configurações.", 90, 10.5],
        ["Saber se o mercado está aberto ou fechado e quando abre.", 22, 13],
        ["Ler o resumo do dia: carteira, acumulado e operações.", 50, 37.5],
        ["Acompanhar a curva do patrimônio simulado.", 50, 62],
        ["Ver estados honestos: sem histórico, o app diz “Não há dados suficientes para concluir”.", 50, 78],
        ["Navegar pelas abas: Acompanhar, Radar, Watchlist, Portfólio e Opções.", 50, 96]],
      guard: "Nada de número inventado: o que não existe aparece como vazio explicado." },
    { id: "radar", row: 1, kind: "m", img: "img/09-radar.jpg", title: "Radar de mercado", sub: "Varredura do universo",
      alt: "Radar de mercado: 65 de 74 ativos varridos, 9 sem dados.",
      can: [
        ["Pedir análise de IA para os melhores ativos (“IA no top-N”).", 70, 22],
        ["Buscar um ticker específico.", 36, 41],
        ["Ver o período em uso (ex.: 1 ano, 252 pregões).", 33, 47],
        ["Saber quantos ativos foram varridos e quantos ficaram sem dados.", 45, 55],
        ["Abrir “Como o Radar analisa” para entender o método.", 26, 60],
        ["Ler o card: plano educacional, confiança e o padrão detectado.", 49, 78]],
      guard: "O Radar mostra condições técnicas para estudo, sem recomendação." },
    { id: "watch", row: 1, kind: "m", img: "img/04-watchlist.jpg", title: "Watchlist", sub: "Seus ativos em estudo",
      alt: "Watchlist com PETR4: preço, fonte do dado e plano educacional.",
      can: [
        ["Editar a lista de ativos e atualizar as cotações.", 89, 21],
        ["Filtrar por Estudar alta, Estudar baixa ou Neutros.", 32, 40],
        ["Trocar o modelo de análise: Completo, Tendência, Price Action, Momentum, Volume…", 48, 51],
        ["Ver preço, variação e a fonte do dado de cada ativo.", 13, 70],
        ["Ler o plano educacional e a confiança do padrão.", 45, 80],
        ["Conferir o estado do pregão e o horário da última barra.", 26, 90]],
      guard: "O backend calcula; a IA interpreta dados históricos." },
    { id: "plano", row: 1, kind: "m", img: "img/05-plano-setup.jpg", title: "Plano do setup", sub: "Antes de agir",
      alt: "Plano do setup com régua de invalidação, gatilho e alvo.",
      can: [
        ["Ver invalidação, gatilho e alvo, com o preço atual na régua.", 49, 40],
        ["Ler o regime (ex.: alta) e se o setup é a favor da tendência.", 19, 47.5],
        ["Ver o aviso de amostra insuficiente quando o histórico medido é pequeno.", 31, 51],
        ["Abrir o ticket com “Simular compra…”.", 49, 66.5],
        ["Estudar o ativo com o Bóris ou abrir os indicadores.", 26, 74]],
      guard: "Níveis calculados por regra, nunca pela IA. Stop e alvo nunca são vetados." },
    { id: "ordem", row: 2, kind: "m", img: "img/06-ordem-virtual.jpg", title: "Ordem simulada", sub: "O ticket",
      alt: "Ticket de compra simulada com custo estimado e aviso de operação simulada.",
      can: [
        ["Ajustar a quantidade (lotes de 100).", 50, 37],
        ["Ver o custo estimado antes de confirmar.", 50, 44.5],
        ["Ler o estado: com o mercado fechado, a ordem fica pendente até a abertura e o caixa já é reservado.", 50, 54],
        ["Saber que a execução é inteira ou nenhuma, sem preenchimento parcial.", 49, 62],
        ["Confirmar que é operação simulada: nenhuma ordem real é enviada.", 49, 67.5],
        ["Confirmar ou cancelar a compra.", 68, 74]],
      guard: "Dinheiro virtual, sempre. Nenhuma ordem chega a corretora, bolsa ou banco." },
    { id: "pend", row: 2, kind: "m", img: "img/07-ordem-pendente.jpg", title: "Ordem pendente", sub: "Execução simulada",
      alt: "Aviso de ordem pendente registrada, com execução na abertura do próximo pregão.",
      can: [
        ["Receber a confirmação: ordem pendente registrada, executa na abertura do próximo pregão.", 50, 83.5],
        ["Ver o caixa disponível já reduzido no topo (valor reservado).", 64, 12.5]],
      guard: "Cada ordem tem preço, quantidade, horário, tipo e status; rejeitadas mostram o motivo." },
    { id: "port", row: 2, kind: "m", img: "img/08-portfolio.jpg", title: "Portfólio", sub: "O resultado",
      alt: "Portfólio com patrimônio total, caixa disponível e indicação de carteira simulada.",
      can: [
        ["Abrir o Operador IA (modo avançado, também com execução simulada).", 50, 21],
        ["Ver patrimônio total e resultado aberto.", 24, 41],
        ["Ver caixa disponível e valor em posições.", 23, 48.7],
        ["Entender o estado vazio e ir à Watchlist para a primeira compra simulada.", 50, 59],
        ["Abrir o histórico de operações.", 50, 81.6]],
      guard: "Carteira SIMULADA: ganhos e perdas aparecem sem maquiagem." },
    { id: "boris", row: 2, kind: "m", img: "img/03-boris-assistente.jpg", title: "Bóris, o assistente", sub: "Em qualquer tela do Estudo",
      alt: "Apresentação do Bóris: não recomenda compra ou venda e não envia ordem.",
      can: [
        ["Saber o que ele não faz: não recomenda compra ou venda e não envia ordem.", 50, 44],
        ["Contar com a base de estudo: indicadores, estrutura de preço, setups e vocabulário da B3.", 50, 58.6],
        ["Chamá-lo pela coruja flutuante, em qualquer tela do Estudo.", 50, 70],
        ["Conversar agora ou deixar para depois.", 50, 79]],
      guard: "O Bóris é o professor, nunca o operador." },
    { id: "web1", row: 3, kind: "w", img: "img/web-acompanhar.jpg", title: "Web · Acompanhar", sub: "No navegador",
      alt: "Versão web, aba Acompanhar.",
      can: [
        ["Percorrer os setups da watchlist em carrossel, cada um com anel de confiança.", 27, 66],
        ["Ver o estado do mercado e do horário de pregão.", 50, 24],
        ["Ver o saldo virtual e o caixa no topo.", 85, 17]],
      guard: "Mesmo conteúdo do celular, em layout largo." },
    { id: "web2", row: 3, kind: "w", img: "img/web-plano-setup.jpg", title: "Web · Watchlist", sub: "Cards em colunas",
      alt: "Versão web, Watchlist com dois cards lado a lado.",
      can: [
        ["Comparar o plano de dois ativos lado a lado.", 30, 33],
        ["Ler regime e amostra de cada setup.", 30, 54],
        ["Abrir a compra simulada direto do card.", 50, 80]],
      guard: "Em telas largas, os cards se organizam em colunas." },
    { id: "web3", row: 3, kind: "w", img: "img/web-portfolio.jpg", title: "Web · Portfólio", sub: "Carteira simulada",
      alt: "Versão web, Portfólio.",
      can: [
        ["Abrir o Operador IA.", 50, 36],
        ["Ver patrimônio total e caixa disponível.", 22, 64],
        ["Ver resultado aberto e valor em posições.", 62, 64]],
      guard: "O aviso de carteira simulada acompanha todas as telas." }
  ];
  var ARROWS = [
    ["boas", "acomp", "Entrar na mesa"], ["acomp", "radar", "aba Radar"], ["radar", "watch", "aba Watchlist"],
    ["watch", "plano", "Rolar até o plano"], ["plano", "ordem", "Simular compra…", "wrap"],
    ["ordem", "pend", "Confirmar compra"], ["pend", "port", "aba Portfólio"], ["port", "boris", "coruja, em qualquer tela", "dash"]
  ];
  var ROWS = { 1: "Fluxo no celular · da escolha ao plano", 2: "Fluxo no celular · da ordem ao resultado", 3: "Versão web · o mesmo app no navegador" };

  /* ---------- montagem do canvas ---------- */
  var NS = "http://www.w3.org/2000/svg";
  var el = function (tag, cls, txt) { var e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; };
  var pos = {}, nodes = {};
  var rowTop = { 1: 150 }, rowFirstX = 0;

  function build() {
    var perRow = { 1: 0, 2: 0, 3: 0 };
    F.forEach(function (f) {
      var w = f.kind === "m" ? MW : WW, h = f.kind === "m" ? MH : WH;
      var unitW = (f.kind === "m" ? MW : WW) + GAPX;
      var x = perRow[f.row] * unitW; perRow[f.row]++;
      var fr = el("div", "fr " + f.kind, null);
      fr.id = "fr-" + f.id; fr.style.width = w + "px"; fr.tabIndex = 0; fr.setAttribute("role", "button");
      fr.setAttribute("aria-label", "Quadro " + f.title + ". Enter para focar.");
      var ft = el("div", "ft"); ft.appendChild(el("b", null, f.title)); ft.appendChild(el("span", null, " · " + f.sub)); fr.appendChild(ft);
      var shot = el("div", "fshot"); shot.style.height = h + "px";
      var img = new Image(); img.src = f.img; img.alt = f.alt; img.width = f.kind === "m" ? 780 : 800; img.height = f.kind === "m" ? 1688 : 500; img.draggable = false; img.loading = "lazy";
      shot.appendChild(img);
      f.can.forEach(function (c, i) {
        var p = el("button", "pin", String(i + 1)); p.type = "button"; p.style.left = c[1] + "%"; p.style.top = c[2] + "%";
        p.setAttribute("aria-label", "Ponto " + (i + 1) + ": " + c[0]); p.dataset.f = f.id; p.dataset.i = i;
        shot.appendChild(p);
      });
      fr.appendChild(shot);
      var note = el("div", "note-card"); note.style.width = w + "px";
      note.appendChild(el("h3", null, "O que dá para fazer"));
      var ol = el("ol");
      f.can.forEach(function (c, i) { var li = el("li"); li.dataset.f = f.id; li.dataset.i = i; li.appendChild(el("span", "n", String(i + 1))); li.appendChild(el("span", null, c[0])); ol.appendChild(li); });
      note.appendChild(ol);
      if (f.guard) note.appendChild(el("p", "guard", f.guard));
      fr.appendChild(note);
      world.appendChild(fr);
      nodes[f.id] = { fr: fr, note: note, w: w, h: h, x: x, f: f };
    });
    layout();
  }

  function layout() {
    Array.prototype.forEach.call(world.querySelectorAll(".wires,.chip,.rowlabel"), function (n) { n.remove(); });
    var y = 150;
    [1, 2, 3].forEach(function (r) {
      var maxNote = 0;
      F.forEach(function (f) { if (f.row === r) { var n = nodes[f.id]; n.y = y; n.fr.style.left = n.x + "px"; n.fr.style.top = y + "px"; n.note.style.top = (n.h + 16) + "px"; maxNote = Math.max(maxNote, n.note.offsetHeight); } });
      var lab = el("div", "rowlabel", ROWS[r]); lab.style.left = "0px"; lab.style.top = (y - 86) + "px"; world.appendChild(lab);
      nodes["row" + r] = { bottom: y + (r === 3 ? WH : MH) + 16 + maxNote };
      y = nodes["row" + r].bottom + 170;
    });
    arrows();
  }

  function arrows() {
    var maxX = 0, maxY = 0;
    F.forEach(function (f) { var n = nodes[f.id]; maxX = Math.max(maxX, n.x + n.w); maxY = Math.max(maxY, n.y + n.h + 16 + n.note.offsetHeight); });
    var svg = document.createElementNS(NS, "svg"); svg.setAttribute("class", "wires"); svg.setAttribute("width", maxX + 100); svg.setAttribute("height", maxY + 100);
    svg.setAttribute("aria-hidden", "true");
    svg.innerHTML = '<defs><marker id="ah" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="9" markerHeight="9" orient="auto-start-reverse"><path d="M1 1 L9 5 L1 9 z" fill="#f2a93b"/></marker></defs>';
    world.insertBefore(svg, world.firstChild);
    ARROWS.forEach(function (a) {
      var s = nodes[a[0]], t = nodes[a[1]], d, lx, ly;
      if (a[3] === "wrap") {
        var x1 = s.x + s.w / 2, y1 = s.y + s.h + 16 + s.note.offsetHeight + 10, x2 = t.x + t.w / 2, y2 = t.y - 44, gy = (y1 + y2) / 2, r = 28, sg = x2 < x1 ? -1 : 1;
        d = "M" + x1 + " " + y1 + " L" + x1 + " " + (gy - r) + " Q" + x1 + " " + gy + " " + (x1 + sg * r) + " " + gy + " L" + (x2 - sg * r) + " " + gy + " Q" + x2 + " " + gy + " " + x2 + " " + (gy + r) + " L" + x2 + " " + y2;
        lx = (x1 + x2) / 2; ly = gy;
      } else {
        var xa = s.x + s.w + 12, ya = s.y + s.h / 2, xb = t.x - 14, yb = t.y + t.h / 2, dx = (xb - xa) / 2;
        d = "M" + xa + " " + ya + " C" + (xa + dx) + " " + ya + " " + (xb - dx) + " " + yb + " " + xb + " " + yb;
        lx = (xa + xb) / 2; ly = ya;
      }
      var p = document.createElementNS(NS, "path"); p.setAttribute("d", d); p.setAttribute("fill", "none"); p.setAttribute("stroke", "#f2a93b"); p.setAttribute("stroke-width", "3");
      if (a[3] === "dash") p.setAttribute("stroke-dasharray", "10 9");
      p.setAttribute("marker-end", "url(#ah)"); svg.appendChild(p);
      var chip = el("div", "chip", a[2]); chip.style.left = lx + "px"; chip.style.top = ly + "px"; world.appendChild(chip);
    });
    bounds = { w: maxX, h: maxY };
  }
  var bounds = { w: 0, h: 0 };

  /* ---------- câmera ---------- */
  var st = { x: 40, y: 20, k: 0.75 };
  var reduce = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
  var zl = $("zoomLbl");
  function apply(anim) {
    world.style.transition = anim && !reduce ? "transform .5s cubic-bezier(.2,.7,.2,1)" : "none";
    world.style.transform = "translate(" + st.x + "px," + st.y + "px) scale(" + st.k + ")";
    board.style.backgroundPosition = st.x + "px " + st.y + "px";
    board.style.backgroundSize = (28 * st.k) + "px " + (28 * st.k) + "px";
    if (zl) zl.textContent = Math.round(st.k * 100) + "%";
  }
  var clampK = function (k) { return Math.max(0.12, Math.min(2.5, k)); };
  function zoomAt(px, py, nk, anim) { nk = clampK(nk); st.x = px - (px - st.x) * (nk / st.k); st.y = py - (py - st.y) * (nk / st.k); st.k = nk; apply(anim); }
  function center() { var r = board.getBoundingClientRect(); return [r.width / 2, r.height / 2]; }
  function fitRect(x, y, w, h, maxK) {
    var r = board.getBoundingClientRect(), pad = 60;
    var k = clampK(Math.min((r.width - pad * 2) / w, (r.height - pad * 2) / h, maxK || 1.2));
    st.k = k; st.x = (r.width - w * k) / 2 - x * k; st.y = (r.height - h * k) / 2 - y * k; apply(true);
  }
  function fitAll() { fitRect(0, 0, bounds.w, bounds.h, 1); }
  var sel = null;
  function select(id, fly) {
    if (sel) nodes[sel].fr.classList.remove("on");
    sel = id; var n = nodes[id]; n.fr.classList.add("on");
    Array.prototype.forEach.call(document.querySelectorAll(".layer"), function (b) { b.setAttribute("aria-current", String(b.dataset.f === id)); });
    if (fly) { var h = n.h + 16 + n.note.offsetHeight + 40; fitRect(n.x - 20, n.y - 40, n.w + 40, h, 1.1); }
  }

  /* ---------- interação ---------- */
  var ptr = {}, moved = 0, last = null, pinch0 = null;
  board.addEventListener("pointerdown", function (e) {
    if (e.target.closest(".toolbar,.layers")) return;
    board.setPointerCapture && board.setPointerCapture(e.pointerId);
    ptr[e.pointerId] = { x: e.clientX, y: e.clientY }; moved = 0; board.classList.add("grab");
    if (Object.keys(ptr).length === 2) { var a = Object.values(ptr); pinch0 = { d: Math.hypot(a[0].x - a[1].x, a[0].y - a[1].y), k: st.k }; }
  });
  board.addEventListener("pointermove", function (e) {
    var p = ptr[e.pointerId]; if (!p) return;
    var n = Object.keys(ptr).length;
    if (n === 1) { var dx = e.clientX - p.x, dy = e.clientY - p.y; moved += Math.abs(dx) + Math.abs(dy); st.x += dx; st.y += dy; apply(false); }
    else if (n === 2 && pinch0) {
      ptr[e.pointerId] = { x: e.clientX, y: e.clientY };
      var a = Object.values(ptr), d = Math.hypot(a[0].x - a[1].x, a[0].y - a[1].y), r = board.getBoundingClientRect();
      zoomAt((a[0].x + a[1].x) / 2 - r.left, (a[0].y + a[1].y) / 2 - r.top, pinch0.k * d / pinch0.d, false); moved += 10; return;
    }
    ptr[e.pointerId] = { x: e.clientX, y: e.clientY };
  });
  function up(e) {
    var wasOne = Object.keys(ptr).length === 1;
    delete ptr[e.pointerId]; pinch0 = null;
    if (!Object.keys(ptr).length) board.classList.remove("grab");
    if (wasOne && moved < 6) {
      var t = e.target.closest && e.target.closest(".fr");
      if (t && !e.target.closest(".pin")) select(t.id.slice(3), true);
    }
  }
  board.addEventListener("pointerup", up); board.addEventListener("pointercancel", up);
  board.addEventListener("wheel", function (e) {
    e.preventDefault();
    var r = board.getBoundingClientRect();
    if (e.ctrlKey || e.metaKey) zoomAt(e.clientX - r.left, e.clientY - r.top, st.k * Math.exp(-e.deltaY * 0.01), false);
    else { st.x -= e.deltaX; st.y -= e.deltaY; apply(false); }
  }, { passive: false });
  board.addEventListener("keydown", function (e) {
    var s = 60, c = center(), handled = true;
    if (e.key === "ArrowLeft") st.x += s; else if (e.key === "ArrowRight") st.x -= s;
    else if (e.key === "ArrowUp") st.y += s; else if (e.key === "ArrowDown") st.y -= s;
    else if (e.key === "+" || e.key === "=") { zoomAt(c[0], c[1], st.k * 1.2, true); return e.preventDefault(); }
    else if (e.key === "-") { zoomAt(c[0], c[1], st.k / 1.2, true); return e.preventDefault(); }
    else if (e.key === "0") { fitAll(); return e.preventDefault(); }
    else if (e.key === "Enter" && e.target.classList && e.target.classList.contains("fr")) { select(e.target.id.slice(3), true); return e.preventDefault(); }
    else handled = false;
    if (handled) { e.preventDefault(); apply(true); }
  });
  $("zIn").addEventListener("click", function () { var c = center(); zoomAt(c[0], c[1], st.k * 1.25, true); });
  $("zOut").addEventListener("click", function () { var c = center(); zoomAt(c[0], c[1], st.k / 1.25, true); });
  $("zFit").addEventListener("click", fitAll);
  $("zPins").addEventListener("click", function () { var on = board.classList.toggle("nopins"); this.setAttribute("aria-pressed", String(!on)); });

  // marcador ↔ item da lista
  function hot(f, i, on) {
    var p = world.querySelector('.pin[data-f="' + f + '"][data-i="' + i + '"]'), li = world.querySelector('li[data-f="' + f + '"][data-i="' + i + '"]');
    if (p) p.classList.toggle("hot", on); if (li) li.classList.toggle("hot", on);
  }
  world.addEventListener("pointerover", function (e) { var t = e.target.closest("[data-f][data-i]"); if (t) hot(t.dataset.f, t.dataset.i, true); });
  world.addEventListener("pointerout", function (e) { var t = e.target.closest("[data-f][data-i]"); if (t) hot(t.dataset.f, t.dataset.i, false); });
  world.addEventListener("click", function (e) { var t = e.target.closest(".pin"); if (t) select(t.dataset.f, true); });

  // painel de páginas
  var lay = $("layers"), lb = $("layersBody");
  function buildLayers() {
    var groups = [["Celular", "m"], ["Web", "w"]];
    groups.forEach(function (g) {
      lb.appendChild(el("p", "lh", g[0]));
      F.filter(function (f) { return f.kind === g[1]; }).forEach(function (f) {
        var b = el("button", "layer", f.title); b.type = "button"; b.dataset.f = f.id; b.addEventListener("click", function () { select(f.id, true); });
        lb.appendChild(b);
      });
    });
  }
  $("layersToggle").addEventListener("click", function () { var h = lay.classList.toggle("closed"); this.setAttribute("aria-expanded", String(!h)); });

  /* ---------- alternância canvas / lista ---------- */
  function setView(v) {
    root.setAttribute("data-view", v);
    Array.prototype.forEach.call(document.querySelectorAll("[data-setview]"), function (b) { b.setAttribute("aria-pressed", String(b.dataset.setview === v)); });
    if (v === "canvas") { initCamera(); }
  }
  var inited = false;
  function initCamera() {
    if (inited) return; inited = true;
    var r = board.getBoundingClientRect();
    st.k = r.width < 700 ? 0.5 : 0.7; st.x = lay.classList.contains("closed") ? 40 : 250; st.y = 10; apply(false);
  }
  Array.prototype.forEach.call(document.querySelectorAll("[data-setview]"), function (b) { b.addEventListener("click", function () { setView(b.dataset.setview); }); });

  build(); buildLayers();
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(function () { layout(); });
  setView(window.innerWidth >= 900 ? "canvas" : "lista");
  if (window.innerWidth >= 900) { lay.classList.remove("closed"); $("layersToggle").setAttribute("aria-expanded", "true"); }
  window.addEventListener("resize", function () { /* mantém a câmera; usuário ajusta */ });
})();
