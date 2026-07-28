(function () {
  const root = document.querySelector("[data-ai-recommendations]");
  if (!root) {
    return;
  }

  const form = root.querySelector(".profile-ai-form");
  const resultsNode = root.querySelector(".profile-ai-results");
  const userId = root.getAttribute("data-user-id");

  const renderItems = (items) => {
    if (!items.length) {
      resultsNode.innerHTML =
        '<section class="empty-state"><h2>Пока пусто</h2><p>AI не нашел достаточно близких тайтлов под этот запрос.</p></section>';
      return;
    }
    resultsNode.innerHTML = items
      .map(
        (item) => `
          <article class="profile-ai-card">
            <div class="profile-ai-card-body">
              <div class="profile-ai-card-head">
                <h3>${item.title}</h3>
                <span>${(item.similarity_score || 0).toFixed(2)}</span>
              </div>
              <p>${item.reason || ""}</p>
              <div class="profile-tag-cloud">
                ${(item.genres || [])
                  .slice(0, 3)
                  .map((genre) => `<span class="profile-tag">${genre}</span>`)
                  .join("")}
              </div>
              <div class="result-actions">
                <a class="btn neon-blue btn-watch" href="${item.watch_url}">Открыть</a>
              </div>
            </div>
          </article>
        `,
      )
      .join("");
  };

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const query = (new FormData(form).get("query") || "").toString().trim();
    if (!query || !userId) {
      return;
    }
    resultsNode.innerHTML =
      '<section class="empty-state"><h2>AI думает</h2><p>Собираю подборку под твой запрос.</p></section>';
    const response = await fetch(`/api/v1/recommendations/ask/${userId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, limit: 6 }),
    });
    if (!response.ok) {
      resultsNode.innerHTML =
        '<section class="empty-state"><h2>Сбой</h2><p>Не удалось получить AI-рекомендации. Попробуй еще раз.</p></section>';
      return;
    }
    const items = await response.json();
    renderItems(Array.isArray(items) ? items : []);
  });
})();
