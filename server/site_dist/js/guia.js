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
        var th = el("span", "th"); var im = new Image(); im.src = t.img; im.alt = ""; im.loading = "lazy"; im.width = 78; im.height = 104; th.appendChild(im); b.appendChild(th);
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

  /* ---------- tela ---------- */
  function render(t) {
    var i = T.indexOf(t);
    viewer.textContent = "";
    var art = el("article", "tela");
    art.appendChild(el("p", "kick", "Tela " + (i + 1) + " de " + T.length + " · " + t.grupo));
    art.appendChild(el("h2", null, t.titulo));
    var onde = el("p", "onde"); onde.appendChild(el("b", null, "Onde fica: ")); onde.appendChild(document.createTextNode(t.onde)); art.appendChild(onde);
    art.appendChild(el("p", "obj", t.objetivo));

    var cols = el("div", "cols" + (t.kind === "w" ? " web" : ""));
    var sc = el("div", "shotcol");
    var pw = el("div", "pwrap" + (t.kind === "w" ? " w" : ""));
    var img = new Image(); img.src = t.img; img.alt = t.alt; img.width = t.kind === "w" ? 800 : 780; img.height = t.kind === "w" ? 500 : 1688; img.draggable = false; pw.appendChild(img);
    var pins = [], items = [];
    var note = el("p", "pinnote"); note.setAttribute("aria-live", "polite"); note.textContent = "Toque num número da captura para ver o que ele mostra.";
    function pick(k, scroll) {
      pins.forEach(function (p, j) { p.classList.toggle("on", j === k); });
      items.forEach(function (b, j) { b.classList.toggle("on", j === k); });
      note.textContent = "";
      var b = el("b", null, (k + 1) + ". "); note.appendChild(b); note.appendChild(document.createTextNode(t.can[k][0]));
      if (scroll && items[k] && items[k].scrollIntoView) { var r = items[k].getBoundingClientRect(); if (r.top < 0 || r.bottom > innerHeight) items[k].scrollIntoView({ block: "center", behavior: "smooth" }); }
    }
    t.can.forEach(function (c, k) {
      var p = el("button", "gpin", String(k + 1)); p.type = "button"; p.style.left = c[1] + "%"; p.style.top = c[2] + "%";
      p.setAttribute("aria-label", "Ponto " + (k + 1) + ": " + c[0]); p.addEventListener("click", function () { pick(k, false); }); pw.appendChild(p); pins.push(p);
    });
    var tg = el("button", "tgl", "Números na tela"); tg.type = "button"; tg.setAttribute("aria-pressed", "true");
    tg.addEventListener("click", function () { var off = pw.classList.toggle("nopins"); tg.setAttribute("aria-pressed", String(!off)); });
    sc.appendChild(pw); sc.appendChild(tg); sc.appendChild(note); cols.appendChild(sc);

    var info = el("div", "info");
    var s1 = el("section"); s1.appendChild(el("h3", null, "O que dá para fazer"));
    var ol = el("ol", "can");
    t.can.forEach(function (c, k) {
      var li = el("li"), b = el("button"); b.type = "button"; b.appendChild(el("span", "n", String(k + 1))); b.appendChild(el("span", null, c[0]));
      b.addEventListener("click", function () { pick(k, false); if (sc.getBoundingClientRect().bottom < 0) sc.scrollIntoView({ block: "center", behavior: "smooth" }); });
      li.appendChild(b); ol.appendChild(li); items.push(b);
    });
    s1.appendChild(ol); if (t.guard) s1.appendChild(el("p", "guardl", t.guard)); info.appendChild(s1);

    var s2 = el("section"); s2.appendChild(el("h3", null, "Missão prática: repita no app"));
    var ul = el("ul", "mis"); mem.mis[t.id] = mem.mis[t.id] || [];
    t.missao.forEach(function (m, k) {
      var li = el("li"), lb = el("label"), cb = el("input"); cb.type = "checkbox"; cb.checked = !!mem.mis[t.id][k];
      cb.addEventListener("change", function () { mem.mis[t.id][k] = cb.checked; save(); refresh(); });
      lb.appendChild(cb); lb.appendChild(el("span", null, m)); li.appendChild(lb); ul.appendChild(li);
    });
    s2.appendChild(ul); info.appendChild(s2);

    var s3 = el("section"); s3.appendChild(el("h3", null, "Teste rápido"));
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
        why.textContent = ok ? "Correto. " + t.quiz.why : "Ainda não. Releia “O que dá para fazer” e tente outra opção.";
        if (ok) { mem.q[t.id] = true; save(); refresh(); }
      });
      fs.appendChild(lb);
    });
    fs.appendChild(why);
    if (mem.q[t.id]) { var rs = fs.querySelectorAll("input"); rs[t.quiz.a].checked = true; fs.querySelectorAll("label")[t.quiz.a].classList.add("ok"); why.hidden = false; why.className = "why ok"; why.textContent = "Correto. " + t.quiz.why; }
    s3.appendChild(fs); info.appendChild(s3);
    cols.appendChild(info); art.appendChild(cols);

    var pg = el("div", "pager");
    var pv = el("button", "btn ghost", "← Anterior"); pv.type = "button"; if (i === 0) pv.disabled = true; pv.addEventListener("click", function () { go(T[i - 1].id, true); });
    var nx = el("button", "btn", i === T.length - 1 ? "Concluir" : "Próxima →"); nx.type = "button";
    nx.addEventListener("click", function () { if (i === T.length - 1) { window.scrollTo({ top: 0, behavior: "smooth" }); } else go(T[i + 1].id, true); });
    pg.appendChild(pv); pg.appendChild(nx); art.appendChild(pg);
    art.appendChild(el("p", "hintm", "Dica: deslize para os lados para trocar de tela."));
    viewer.appendChild(art);
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
  viewer.addEventListener("touchstart", function (e) { if (e.touches.length !== 1 || e.target.closest("input,label,.gpin")) { sx = null; return; } sx = e.touches[0].clientX; sy = e.touches[0].clientY; }, { passive: true });
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
