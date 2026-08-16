/* Anime Epic Moments — particles.js
   Лёгкие фоновые частицы поверх арта темы. Без внешних зависимостей.
   Цвета берутся из CSS-переменных темы, обновляются при смене темы. */
(function () {
  "use strict";

  var canvas, ctx, particles = [];
  var running = false;
  var reduced = false;

  function prefersReduced() {
    return (
      window.matchMedia &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches
    );
  }

  function themeColors() {
    var css = getComputedStyle(document.documentElement);
    var a = css.getPropertyValue("--particle-color").trim() || "#f472b6";
    var b = css.getPropertyValue("--particle-color-2").trim() || "#22d3ee";
    return [a, b];
  }

  function resize() {
    if (!canvas) return;
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }

  function init() {
    if (reduced) return;
    canvas = document.getElementById("particles-canvas");
    if (!canvas) return;
    ctx = canvas.getContext("2d");
    resize();
    var count = Math.min(Math.floor((window.innerWidth * window.innerHeight) / 26000), 46);
    var colors = themeColors();
    for (var i = 0; i < count; i++) {
      particles.push({
        x: Math.random() * window.innerWidth,
        y: Math.random() * window.innerHeight,
        r: Math.random() * 2.2 + 0.6,
        vx: (Math.random() - 0.5) * 0.22,
        vy: -Math.random() * 0.28 - 0.05,
        color: colors[i % 2],
        alpha: Math.random() * 0.35 + 0.12,
        pulse: Math.random() * Math.PI * 2,
      });
    }
    running = true;
    requestAnimationFrame(loop);
  }

  function loop() {
    if (!running) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (var i = 0; i < particles.length; i++) {
      var p = particles[i];
      p.x += p.vx;
      p.y += p.vy;
      p.pulse += 0.02;
      if (p.y < -12) {
        p.y = canvas.height + 12;
        p.x = Math.random() * canvas.width;
      }
      if (p.x < -12) p.x = canvas.width + 12;
      if (p.x > canvas.width + 12) p.x = -12;
      var alpha = p.alpha * (0.75 + 0.25 * Math.sin(p.pulse));
      ctx.globalAlpha = alpha;
      ctx.fillStyle = p.color;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.globalAlpha = 1;
    requestAnimationFrame(loop);
  }

  function restart() {
    particles = [];
    if (running) {
      running = false;
      if (ctx) ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
    init();
  }

  document.addEventListener("DOMContentLoaded", function () {
    reduced = prefersReduced();
    init();
  });

  window.addEventListener("resize", function () {
    resize();
  });

  document.addEventListener("aem:themechange", function () {
    if (reduced) return;
    var colors = themeColors();
    for (var i = 0; i < particles.length; i++) {
      particles[i].color = colors[i % 2];
    }
  });
})();