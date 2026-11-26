(function () {
  var root = document.documentElement;
  function setLang(l) {
    root.dataset.lang = l; root.lang = l;
    try { localStorage.setItem("ur-lang", l); } catch (e) {}
    document.querySelectorAll(".langsw button").forEach(function (b) { b.setAttribute("aria-pressed", b.dataset.lang === l); });
    document.querySelectorAll("[data-ph-it]").forEach(function (el) { el.placeholder = el.dataset["ph" + (l === "en" ? "En" : "It")]; });
    document.dispatchEvent(new CustomEvent("langchange", { detail: l }));
  }
  document.querySelectorAll(".langsw button").forEach(function (b) { b.addEventListener("click", function () { setLang(b.dataset.lang); }); });
  setLang(root.dataset.lang || "it");
  var mb = document.querySelector(".menu-btn"), nav = document.querySelector(".bar nav");
  if (mb && nav) mb.addEventListener("click", function () { nav.classList.toggle("open"); mb.setAttribute("aria-expanded", nav.classList.contains("open")); });
  // mark wide images in catalogue cards
  document.querySelectorAll(".wcard .frame img").forEach(function (im) {
    function mark() {
      if (im.naturalWidth > im.naturalHeight * 1.15) {
        im.parentNode.classList.add("wide");
      }
    }
    if (im.complete) mark(); else im.addEventListener("load", mark);
  });
  // work page: views + zoom
  var main = document.getElementById("w-main");
  if (main) {
    var mode = "r", sw = document.querySelector(".restsw"), stage = document.querySelector(".stage");
    function show(src, orig, rest) {
      main.dataset.orig = orig; main.dataset.rest = rest; main.dataset.src = src;
      var useR = rest === "true" && mode === "r";
      main.src = useR ? src : orig;
      stage.classList.toggle("is-restored", useR);
      if (sw) sw.hidden = rest !== "true";
    }
    main.dataset.src = main.src;
    if (sw) sw.querySelectorAll("button").forEach(function (b) {
      b.addEventListener("click", function () {
        mode = b.dataset.v;
        sw.querySelectorAll("button").forEach(function (x) { x.setAttribute("aria-pressed", x === b); });
        show(main.dataset.src, main.dataset.orig, main.dataset.rest);
      });
    });
    document.querySelectorAll(".thumbs button").forEach(function (b) {
      b.addEventListener("click", function () {
        show(b.dataset.src, b.dataset.orig, b.dataset.rest);
        document.querySelectorAll(".thumbs button").forEach(function (x) { x.setAttribute("aria-current", x === b); });
      });
    });
    var z = document.querySelector(".zoom");
    main.addEventListener("click", function () { z.querySelector("img").src = main.src; z.classList.add("on"); });
    z.addEventListener("click", function () { z.classList.remove("on"); });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") z.classList.remove("on");
      if (e.target.closest && e.target.closest("input,select,textarea")) return;
      var a = e.key === "ArrowLeft" ? document.querySelector(".pn .prev") : e.key === "ArrowRight" ? document.querySelector(".pn .next") : null;
      if (a && !z.classList.contains("on")) location.href = a.href;
    });
  }
})();
