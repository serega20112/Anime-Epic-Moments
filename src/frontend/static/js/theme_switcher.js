/* Anime Epic Moments — theme_switcher.js
   Переключение тем (neon → dark → light → rose), сохранение в localStorage. */
(function () {
  "use strict";

  var STORAGE_KEY = "aem_theme";
  var LABELS = {
    neon: "Неон",
    dark: "Тёмная",
    light: "Светлая",
    rose: "Сакура",
  };

  function getSaved() {
    try {
      return localStorage.getItem(STORAGE_KEY);
    } catch (e) {
      return null;
    }
  }

  function save(theme) {
    try {
      localStorage.setItem(STORAGE_KEY, theme);
    } catch (e) {
      /* localStorage недоступен — живём без сохранения */
    }
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    var label = document.getElementById("theme-fab-label");
    if (label) label.textContent = "Тема: " + (LABELS[theme] || theme);
    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) {
      var css = getComputedStyle(document.documentElement);
      meta.setAttribute(
        "content",
        css.getPropertyValue("--color-background").trim(),
      );
    }
    document.dispatchEvent(
      new CustomEvent("aem:themechange", { detail: { theme: theme } }),
    );
  }

  function nextTheme(current) {
    var keys = ["neon", "dark", "light", "rose"];
    var index = keys.indexOf(current);
    return keys[(index + 1) % keys.length];
  }

  document.addEventListener("DOMContentLoaded", function () {
    var saved = getSaved();
    var current =
      saved || document.documentElement.getAttribute("data-theme") || "neon";
    if (keysIndexOf(current) === -1) current = "neon";
    applyTheme(current);

    var fab = document.getElementById("theme-fab");
    if (fab) {
      fab.addEventListener("click", function () {
        var next = nextTheme(current);
        current = next;
        save(next);
        applyTheme(next);
      });
    }
  });

  function keysIndexOf(theme) {
    return ["neon", "dark", "light", "rose"].indexOf(theme);
  }
})();
