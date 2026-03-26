(function () {
    const storageKey = "aem_theme";

    const applyTheme = (theme) => {
        document.documentElement.setAttribute("data-theme", theme);
    };

    const savedTheme = localStorage.getItem(storageKey);
    if (savedTheme) {
        applyTheme(savedTheme);
    }

    const menuItems = Array.from(document.querySelectorAll(".dropdown-menu a"));
    const themeLink = menuItems.find((item) => item.textContent.trim() === "Тема");
    if (!themeLink) {
        return;
    }

    themeLink.addEventListener("click", (event) => {
        event.preventDefault();
        const currentTheme = document.documentElement.getAttribute("data-theme");
        const nextTheme = currentTheme === "light" ? "dark" : "light";
        applyTheme(nextTheme);
        localStorage.setItem(storageKey, nextTheme);
    });
}());
