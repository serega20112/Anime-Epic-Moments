/* Anime Epic Moments — favorites.js
   Кнопка «в избранное» на карточках аниме:
   делегирование кликов, POST/DELETE /favorites/, отрисовка состояния
   с сервера (GET /favorites/ids/{user_id}), localStorage — только кэш. */
(function () {
  "use strict";

  var STORAGE_PREFIX = "aem_fav_";
  var refreshTimer = null;

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
      return;
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
    var unchanged =
      btn.dataset.favPainted === "1" &&
      btn.classList.contains("active") === active;
    if (unchanged) return;
    btn.dataset.favPainted = "1";
    btn.classList.toggle("active", active);
    btn.innerHTML = active ? "❤️" : "🤍";
    btn.title = active ? "Убрать из избранного" : "В избранное";
  }

  function paintAll(buttons, userId) {
    Array.prototype.forEach.call(buttons, function (btn) {
      paint(btn, isFavorite(userId, btn.dataset.favId));
    });
  }

  function initButtons() {
    var userId = authUserId();
    if (!userId) return;
    var buttons = document.querySelectorAll(".fav-btn[data-fav-id]");
    if (!buttons.length) return;

    paintAll(buttons, userId);
    AEM.api("/favorites/ids/" + encodeURIComponent(userId))
      .then(function (data) {
        var ids = ((data && data.anime_ids) || []).map(String);
        saveIds(userId, ids);
        Array.prototype.forEach.call(buttons, function (btn) {
          paint(btn, ids.indexOf(String(btn.dataset.favId)) !== -1);
        });
      })
      .catch(function () {});
  }

  function scheduleInit() {
    if (refreshTimer) clearTimeout(refreshTimer);
    refreshTimer = setTimeout(initButtons, 150);
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
        AEM.toast(
          makeFavorite ? "Добавлено в избранное" : "Убрано из избранного",
          "success",
        );
      })
      .catch(function (error) {
        AEM.toast("Не удалось: " + (error.message || "ошибка"), "error");
      });
  });

  document.addEventListener("DOMContentLoaded", function () {
    initButtons();
    if (typeof MutationObserver === "function") {
      var observer = new MutationObserver(function (mutations) {
        for (var i = 0; i < mutations.length; i++) {
          var added = mutations[i].addedNodes;
          for (var j = 0; j < added.length; j++) {
            var node = added[j];
            if (
              node.nodeType === 1 &&
              (node.matches(".fav-btn[data-fav-id]") ||
                node.querySelector(".fav-btn[data-fav-id]"))
            ) {
              scheduleInit();
              return;
            }
          }
        }
      });
      observer.observe(document.body, { childList: true, subtree: true });
    }
  });
})();
