(function () {
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var body = document.body;
  var bar = document.querySelector(".bar");

  /* 1 — threshold: a light that reveals the sculpture */
  var intro = document.querySelector(".j-intro"), lit = intro && intro.querySelector(".lit");
  if (intro) {
    requestAnimationFrame(function () { intro.classList.add("on"); });
    if (!reduce && lit) {
      var r = 0, target = Math.max(innerWidth, innerHeight) * 0.28, x = 50, y = 45, tx = 50, ty = 45, moved = false, t0 = performance.now();
      var touch = window.matchMedia("(hover: none)").matches;
      intro.addEventListener("pointermove", function (e) {
        var b = intro.getBoundingClientRect();
        tx = (e.clientX - b.left) / b.width * 100; ty = (e.clientY - b.top) / b.height * 100; moved = true;
      });
      (function loop(now) {
        r += (target - r) * 0.03;
        if (!moved || touch) { var k = (now - t0) / 4200; tx = 50 + Math.sin(k) * 9; ty = 44 + Math.cos(k * 0.8) * 7; }
        x += (tx - x) * 0.06; y += (ty - y) * 0.06;
        lit.style.setProperty("--r", r.toFixed(1) + "px");
        lit.style.setProperty("--x", x.toFixed(2) + "%");
        lit.style.setProperty("--y", y.toFixed(2) + "%");
        if (intro.getBoundingClientRect().bottom > 0) requestAnimationFrame(loop); else setTimeout(function () { requestAnimationFrame(loop); }, 400);
      })(t0);
    }
  }

  /* 2 — reveal-on-scroll and the colour of each chapter */
  var io = new IntersectionObserver(function (es) {
    es.forEach(function (e) { if (e.isIntersecting) e.target.classList.add("in"); });
  }, { threshold: 0.28 });
  document.querySelectorAll(".j-work,.j-grain,.j-workshop,.j-light").forEach(function (el) { io.observe(el); });

  var tones = document.querySelectorAll("[data-tone]");
  var progress = document.querySelector(".j-progress");
  var links = progress ? progress.querySelectorAll("a") : [];
  var io2 = new IntersectionObserver(function (es) {
    es.forEach(function (e) {
      if (!e.isIntersecting) return;
      body.style.backgroundColor = e.target.dataset.tone;
      var ch = e.target.dataset.ch;
      links.forEach(function (a) { a.classList.toggle("cur", a.dataset.ch === ch); });
    });
  }, { rootMargin: "-45% 0px -45% 0px" });
  tones.forEach(function (el) { io2.observe(el); });

  function onScroll() {
    var y = scrollY, h = innerHeight;
    if (progress) progress.classList.toggle("on", y > h * 1.6 && y < document.body.scrollHeight - h * 2.2);
  }
  addEventListener("scroll", onScroll, { passive: true }); onScroll();
})();
