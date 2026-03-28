(function () {
  const container = document.getElementById("particles-js");
  if (!container) {
    return;
  }

  const canvas = document.createElement("canvas");
  const context = canvas.getContext("2d");
  container.appendChild(canvas);

  const particles = [];
  const particleCount = 28;

  const readParticleColor = () =>
    getComputedStyle(document.documentElement)
      .getPropertyValue("--particle-color")
      .trim() || "rgba(148, 163, 184, 0.16)";

  const resize = () => {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  };

  const spawnParticle = () => ({
    x: Math.random() * canvas.width,
    y: Math.random() * canvas.height,
    r: 1 + Math.random() * 2.2,
    vx: (Math.random() - 0.5) * 0.18,
    vy: (Math.random() - 0.5) * 0.18,
  });

  const draw = () => {
    context.clearRect(0, 0, canvas.width, canvas.height);
    context.fillStyle = readParticleColor();

    particles.forEach((particle) => {
      particle.x += particle.vx;
      particle.y += particle.vy;

      if (particle.x < 0 || particle.x > canvas.width) {
        particle.vx *= -1;
      }
      if (particle.y < 0 || particle.y > canvas.height) {
        particle.vy *= -1;
      }

      context.beginPath();
      context.arc(particle.x, particle.y, particle.r, 0, Math.PI * 2);
      context.fill();
    });

    requestAnimationFrame(draw);
  };

  resize();
  window.addEventListener("resize", resize);

  for (let index = 0; index < particleCount; index += 1) {
    particles.push(spawnParticle());
  }

  draw();
})();
