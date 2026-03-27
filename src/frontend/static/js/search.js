(function () {
  const form = document.getElementById("description-search-form");
  const results = document.getElementById("results");
  const resultsMeta = document.getElementById("results-meta");
  const ratingInput = document.getElementById("rating");
  const ratingValue = document.getElementById("rating-value");
  const resetButton = document.getElementById("reset-filters");

  if (!form || !results) {
    return;
  }

  const syncRangeLabels = () => {
    if (ratingInput && ratingValue) {
      ratingValue.textContent = ratingInput.value;
    }
  };

  syncRangeLabels();
  if (ratingInput) {
    ratingInput.addEventListener("input", syncRangeLabels);
  }

  if (resetButton) {
    resetButton.addEventListener("click", () => {
      setTimeout(syncRangeLabels, 0);
      if (resultsMeta) {
        resultsMeta.textContent = "Фильтры сброшены";
      }
    });
  }

  const renderResults = (items) => {
    if (!items.length) {
      results.innerHTML = `
                <p>Ничего не найдено. Попробуйте уточнить описание или ослабить фильтры.</p>
                <a class="btn neon-pink" href="/anime/search">Добавь вручную</a>
            `;
      return;
    }

    if (
      window.AEMAnimeUI &&
      typeof window.AEMAnimeUI.renderAnimeCards === "function"
    ) {
      window.AEMAnimeUI.renderAnimeCards(results, items);
      return;
    }

    results.innerHTML = "";
  };

  const buildParamsFromForm = (formData, adultConfirmed) => {
    const params = new URLSearchParams();
    params.set("description", String(formData.get("description") || "").trim());
    params.set("limit", "18");

    const yearFrom = String(formData.get("year_from") || "");
    const yearTo = String(formData.get("year_to") || "");
    const rating = String(formData.get("rating") || "");
    const ageRating = String(formData.get("age_rating") || "");
    const sort = String(formData.get("sort") || "");
    const genreHint = String(formData.get("genre_hint") || "").trim();

    if (yearFrom) params.set("year_from", yearFrom);
    if (yearTo) params.set("year_to", yearTo);
    if (rating) params.set("rating", rating);
    if (ageRating) params.set("age_rating", ageRating);
    params.set("adult_confirmed", adultConfirmed ? "1" : "0");
    if (sort) params.set("sort", sort);
    if (genreHint) params.set("genre_hint", genreHint);
    return params;
  };

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(form);
    const description = String(formData.get("description") || "").trim();
    if (!description) {
      return;
    }

    results.innerHTML = "<p>Ищем подходящее аниме...</p>";

    const ageRating = String(formData.get("age_rating") || "");
    let adultConfirmed = false;

    if (ageRating === "18+") {
      const confirmed = window.confirm(
        "Показать 18+ контент? Подтвердите, что вам есть 18 лет.",
      );
      if (!confirmed) {
        if (resultsMeta) {
          resultsMeta.textContent = "Показ 18+ отменён";
        }
        results.innerHTML =
          "<p>Поиск 18+ отменён. Выберите другой возрастной рейтинг.</p>";
        return;
      }
      adultConfirmed = true;
    }

    let params = buildParamsFromForm(formData, adultConfirmed);
    let response = await fetch(
      `/anime/api/search/description?${params.toString()}`,
    );
    if (!response.ok) {
      results.innerHTML = "<p>Ошибка поиска. Попробуйте позже.</p>";
      if (resultsMeta) {
        resultsMeta.textContent = "Не удалось получить результаты";
      }
      return;
    }

    let payload = await response.json();
    if (!Array.isArray(payload) && payload.requires_age_confirmation) {
      const confirmed = window.confirm(
        payload.message || "Подтвердите, что вам есть 18 лет.",
      );
      if (!confirmed) {
        if (resultsMeta) {
          resultsMeta.textContent = "Показ 18+ отменён";
        }
        results.innerHTML =
          "<p>Контент 18+ скрыт до подтверждения возраста.</p>";
        return;
      }
      params = buildParamsFromForm(formData, true);
      response = await fetch(
        `/anime/api/search/description?${params.toString()}`,
      );
      if (!response.ok) {
        results.innerHTML = "<p>Ошибка поиска. Попробуйте позже.</p>";
        if (resultsMeta) {
          resultsMeta.textContent = "Не удалось получить результаты";
        }
        return;
      }
      payload = await response.json();
    }

    const items = Array.isArray(payload) ? payload : payload.items || [];
    if (resultsMeta) {
      resultsMeta.textContent = `Найдено: ${items.length}`;
    }
    renderResults(items);
  });
})();
