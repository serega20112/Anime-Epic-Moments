/* Anime Epic Moments — index_recommendations.js
   Асинхронная подгрузка сезонных тайтлов и персональных рекомендаций
   на главную страницу (не блокирует первую отрисовку). */
(function () {
  "use strict";

  function renderCards(track, list) {
    if (!track) return;
    track.innerHTML = list
      .map(function (anime) {
        return AEM.animeCard(anime);
      })
      .join("");
    track.hidden = list.length === 0;
    if (list.length === 0) {
      var empty = document.createElement("div");
      empty.className = "empty-state";
      empty.innerHTML =
        '<span class="empty-emoji">🌫️</span><h3>Пока пусто</h3>' +
        "<p>Пока нет данных. Загляните позже — подборка обновится.</p>";
      track.parentNode.appendChild(empty);
    }
  }

  function loadSeason() {
    var cfg = window.AEMIndexPage || {};
    var track = document.getElementById("season-track");
    var loading = document.getElementById("season-loading");
    if (!track) return;
    var params = new URLSearchParams();
    if (cfg.year) params.set("year", cfg.year);
    if (cfg.season) params.set("season", cfg.season);
    params.set("limit", "12");
    fetch("/anime/api/season/popular?" + params.toString(), {
      credentials: "same-origin",
    })
      .then(function (response) {
        return response.json();
      })
      .then(function (list) {
        if (loading) loading.remove();
        renderCards(track, Array.isArray(list) ? list : []);
      })
      .catch(function () {
        if (loading) loading.remove();
        renderCards(track, []);
      });
  }

  function loadRecommendations() {
    var cfg = window.AEMIndexPage || {};
    var track = document.getElementById("recommendations-track");
    var loading = document.getElementById("recommendations-loading");
    if (!track || !cfg.userId) return;
    fetch("/api/v1/recommendations/generate/" + cfg.userId, {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "X-CSRF-Token": AEM.csrfToken(),
        Accept: "application/json",
      },
    })
      .then(function (response) {
        return response.json();
      })
      .then(function (list) {
        if (loading) loading.remove();
        renderCards(track, Array.isArray(list) ? list : []);
      })
      .catch(function () {
        if (loading) loading.remove();
        renderCards(track, []);
      });
  }

  function bindCarousels() {
    document.querySelectorAll("[data-carousel]").forEach(function (carousel) {
      var track = carousel.querySelector(".carousel-track");
      var prev = carousel.querySelector("[data-carousel-prev]");
      var next = carousel.querySelector("[data-carousel-next]");
      if (!track) return;
      var step = function (dir) {
        track.scrollBy({
          left: dir * Math.round(track.clientWidth * 0.8),
          behavior: "smooth",
        });
      };
      if (prev)
        prev.addEventListener("click", function () {
          step(-1);
        });
      if (next)
        next.addEventListener("click", function () {
          step(1);
        });
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    bindCarousels();
    loadSeason();
    loadRecommendations();
  });
})();
