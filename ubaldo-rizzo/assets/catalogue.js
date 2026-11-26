(function () {
  var cards = [].slice.call(document.querySelectorAll(".cat-grid .wcard"));
  var rows = [].slice.call(document.querySelectorAll(".cat-list a"));
  var state = { period: "all", type: "all", mat: "all", q: "", sort: "no" };
  var qs = new URLSearchParams(location.search);
  ["period", "type", "mat", "q", "sort"].forEach(function (k) { if (qs.get(k)) state[k] = qs.get(k); });
  if (qs.get("view") === "list") document.body.classList.add("list");

  function norm(s) { return (s || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, ""); }
  function match(el) {
    var d = el.dataset;
    return (state.period === "all" || d.period === state.period) &&
           (state.type === "all" || d.type === state.type) &&
           (state.mat === "all" || d.mat === state.mat) &&
           (!state.q || norm(d.search).indexOf(norm(state.q)) >= 0);
  }
  function key(el) {
    var d = el.dataset;
    return state.sort === "title" ? norm(d.title) : state.sort === "year" ? (d.year || "9999") + d.no : d.no;
  }
  function apply() {
    var n = 0;
    [cards, rows].forEach(function (list) {
      var parent = list[0] && list[0].parentNode;
      list.sort(function (a, b) { return key(a) < key(b) ? -1 : key(a) > key(b) ? 1 : 0; });
      list.forEach(function (el) { var ok = match(el); el.classList.toggle("hide", !ok); parent.appendChild(el); });
    });
    cards.forEach(function (c) { if (!c.classList.contains("hide")) n++; });
    document.querySelectorAll(".count .num").forEach(function (s) { s.textContent = n; });
    document.querySelector(".empty").classList.toggle("hide", n > 0);
    document.querySelectorAll(".chip[data-k]").forEach(function (c) { c.setAttribute("aria-pressed", state[c.dataset.k] === c.dataset.v); });
    var u = new URLSearchParams();
    Object.keys(state).forEach(function (k) { if (state[k] && state[k] !== "all" && !(k === "sort" && state[k] === "no")) u.set(k, state[k]); });
    if (document.body.classList.contains("list")) u.set("view", "list");
    history.replaceState(null, "", location.pathname + (u.toString() ? "?" + u : ""));
  }
  document.querySelectorAll(".chip[data-k]").forEach(function (c) {
    c.addEventListener("click", function () { state[c.dataset.k] = c.dataset.v; apply(); });
  });
  var mat = document.getElementById("f-mat"), q = document.getElementById("f-q"), so = document.getElementById("f-sort");
  mat.value = state.mat; q.value = state.q; so.value = state.sort;
  mat.addEventListener("change", function () { state.mat = mat.value; apply(); });
  q.addEventListener("input", function () { state.q = q.value.trim(); apply(); });
  so.addEventListener("change", function () { state.sort = so.value; apply(); });
  document.querySelectorAll(".viewsw .chip").forEach(function (b) {
    b.addEventListener("click", function () {
      document.body.classList.toggle("list", b.dataset.view === "list");
      document.querySelectorAll(".viewsw .chip").forEach(function (x) { x.setAttribute("aria-pressed", x === b); });
      apply();
    });
    b.setAttribute("aria-pressed", (b.dataset.view === "list") === document.body.classList.contains("list"));
  });
  apply();
})();
