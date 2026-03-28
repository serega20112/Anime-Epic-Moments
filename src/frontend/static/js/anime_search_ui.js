(function () {
  const AUTOCOMPLETE_DELAY = 220;

  const debounce = (callback, delay) => {
    let timeoutId = null;
    return (...args) => {
      window.clearTimeout(timeoutId);
      timeoutId = window.setTimeout(() => callback(...args), delay);
    };
  };

  const truncate = (value, maxLength) => {
    const text = String(value || "")
      .replace(/\s+/g, " ")
      .trim();
    if (text.length <= maxLength) {
      return text;
    }
    return `${text.slice(0, maxLength - 1)}…`;
  };

  const escapeHtml = (value) =>
    String(value || "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");

  const buildWatchUrl = (title, externalId) => {
    const numericId = Number(externalId);
    if (Number.isInteger(numericId) && numericId > 0) {
      return `/watch/${numericId}?episode=1`;
    }
    return `https://www.google.com/search?q=${encodeURIComponent(`where to watch ${title} anime`)}`;
  };

  const getCurrentUserId = () => document.body.dataset.currentUserId || "";

  const addFavorite = async (anime, button) => {
    const userId = getCurrentUserId();
    if (!userId) {
      window.location.href = "/auth/login";
      return;
    }

    const animeId = Number(anime && anime.external_id);
    if (!Number.isInteger(animeId) || animeId <= 0) {
      window.alert("Это аниме пока нельзя сохранить в избранное.");
      return;
    }

    const response = await fetch("/favorites/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: userId,
        anime_id: animeId,
        title: anime.title || "",
        description: anime.description || "",
        cover_url: anime.cover_url || "",
        genres: Array.isArray(anime.genres) ? anime.genres : [],
      }),
    });

    if (!response.ok) {
      window.alert("Не удалось добавить в избранное.");
      return;
    }

    button.classList.add("is-added");
    button.textContent = "В избранном";
  };

  const buildAnimeCard = (anime) => {
    const genres = Array.isArray(anime.genres) ? anime.genres.slice(0, 3) : [];
    const coverUrl = anime.cover_url || "/static/images/no-cover.png";
    const watchUrl =
      anime.watch_url || buildWatchUrl(anime.title, anime.external_id);
    const canFavorite =
      Number.isInteger(Number(anime.external_id)) &&
      Number(anime.external_id) > 0;

    return `
            <article class="result-card">
                <img src="${escapeHtml(coverUrl)}" alt="${escapeHtml(anime.title)}" loading="lazy">
                <div class="result-card-body">
                    <h3>${escapeHtml(anime.title)}</h3>
                    <p>${escapeHtml(truncate(anime.description || "Описание недоступно", 220))}</p>
                    <div class="result-genres">
                        ${genres.map((genre) => `<span class="genre-chip">${escapeHtml(genre)}</span>`).join("")}
                    </div>
                    <div class="result-meta">
                        <span>Рейтинг: ${escapeHtml(anime.rating ?? "?")}</span>
                        <span>Год: ${escapeHtml(anime.year ?? "?")}</span>
                    </div>
                    <div class="result-actions">
                        ${canFavorite ? `<button class="btn-favorite" data-anime-id="${escapeHtml(anime.external_id)}">В избранное</button>` : ""}
                        <a class="btn neon-blue btn-watch" href="${escapeHtml(watchUrl)}" target="_blank" rel="noopener noreferrer">Где смотреть</a>
                    </div>
                </div>
            </article>
        `;
  };

  const renderAnimeCards = (container, items) => {
    container.innerHTML = items.map(buildAnimeCard).join("");
    const animeById = new Map(
      items.map((anime) => [String(anime.external_id || ""), anime]),
    );
    container.querySelectorAll(".btn-favorite").forEach((button) => {
      button.addEventListener("click", () => {
        const anime = animeById.get(String(button.dataset.animeId || ""));
        if (!anime) {
          window.alert("Не удалось определить аниме для избранного.");
          return;
        }
        addFavorite(anime, button);
      });
    });
  };

  const renderAutocomplete = (container, items) => {
    if (!items.length) {
      container.hidden = true;
      container.innerHTML = "";
      return;
    }

    container.innerHTML = items
      .map(
        (anime) => `
            <a class="autocomplete-item" href="/anime/search?title=${encodeURIComponent(anime.title)}">
                <img src="${escapeHtml(anime.cover_url || "/static/images/no-cover.png")}" alt="${escapeHtml(anime.title)}" loading="lazy">
                <div>
                    <strong>${escapeHtml(anime.title)}</strong>
                    <span>${escapeHtml((anime.genres || []).slice(0, 3).join(" • ") || "Без жанров")}</span>
                </div>
            </a>
        `,
      )
      .join("");
    container.hidden = false;
  };

  const setupGlobalSearchForms = () => {
    document.querySelectorAll(".global-search-form").forEach((form) => {
      const input = form.querySelector(".global-search-input");
      const autocomplete = form.querySelector(".search-autocomplete");
      if (!input || !autocomplete) {
        return;
      }

      const loadSuggestions = debounce(async () => {
        const query = input.value.trim();
        if (query.length < 2) {
          renderAutocomplete(autocomplete, []);
          return;
        }
        const response = await fetch(
          `/anime/api/autocomplete?query=${encodeURIComponent(query)}&limit=6`,
        );
        if (!response.ok) {
          renderAutocomplete(autocomplete, []);
          return;
        }
        const items = await response.json();
        renderAutocomplete(autocomplete, Array.isArray(items) ? items : []);
      }, AUTOCOMPLETE_DELAY);

      input.addEventListener("input", loadSuggestions);
      input.addEventListener("focus", loadSuggestions);
      document.addEventListener("click", (event) => {
        if (!form.contains(event.target)) {
          autocomplete.hidden = true;
        }
      });
    });
  };

  const setupTitleSearchPage = () => {
    const resultsContainer = document.getElementById("title-search-results");
    const resultsMeta = document.getElementById("title-results-meta");
    const form = document.querySelector(".global-search-form");
    const input = form ? form.querySelector(".global-search-input") : null;
    if (!resultsContainer || !form || !input) {
      return;
    }

    const loadResults = async (title) => {
      const query = String(title || "").trim();
      if (!query) {
        resultsContainer.innerHTML = "";
        if (resultsMeta) {
          resultsMeta.textContent = "Введи название или выбери подсказку";
        }
        return;
      }

      resultsContainer.innerHTML = "<p>Ищем аниме...</p>";
      const response = await fetch(
        `/anime/api/search?title=${encodeURIComponent(query)}&limit=18`,
      );
      if (!response.ok) {
        resultsContainer.innerHTML = "<p>Не удалось загрузить результаты.</p>";
        return;
      }

      const apiItems = await response.json();
      const mergedItems = Array.isArray(apiItems) ? apiItems : [];

      if (resultsMeta) {
        resultsMeta.textContent = `Найдено: ${mergedItems.length}`;
      }

      if (!mergedItems.length) {
        resultsContainer.innerHTML = "<p>Ничего не найдено по названию.</p>";
        return;
      }

      renderAnimeCards(resultsContainer, mergedItems);
    };

    form.addEventListener("submit", (event) => {
      event.preventDefault();
      const query = input.value.trim();
      const url = new URL(window.location.href);
      if (query) {
        url.searchParams.set("title", query);
      } else {
        url.searchParams.delete("title");
      }
      window.history.replaceState({}, "", url.toString());
      loadResults(query);
    });

    const initialTitle =
      new URLSearchParams(window.location.search).get("title") ||
      input.value.trim();
    if (initialTitle) {
      input.value = initialTitle;
      loadResults(initialTitle);
    }
  };

  window.AEMAnimeUI = {
    addFavorite,
    renderAnimeCards,
    buildWatchUrl,
  };

  setupGlobalSearchForms();
  setupTitleSearchPage();
})();
