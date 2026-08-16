/* Anime Epic Moments — password_strength.js
   Индикатор надёжности пароля для форм регистрации и сброса. */
(function () {
  "use strict";

  function strength(password) {
    var score = 0;
    if (!password) return 0;
    if (password.length >= 8) score += 1;
    if (password.length >= 12) score += 1;
    if (/[A-ZА-ЯЁ]/.test(password) && /[a-zа-яё]/.test(password)) score += 1;
    if (/\d/.test(password)) score += 1;
    if (/[^A-Za-zА-Яа-яЁё0-9]/.test(password)) score += 1;
    return Math.min(score, 4);
  }

  var LABELS = ["", "Слабый", "Нормальный", "Хороший", "Крепкий", "Отличный"];
  var COLORS = ["", "#fb7185", "#fbbf24", "#38bdf8", "#34d399", "#34d399"];

  function init() {
    var inputs = document.querySelectorAll(
      '#password, form input[type="password"]:first-of-type'
    );
    Array.prototype.forEach.call(inputs, function (input) {
      var group = input.closest(".form-group");
      if (!group) return;
      var bars = group.querySelectorAll(".pw-bar");
      var label = group.querySelector(".pw-label");
      if (!bars.length && !label) return;

      input.addEventListener("input", function () {
        var score = strength(input.value);
        var idx = score; /* 0..4 */
        Array.prototype.forEach.call(bars, function (bar, i) {
          var filled = i < idx;
          bar.classList.toggle("filled", filled);
          bar.style.setProperty("--pw-color", COLORS[idx] || "");
        });
        if (label) label.textContent = LABELS[idx] || "";
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();