/* Boris+ — Guia das telas (treinamento tela a tela). Vanilla JS, sem dependências.
   Dados em js/telas-data.js. Progresso em localStorage (opcional). Mobile-first. */
(function () {
  "use strict";
  var T = window.TELAS || [];
  var viewer = document.getElementById("viewer"), mapa = document.getElementById("mapa");
  if (!T.length || !viewer) return;
  var KEY = "boris-guia-v1", mem = { mis: {}, q: {} }, cur = null;
  var $ = function (id) { return document.getElementById(id); };
  var el = function (tag, cls, txt) { var e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; };

  function load() {
    try { var r = localStorage.getItem(KEY); if (r) { var o = JSON.parse(r); if (o && typeof o === "object") mem = { mis: o.mis || {}, q: o.q || {} }; } } catch (e) {}
  }
  function save() { try { localStorage.setItem(KEY, JSON.stringify(mem)); } catch (e) {} }
  function misDone(t) { var m = mem.mis[t.id] || []; return t.missao.every(function (_, i) { return m[i]; }); }
  function isDone(t) { return !!mem.q[t.id] && misDone(t); }

  /* ---------- mapa ---------- */
  function buildMapa() {
    mapa.textContent = "";
    var groups = [], map = {};
    T.forEach(function (t) { if (!map[t.grupo]) { map[t.grupo] = []; groups.push(t.grupo); } map[t.grupo].push(t); });
    groups.forEach(function (g) {
      var box = el("div", "grp"); box.appendChild(el("p", "gl", g));
      var row = el("div", "row");
      map[g].forEach(function (t) {
        var b = el("button"); b.type = "button"; b.dataset.id = t.id; b.setAttribute("aria-label", t.titulo);
        var th = el("span", "th"); var im = new Image(); im.src = (window.TELAS_BASE || "") + t.img; im.alt = ""; im.loading = "lazy"; im.width = 78; im.height = 104; th.appendChild(im); b.appendChild(th);
        b.appendChild(el("span", "nm", t.titulo)); b.appendChild(el("span", "ok", "✓"));
        b.addEventListener("click", function () { go(t.id, true); });
        row.appendChild(b);
      });
      box.appendChild(row); mapa.appendChild(box);
    });
  }
  function refresh() {
    var n = T.filter(isDone).length;
    $("gTxt").textContent = n + " de " + T.length + " telas";
    $("gFill").style.width = (n / T.length * 100) + "%";
    $("gBar").setAttribute("aria-valuenow", String(Math.round(n / T.length * 100)));
    Array.prototype.forEach.call(mapa.querySelectorAll("button"), function (b) {
      var t = T.filter(function (x) { return x.id === b.dataset.id; })[0];
      b.classList.toggle("done", isDone(t));
      if (b.dataset.id === cur) b.setAttribute("aria-current", "step"); else b.removeAttribute("aria-current");
    });
  }

  /* ---------- tela ----------
     Lente: a captura fica numa moldura fixa; a câmera dá zoom no ponto ativo, o resto escurece
     (translúcido) e a explicação aparece num cartão de vidro colado ao ponto. Sem linhas, sem
     marcadores cobrindo conteúdo. Abaixo da lente, abas: Pontos · Missão · Teste. */
  function render(t) {
    var i = T.indexOf(t), web = t.kind === "w", base = window.TELAS_BASE || "";
    viewer.textContent = "";
    var art = el("article", "tela");
    var head = el("header", "thead");
    head.appendChild(el("p", "kick", "Tela " + (i + 1) + " de " + T.length + " · " + t.grupo));
    head.appendChild(el("h2", null, t.titulo));
    var onde = el("p", "onde"); onde.appendChild(el("b", null, "Onde fica: ")); onde.appendChild(document.createTextNode(t.onde)); head.appendChild(onde);
    art.appendChild(head);

    var cols = el("div", "cols" + (web ? " web" : ""));
    /* --- lente --- */
    var sc = el("div", "shotcol");
    var lens = el("div", "lens" + (web ? " w" : "")); lens.setAttribute("role", "group"); lens.setAttribute("aria-label", "Captura de " + t.titulo + " com os pontos explicados");
    var cam = el("div", "cam");
    var img = new Image(); img.src = base + t.img; img.alt = t.alt; img.draggable = false; cam.appendChild(img);
    var ghosts = [];
    t.can.forEach(function (c, k) {
      var g = el("button", "ghost", String(k + 1)); g.type = "button"; g.style.left = c[1] + "%"; g.style.top = c[2] + "%";
      g.setAttribute("aria-label", "Ponto " + (k + 1) + ": " + c[0]); g.addEventListener("click", function () { focusAt(k, true); }); cam.appendChild(g); ghosts.push(g);
    });
    var spot = el("div", "spot"), ring = el("div", "ring");
    var glass = el("div", "glass"); glass.setAttribute("aria-live", "polite");
    var gtop = el("div", "gtop"), gcount = el("span", "gcount"), gnav = el("span", "gnav");
    var pv = el("button", "gb", "‹"); pv.type = "button"; pv.setAttribute("aria-label", "Ponto anterior");
    var nx = el("button", "gb", "›"); nx.type = "button"; nx.setAttribute("aria-label", "Próximo ponto");
    gnav.appendChild(pv); gnav.appendChild(nx); gtop.appendChild(gcount); gtop.appendChild(gnav);
    var gtxt = el("p", "gtxt"); glass.appendChild(gtop); glass.appendChild(gtxt);
    var wide = el("button", "wide", "Tela inteira"); wide.type = "button"; wide.setAttribute("aria-pressed", "false");
    lens.appendChild(cam); lens.appendChild(spot); lens.appendChild(ring); lens.appendChild(glass);
    sc.appendChild(lens);
    var dots = el("div", "stepdots"); dots.setAttribute("role", "tablist"); dots.setAttribute("aria-label", "Pontos da tela");
    var chips = t.can.map(function (c, k) { var b = el("button", null, String(k + 1)); b.type = "button"; b.setAttribute("aria-label", "Ir ao ponto " + (k + 1)); b.addEventListener("click", function () { focusAt(k, true); }); dots.appendChild(b); return b; });
    var ctl = el("div", "ctl"); ctl.appendChild(dots); ctl.appendChild(wide); sc.appendChild(ctl);
    cols.appendChild(sc);

    var cur2 = 0, overview = false, natW = web ? 800 : 780, natH = web ? 500 : 1688;
    function geom() { var vw = lens.clientWidth, vh = lens.clientHeight; return { vw: vw, vh: vh, fit: Math.min(vw / natW, vh / natH), w0: vw / natW }; }
    function place(k) {
      var g = geom(); if (!g.vw) return;
      var c = t.can[k], s2, tx, ty, cxp, cyp;
      if (overview) {
        s2 = g.fit; cam.style.width = natW * s2 + "px"; cam.style.height = natH * s2 + "px";
        tx = (g.vw - natW * s2) / 2; ty = (g.vh - natH * s2) / 2;
      } else {
        s2 = g.w0; cam.style.width = natW * s2 + "px"; cam.style.height = natH * s2 + "px";
        var X = c[1] / 100 * natW * s2, Y = c[2] / 100 * natH * s2;
        tx = g.vw / 2 - X; ty = g.vh * 0.36 - Y;
        tx = Math.min(0, Math.max(g.vw - natW * s2, tx)); ty = Math.min(0, Math.max(g.vh - natH * s2, ty));
        if (natW * s2 <= g.vw) tx = (g.vw - natW * s2) / 2;
        if (natH * s2 <= g.vh) ty = (g.vh - natH * s2) / 2;
        cxp = tx + X; cyp = ty + Y;
        spot.style.top = (cyp - 46) + "px"; ring.style.left = cxp + "px"; ring.style.top = cyp + "px";
        glass.classList.toggle("up", cyp > g.vh * 0.52);
      }
      cam.style.transform = "translate(" + tx + "px," + ty + "px)";
    }
    function focusAt(k, user) {
      cur2 = k; if (overview) { overview = false; wide.setAttribute("aria-pressed", "false"); lens.classList.remove("ov"); }
      place(k);
      ghosts.forEach(function (g, j) { g.classList.toggle("on", j === k); });
      chips.forEach(function (b, j) { b.classList.toggle("on", j === k); if (j === k) b.setAttribute("aria-current", "true"); else b.removeAttribute("aria-current"); });
      items.forEach(function (b, j) { b.classList.toggle("on", j === k); });
      gcount.textContent = "Ponto " + (k + 1) + " de " + t.can.length; gtxt.textContent = t.can[k][0];
      pv.disabled = k === 0; nx.disabled = k === t.can.length - 1;
    }
    pv.addEventListener("click", function () { if (cur2 > 0) focusAt(cur2 - 1, true); });
    nx.addEventListener("click", function () { if (cur2 < t.can.length - 1) focusAt(cur2 + 1, true); });
    wide.addEventListener("click", function () {
      overview = !overview; wide.setAttribute("aria-pressed", String(overview)); lens.classList.toggle("ov", overview);
      if (overview) place(cur2); else focusAt(cur2, true);
    });
    var rz; window.addEventListener("resize", function () { clearTimeout(rz); rz = setTimeout(function () { place(cur2); }, 100); });

    /* --- abas: Pontos · Missão · Teste --- */
    var info = el("div", "info");
    var tabs = el("div", "tabs3"); tabs.setAttribute("role", "tablist");
    var panels = {}, tabBtn = {};
    [["pontos", "Pontos"], ["missao", "Missão"], ["teste", "Teste"]].forEach(function (d) {
      var b = el("button", null, d[1]); b.type = "button"; b.setAttribute("role", "tab"); b.id = "tab-" + d[0]; b.setAttribute("aria-controls", "pn-" + d[0]);
      b.addEventListener("click", function () { showTab(d[0]); }); tabs.appendChild(b); tabBtn[d[0]] = b;
      var p = el("section", "panel"); p.id = "pn-" + d[0]; p.setAttribute("role", "tabpanel"); p.setAttribute("aria-labelledby", "tab-" + d[0]); panels[d[0]] = p;
    });
    function showTab(n) { Object.keys(panels).forEach(function (k) { panels[k].hidden = k !== n; tabBtn[k].setAttribute("aria-selected", String(k === n)); tabBtn[k].tabIndex = k === n ? 0 : -1; }); }
    info.appendChild(tabs);

    // Pontos
    var items = [];
    panels.pontos.appendChild(el("p", "obj", t.objetivo));
    var ol = el("ol", "can");
    t.can.forEach(function (c, k) {
      var li = el("li"), b = el("button"); b.type = "button"; b.appendChild(el("span", "n", String(k + 1))); b.appendChild(el("span", null, c[0]));
      b.addEventListener("click", function () { focusAt(k, true); var r = lens.getBoundingClientRect(); if (r.top < 0 || r.bottom > innerHeight) lens.scrollIntoView({ block: "center", behavior: "smooth" }); });
      li.appendChild(b); ol.appendChild(li); items.push(b);
    });
    panels.pontos.appendChild(ol); if (t.guard) panels.pontos.appendChild(el("p", "guardl", t.guard));

    // Missão
    var ul = el("ul", "mis"); mem.mis[t.id] = mem.mis[t.id] || [];
    t.missao.forEach(function (m, k) {
      var li = el("li"), lb = el("label"), cb = el("input"); cb.type = "checkbox"; cb.checked = !!mem.mis[t.id][k];
      cb.addEventListener("change", function () { mem.mis[t.id][k] = cb.checked; save(); refresh(); badge(); });
      lb.appendChild(cb); lb.appendChild(el("span", null, m)); li.appendChild(lb); ul.appendChild(li);
    });
    panels.missao.appendChild(el("p", "obj", "Repita no app, com o saldo virtual:")); panels.missao.appendChild(ul);

    // Teste
    var fs = el("fieldset", "qz"); fs.appendChild(el("legend", null, t.quiz.q));
    var why = el("p", "why"); why.hidden = true; why.setAttribute("role", "status");
    t.quiz.o.forEach(function (txt, j) {
      var lb = el("label"), r = el("input"); r.type = "radio"; r.name = "q-" + t.id; r.value = j;
      lb.appendChild(r); lb.appendChild(document.createTextNode(" " + txt));
      r.addEventListener("change", function () {
        var ok = j === t.quiz.a;
        Array.prototype.forEach.call(fs.querySelectorAll("label"), function (l) { l.classList.remove("ok", "bad"); });
        lb.classList.add(ok ? "ok" : "bad");
        why.hidden = false; why.className = "why " + (ok ? "ok" : "bad");
        why.textContent = ok ? "Correto. " + t.quiz.why : "Ainda não. Releia os pontos e tente outra opção.";
        if (ok) { mem.q[t.id] = true; save(); refresh(); badge(); }
      });
      fs.appendChild(lb);
    });
    fs.appendChild(why);
    if (mem.q[t.id]) { var rs = fs.querySelectorAll("input"); rs[t.quiz.a].checked = true; fs.querySelectorAll("label")[t.quiz.a].classList.add("ok"); why.hidden = false; why.className = "why ok"; why.textContent = "Correto. " + t.quiz.why; }
    panels.teste.appendChild(fs);

    function badge() { // marca na aba o que já foi feito
      tabBtn.missao.textContent = "Missão" + (misDone(t) ? " ✓" : ""); tabBtn.teste.textContent = "Teste" + (mem.q[t.id] ? " ✓" : "");
    }
    Object.keys(panels).forEach(function (k) { info.appendChild(panels[k]); });
    showTab("pontos"); badge();
    cols.appendChild(info); art.appendChild(cols);

    var pg = el("div", "pager");
    var pvT = el("button", "btn ghost", "← Tela anterior"); pvT.type = "button"; if (i === 0) pvT.disabled = true; pvT.addEventListener("click", function () { go(T[i - 1].id, true); });
    var nxT = el("button", "btn", i === T.length - 1 ? "Concluir" : "Próxima tela →"); nxT.type = "button";
    nxT.addEventListener("click", function () { if (i === T.length - 1) { window.scrollTo({ top: 0, behavior: "smooth" }); } else go(T[i + 1].id, true); });
    pg.appendChild(pvT); pg.appendChild(nxT); art.appendChild(pg);
    viewer.appendChild(art);
    /* a lente só tem medida depois de montada e com a imagem carregada */
    var go1 = function () { focusAt(0, false); };
    if (img.complete) requestAnimationFrame(go1); else img.addEventListener("load", go1);
    requestAnimationFrame(function () { requestAnimationFrame(go1); });
  }

  function go(id, focus) {
    var t = T.filter(function (x) { return x.id === id; })[0] || T[0];
    cur = t.id; render(t); refresh();
    if (location.hash !== "#" + t.id) { try { history.replaceState(null, "", "#" + t.id); } catch (e) {} }
    if (focus) {
      var h = viewer.querySelector("h2"); h.setAttribute("tabindex", "-1"); h.focus({ preventScroll: true });
      viewer.scrollIntoView({ behavior: "smooth", block: "start" });
      var cb = mapa.querySelector('button[data-id="' + t.id + '"]'); if (cb && cb.scrollIntoView) { try { cb.scrollIntoView({ block: "nearest", inline: "center" }); } catch (e) {} }
    }
  }

  /* swipe (celular) */
  var sx = null, sy = null;
  viewer.addEventListener("touchstart", function (e) { if (e.touches.length !== 1 || e.target.closest("input,label,.lens,.tabs3")) { sx = null; return; } sx = e.touches[0].clientX; sy = e.touches[0].clientY; }, { passive: true });
  viewer.addEventListener("touchend", function (e) {
    if (sx == null) return;
    var dx = e.changedTouches[0].clientX - sx, dy = e.changedTouches[0].clientY - sy; sx = null;
    if (Math.abs(dx) < 70 || Math.abs(dx) < Math.abs(dy) * 1.8) return;
    var i = T.map(function (t) { return t.id; }).indexOf(cur);
    var n = dx < 0 ? i + 1 : i - 1; if (n >= 0 && n < T.length) go(T[n].id, true);
  }, { passive: true });
  document.addEventListener("keydown", function (e) {
    if (e.target.closest && e.target.closest("input,textarea,select")) return;
    var i = T.map(function (t) { return t.id; }).indexOf(cur);
    if (e.key === "ArrowRight" && i < T.length - 1) go(T[i + 1].id, true);
    else if (e.key === "ArrowLeft" && i > 0) go(T[i - 1].id, true);
  });

  $("gReset").addEventListener("click", function () {
    if (!window.confirm("Apagar o progresso do guia neste navegador?")) return;
    mem = { mis: {}, q: {} }; save(); go(cur || T[0].id, false);
  });
  window.addEventListener("hashchange", function () { var h = location.hash.slice(1); if (h && h !== cur) go(h, false); });

  load(); buildMapa();
  var start = location.hash.slice(1);
  if (!T.some(function (t) { return t.id === start; })) { var first = T.filter(function (t) { return !isDone(t); })[0]; start = (first || T[0]).id; }
  go(start, !!location.hash);
})();
