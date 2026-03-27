(function () {
  const container = document.getElementById("particles-js");
  if (!container) {
    return;
  }

  const canvas = document.createElement("canvas");
  const context = canvas.getContext("2d");
  container.appendChild(canvas);

  const particles = [];
  const particleCount = 42;

  const resize = () => {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  };

  const spawnParticle = () => ({
    x: Math.random() * canvas.width,
    y: Math.random() * canvas.height,
    r: 1 + Math.random() * 2.8,
    vx: (Math.random() - 0.5) * 0.35,
    vy: (Math.random() - 0.5) * 0.35,
  });

  const draw = () => {
    context.clearRect(0, 0, canvas.width, canvas.height);
    context.fillStyle = "rgba(56, 189, 248, 0.75)";

    particles.forEach((p) => {
      p.x += p.vx;
      p.y += p.vy;

      if (p.x < 0 || p.x > canvas.width) {
        p.vx *= -1;
      }
      if (p.y < 0 || p.y > canvas.height) {
        p.vy *= -1;
      }

      context.beginPath();
      context.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      context.fill();
    });

    requestAnimationFrame(draw);
  };

  resize();
  window.addEventListener("resize", resize);

  for (let i = 0; i < particleCount; i += 1) {
    particles.push(spawnParticle());
  }

  draw();
})();
