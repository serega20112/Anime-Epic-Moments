(function () {
  const storageKey = "aem_theme";
  const themes = ["neon", "dark", "light", "rose"];
  const labels = {
    neon: "Неон",
    dark: "Тёмная",
    light: "Светлая",
    rose: "Сакура",
  };
  const icons = {
    neon: "✦",
    dark: "◐",
    light: "☼",
    rose: "✿",
  };

  let toggleButton = null;

  const normalizeTheme = (theme) => {
    if (!theme || !themes.includes(theme)) {
      return "neon";
    }
    return theme;
  };

  const currentTheme = () =>
    normalizeTheme(document.documentElement.getAttribute("data-theme"));

  const updateButton = (theme) => {
    if (!toggleButton) {
      return;
    }
    toggleButton.setAttribute("aria-label", `Переключить тему. Сейчас: ${labels[theme]}`);
    const labelNode = toggleButton.querySelector(".theme-toggle-label");
    const valueNode = toggleButton.querySelector(".theme-toggle-value");
    const iconNode = toggleButton.querySelector(".theme-toggle-icon");
    if (labelNode) {
      labelNode.textContent = "Тема";
    }
    if (valueNode) {
      valueNode.textContent = labels[theme];
    }
    if (iconNode) {
      iconNode.textContent = icons[theme];
    }
  };

  const syncThemeFields = (theme) => {
    document
      .querySelectorAll("input[data-theme-field]")
      .forEach((field) => {
        field.value = theme;
      });
  };

  const applyTheme = (theme) => {
    const normalized = normalizeTheme(theme);
    document.documentElement.setAttribute("data-theme", normalized);
    updateButton(normalized);
    syncThemeFields(normalized);
  };

  const cycleTheme = () => {
    const theme = currentTheme();
    const nextIndex = (themes.indexOf(theme) + 1) % themes.length;
    const nextTheme = themes[nextIndex];
    applyTheme(nextTheme);
    localStorage.setItem(storageKey, nextTheme);
  };

  const ensureToggleButton = () => {
    toggleButton = document.querySelector("[data-theme-toggle]");
    if (!toggleButton) {
      toggleButton = document.createElement("button");
      toggleButton.type = "button";
      toggleButton.className = "theme-toggle";
      toggleButton.setAttribute("data-theme-toggle", "1");
      toggleButton.innerHTML =
        '<span class="theme-toggle-icon" aria-hidden="true"></span>' +
        '<span class="theme-toggle-label"></span>' +
        '<span class="theme-toggle-value"></span>';
      document.body.appendChild(toggleButton);
    }
    if (toggleButton.dataset.themeBound !== "1") {
      toggleButton.dataset.themeBound = "1";
      toggleButton.addEventListener("click", cycleTheme);
    }
    updateButton(currentTheme());
  };

  const savedTheme = normalizeTheme(localStorage.getItem(storageKey));
  applyTheme(savedTheme);

  const init = () => {
    ensureToggleButton();
    syncThemeFields(currentTheme());
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
