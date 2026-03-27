(function () {
  const input = document.getElementById("password");
  const text = document.getElementById("strength-text");

  if (!input || !text) {
    return;
  }

  const evaluate = (value) => {
    let score = 0;
    if (value.length >= 8) score += 1;
    if (/[A-Z]/.test(value)) score += 1;
    if (/[0-9]/.test(value)) score += 1;
    if (/[^A-Za-z0-9]/.test(value)) score += 1;
    return score;
  };

  input.addEventListener("input", () => {
    const score = evaluate(input.value);
    if (score <= 1) {
      text.textContent = "Слабый";
      return;
    }
    if (score <= 3) {
      text.textContent = "Средний";
      return;
    }
    text.textContent = "Сильный";
  });
})();
