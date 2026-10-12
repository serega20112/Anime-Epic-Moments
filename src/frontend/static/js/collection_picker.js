/* Anime Epic Moments — collection_picker.js
   Кнопка «в коллекцию» на страницах аниме: загружает список коллекций
   пользователя (GET /collections/api/mine), показывает модалку-пикер
   и добавляет тайтл в выбранную коллекцию (POST /collections/{id}/items). */
(function () {
  "use strict";

  var modal = null;

  function authUserId() {
    var meta = document.querySelector('meta[name="auth-user-id"]');
    return meta && meta.content ? meta.content : null;
  }

  function ensureModal() {
    if (modal) return modal;
    modal = document.createElement("div");
    modal.className = "modal-overlay";
    modal.id = "collection-picker-modal";
    modal.innerHTML =
      '<div class="modal" role="dialog" aria-modal="true">' +
      '<div class="modal-header">' +
      "<h3>Добавить в коллекцию</h3>" +
      '<button class="modal-close" data-picker-close aria-label="Закрыть">&times;</button>' +
      "</div>" +
      '<div class="modal-body" data-picker-list></div>' +
      '<div class="modal-footer">' +
      '<a class="btn btn-ghost btn-sm" href="/collections">Создать новую</a>' +
      '<button type="button" class="btn btn-ghost" data-picker-close>Закрыть</button>' +
      "</div>" +
      "</div>";
    document.body.appendChild(modal);
    modal.addEventListener("click", function (event) {
      if (event.target === modal || event.target.closest("[data-picker-close]")) {
        close();
      }
    });
    return modal;
  }

  function open() {
    ensureModal().classList.add("open");
  }

  function close() {
    if (modal) modal.classList.remove("open");
  }

  function renderList(listNode, collections, animeId) {
    listNode.innerHTML = "";
    if (!collections.length) {
      listNode.innerHTML =
        '<p class="muted">Коллекций пока нет. Создайте первую на странице «Коллекции».</p>';
      return;
    }
    collections.forEach(function (collection) {
      var button = document.createElement("button");
      button.type = "button";
      button.className = "btn btn-ghost btn-sm picker-collection-btn";
      button.style.width = "100%";
      button.style.justifyContent = "space-between";
      button.style.marginBottom = "8px";
      button.innerHTML =
        "<span>" + AEM.escapeHtml(collection.title) + "</span><span>＋</span>";
      button.addEventListener("click", function () {
        addToCollection(collection, animeId);
      });
      listNode.appendChild(button);
    });
  }

  function addToCollection(collection, animeId) {
    AEM.api("/collections/" + collection.id + "/items", {
      method: "POST",
      body: { anime_id: Number(animeId) },
    })
      .then(function () {
        close();
        AEM.toast("Добавлено в «" + collection.title + "»", "success");
      })
      .catch(function (error) {
        AEM.toast("Не удалось: " + (error.message || "ошибка"), "error");
      });
  }

  function loadCollections(animeId) {
    var listNode = ensureModal().querySelector("[data-picker-list]");
    listNode.innerHTML = '<p class="muted">Загрузка…</p>';
    AEM.api("/collections/api/mine")
      .then(function (data) {
        renderList(listNode, (data && data.collections) || [], animeId);
      })
      .catch(function () {
        listNode.innerHTML = '<p class="muted">Не удалось загрузить коллекции.</p>';
      });
  }

  document.addEventListener("click", function (event) {
    var button = event.target.closest(".add-to-collection-btn[data-anime-id]");
    if (!button) return;
    event.preventDefault();
    event.stopPropagation();

    if (!authUserId()) {
      window.location.href = "/auth/login";
      return;
    }
    open();
    loadCollections(button.dataset.animeId);
  });
})();