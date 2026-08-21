/* Anime Epic Moments — favorites.js
   Кнопка «в избранное» на карточках аниме:
   делегирование кликов, POST/DELETE /favorites/, состояние в localStorage. */
(function () {
  "use strict";

  var STORAGE_PREFIX = "aem_fav_";

  function authUserId() {
    var meta = document.querySelector('meta[name="auth-user-id"]');
    return meta && meta.content ? meta.content : null;
  }

  function storageKey(userId) {
    return STORAGE_PREFIX + userId;
  }

  function loadIds(userId) {
    try {
      var raw = localStorage.getItem(storageKey(userId));
      return raw ? JSON.parse(raw) : [];
    } catch (e) {
      return [];
    }
  }

  function saveIds(userId, ids) {
    try {
      localStorage.setItem(storageKey(userId), JSON.stringify(ids));
    } catch (e) {
      /* приватный режим — игнорируем */
    }
  }

  function isFavorite(userId, animeId) {
    return loadIds(userId).indexOf(String(animeId)) !== -1;
  }

  function setFavorite(userId, animeId, value) {
    var ids = loadIds(userId);
    var key = String(animeId);
    var index = ids.indexOf(key);
    if (value && index === -1) {
      ids.push(key);
    } else if (!value && index !== -1) {
      ids.splice(index, 1);
    }
    saveIds(userId, ids);
  }

  function paint(btn, active) {
    btn.classList.toggle("active", active);
    btn.innerHTML = active ? "❤️" : "🤍";
    btn.title = active ? "Убрать из избранного" : "В избранное";
  }

  function initButtons() {
    var userId = authUserId();
    if (!userId) return;
    document.querySelectorAll(".fav-btn[data-fav-id]").forEach(function (btn) {
      paint(btn, isFavorite(userId, btn.dataset.favId));
    });
  }

  document.addEventListener("click", function (event) {
    var btn = event.target.closest(".fav-btn[data-fav-id]");
    if (!btn) return;
    event.preventDefault();
    event.stopPropagation();

    var userId = authUserId();
    if (!userId) {
      window.location.href = "/auth/login";
      return;
    }

    var animeId = btn.dataset.favId;
    var makeFavorite = !isFavorite(userId, animeId);

    AEM.api("/favorites/", {
      method: makeFavorite ? "POST" : "DELETE",
      body: { user_id: Number(userId), anime_id: Number(animeId) },
    })
      .then(function () {
        setFavorite(userId, animeId, makeFavorite);
        paint(btn, makeFavorite);
        AEM.toast(makeFavorite ? "Добавлено в избранное" : "Убрано из избранного", "success");
      })
      .catch(function (error) {
        AEM.toast("Не удалось: " + (error.message || "ошибка"), "error");
      });
  });

  document.addEventListener("DOMContentLoaded", initButtons);
})();
