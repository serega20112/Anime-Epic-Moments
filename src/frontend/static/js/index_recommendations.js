(function () {
  const root = document.getElementById("index-recommendation-grid");
  const popularRoot = document.getElementById("index-popular-grid");
  const config = window.AEMIndexPage || {};
  const userId = String(config.currentUserId || root?.dataset.userId || "").trim();

  const escapeHtml = (value) =>
    String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");

  const truncate = (value, limit) => {
    const text = String(value || "").trim();
    if (text.length <= limit) {
      return text;
    }
    return `${text.slice(0, limit - 1).trimEnd()}…`;
  };

  const buildCard = (rec) => {
    const genres = Array.isArray(rec.genres) ? rec.genres.slice(0, 3) : [];
    const similarity = Number(rec.similarity_score);
    const similarityLabel = Number.isFinite(similarity)
      ? similarity.toFixed(2)
      : "match";

    return `
      <article class="result-card index-result-card">
        <img
          src="${escapeHtml(rec.image_url || "/static/images/no-cover.png")}"
          alt="${escapeHtml(rec.title || "Recommendation")}"
          loading="lazy"
        />
        <div class="result-card-body">
          <h3>${escapeHtml(rec.title || "Неизвестное аниме")}</h3>
          <p>${escapeHtml(truncate(rec.description || "Описание недоступно", 240))}</p>
          ${
            genres.length
              ? `<div class="result-genres">${genres
                  .map((genre) => `<span class="genre-chip">${escapeHtml(genre)}</span>`)
                  .join("")}</div>`
              : ""
          }
          <div class="result-meta">
            <span>${escapeHtml(rec.reason || "Подобрано по твоему профилю")}</span>
            <span>${escapeHtml(similarityLabel)}</span>
          </div>
          <div class="result-actions">
            <button
              class="btn-favorite recommendation-favorite-button"
              data-anime-id="${escapeHtml(rec.anime_id)}"
              data-title="${escapeHtml(rec.title || "")}"
              data-description="${escapeHtml(rec.description || "")}"
              data-cover-url="${escapeHtml(rec.image_url || "")}"
              data-genres='${escapeHtml(JSON.stringify(rec.genres || []))}'
            >
              Добавить в избранное
            </button>
            <a class="btn neon-blue btn-watch" href="${escapeHtml(rec.watch_url || "#")}">Где смотреть</a>
          </div>
        </div>
      </article>
    `;
  };

  const bindFavoriteButtons = () => {
    root.querySelectorAll(".recommendation-favorite-button").forEach((button) => {
      button.addEventListener("click", async () => {
        const response = await fetch("/favorites/", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            user_id: userId,
            anime_id: button.dataset.animeId,
            title: button.dataset.title || "",
            description: button.dataset.description || "",
            cover_url: button.dataset.coverUrl || "",
            genres: JSON.parse(button.dataset.genres || "[]"),
          }),
        });
        if (!response.ok) {
          window.alert("Не удалось добавить аниме в избранное.");
          return;
        }
        button.textContent = "В избранном";
        button.classList.add("is-added");
      });
    });
  };

  const renderEmptyState = (title, text) => {
    root.innerHTML = `
      <section class="empty-state index-recommendation-state">
        <h2>${escapeHtml(title)}</h2>
        <p>${escapeHtml(text)}</p>
      </section>
    `;
  };

  const loadRecommendations = async () => {
    if (!root || !userId) {
      return;
    }
    try {
      const response = await fetch(`/api/v1/recommendations/generate/${userId}`, {
        method: "POST",
        headers: { Accept: "application/json" },
      });
      if (!response.ok) {
        throw new Error(`http_${response.status}`);
      }
      const payload = await response.json();
      if (!Array.isArray(payload) || !payload.length) {
        renderEmptyState(
          "Пока мало данных для рекомендаций",
          "Добавь избранное или хайлайты, чтобы подборка стала точнее.",
        );
        return;
      }
      root.innerHTML = payload.map(buildCard).join("");
      bindFavoriteButtons();
    } catch (_error) {
      renderEmptyState(
        "Рекомендации пока недоступны",
        "Главная уже работает. Подборку можно обновить позже, когда внешние источники ответят быстрее.",
      );
    }
  };

  const buildPopularCard = (anime) => `
    <div class="anime-card">
      <img
        src="${escapeHtml(anime.cover_url || "/static/images/no-cover.png")}"
        alt="${escapeHtml(anime.title || "Anime")}"
        loading="lazy"
      />
      <h3>${escapeHtml(anime.title || "Неизвестное аниме")}</h3>
      <a class="btn-watch" href="/watch/${escapeHtml(anime.external_id || 0)}?episode=1">Где смотреть</a>
    </div>
  `;

  const loadPopularAnime = async () => {
    if (!popularRoot) {
      return;
    }
    const season = String(config.season || popularRoot.dataset.season || "").trim();
    const year = String(config.year || popularRoot.dataset.year || "").trim();
    if (!season || !year) {
      return;
    }
    try {
      const response = await fetch(
        `/anime/api/season/popular?season=${encodeURIComponent(season)}&year=${encodeURIComponent(year)}&limit=12`,
        { headers: { Accept: "application/json" } },
      );
      if (!response.ok) {
        throw new Error(`http_${response.status}`);
      }
      const payload = await response.json();
      if (!Array.isArray(payload) || !payload.length) {
        popularRoot.innerHTML = `
          <section class="empty-state index-recommendation-state">
            <h2>Сезонные тайтлы пока недоступны</h2>
            <p>Внешний источник не ответил вовремя. Попробуй обновить страницу позже.</p>
          </section>
        `;
        return;
      }
      popularRoot.innerHTML = payload.map(buildPopularCard).join("");
    } catch (_error) {
      popularRoot.innerHTML = `
        <section class="empty-state index-recommendation-state">
          <h2>Сезонные тайтлы пока недоступны</h2>
          <p>Главная уже открыта. Подборка сезона догрузится позже, когда API ответит быстрее.</p>
        </section>
      `;
    }
  };

  loadRecommendations();
  loadPopularAnime();
})();
