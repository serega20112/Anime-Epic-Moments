/* Anime Epic Moments — anime_search_ui.js
   Логика страниц поиска: по названию и по описанию (с age-gate). */
(function () {
  "use strict";

  var NO_COVER = "/static/images/no-cover.svg";
  var adultConfirmed = false;

  function findPage() {
    if (document.getElementById("title-search-form")) return "title";
    if (document.getElementById("description-search-form"))
      return "description";
    return null;
  }

  /* ---------- карточка результата ---------- */
  function resultCard(anime) {
    var wrap = document.createElement("div");
    wrap.className = "age-wrapper";
    wrap.appendChild(
      elementFromHtml(
        AEM.animeCard(anime, {
          watchUrl:
            "/watch/" + (anime.anime_id || anime.external_id || anime.id),
        }),
      ),
    );
    if (anime.requires_age_confirmation) {
      var overlay = document.createElement("div");
      overlay.className = "age-overlay";
      overlay.innerHTML =
        '<span class="age-emoji">🔞</span>' +
        "<p>Этот тайтл может содержать материалы 18+. Покажите, что вы совершеннолетний.</p>";
      wrap.appendChild(overlay);
    }
    return wrap;
  }

  function elementFromHtml(html) {
    var template = document.createElement("template");
    template.innerHTML = html.trim();
    return template.content.firstChild;
  }

  function renderResults(list) {
    var grid = document.getElementById("results-grid");
    var empty = document.getElementById("results-empty");
    var count = document.getElementById("results-count");
    grid.innerHTML = "";
    list.forEach(function (anime) {
      grid.appendChild(resultCard(anime));
    });
    if (count) {
      count.textContent = list.length
        ? "Найдено: " +
          list.length +
          (list.length === 1 ? " тайтл" : " тайтлов")
        : "";
    }
    if (empty) empty.classList.toggle("hidden", list.length > 0);
  }

  function setLoading(on) {
    var loading = document.getElementById("results-loading");
    if (loading) loading.classList.toggle("hidden", !on);
  }

  /* ---------- поиск по названию ---------- */
  function initTitleSearch() {
    var form = document.getElementById("title-search-form");
    var grid = document.getElementById("results-grid");
    if (!form || !grid) return;
    var input = document.getElementById("search-input");
    var hints = document.querySelectorAll("[data-hint]");

    form.addEventListener("submit", function (event) {
      event.preventDefault();
      runTitleSearch(input.value.trim());
    });

    Array.prototype.forEach.call(hints, function (hint) {
      hint.addEventListener("click", function () {
        input.value = hint.getAttribute("data-hint");
        runTitleSearch(input.value);
      });
    });

    /* Авто-запуск только когда пришли с запросом из шапки (?title=):
       это уже «нажатая кнопка отправки». При прямом переходе на страницу
       результаты не показываем, пока не нажата кнопка «Найти». */
    var initial = (window.AEMAnimeSearchPage || {}).initialTitle || "";
    if (initial) runTitleSearch(initial);
  }

  function runTitleSearch(title) {
    var empty = document.getElementById("results-empty");
    if (!title) {
      if (empty) empty.classList.remove("hidden");
      return;
    }
    setLoading(true);
    AEM.api(
      "/anime/api/search?title=" + encodeURIComponent(title) + "&limit=10",
    )
      .then(function (list) {
        setLoading(false);
        renderResults(Array.isArray(list) ? list : []);
      })
      .catch(function () {
        setLoading(false);
        if (empty) empty.classList.remove("hidden");
      });
  }

  /* ---------- поиск по описанию ---------- */
  function initDescriptionSearch() {
    var form = document.getElementById("description-search-form");
    if (!form) return;
    var hints = document.querySelectorAll("[data-desc-hint]");
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      runDescriptionSearch();
    });
    Array.prototype.forEach.call(hints, function (hint) {
      hint.addEventListener("click", function () {
        var input = document.getElementById("description-input");
        input.value = hint.getAttribute("data-desc-hint");
        runDescriptionSearch();
      });
    });

    bindAgeModal();
  }

  function runDescriptionSearch() {
    var input = document.getElementById("description-input");
    var description = input.value.trim();
    if (!description) return;
    var form = document.getElementById("description-search-form");
    var params = new URLSearchParams();
    params.set("description", description);
    params.set("limit", "10");
    [
      "genre_hint",
      "sort",
      "year_from",
      "year_to",
      "rating",
      "age_rating",
    ].forEach(function (name) {
      var el = form.querySelector('[name="' + name + '"]');
      var value = el ? el.value.trim() : "";
      if (name === "sort" && !value) value = "match";
      if (value) params.set(name, value);
    });
    if (adultConfirmed) params.set("adult_confirmed", "1");

    setLoading(true);
    AEM.api("/anime/api/search/description?" + params.toString())
      .then(function (result) {
        setLoading(false);
        var items = Array.isArray(result.items) ? result.items : [];
        if (result && result.requires_age_confirmation && !adultConfirmed) {
          showAgeModal(result.message || "");
          return;
        }
        if (result && result.message && items.length) {
          AEM.toast(result.message, "info");
        }
        renderResults(items);
      })
      .catch(function () {
        setLoading(false);
        AEM.toast("Не удалось выполнить поиск. Попробуйте ещё раз.", "error");
      });
  }

  /* ---------- age-gate ---------- */
  function bindAgeModal() {
    var overlay = document.getElementById("age-modal");
    if (!overlay) return;
    var close = document.getElementById("age-modal-close");
    var cancel = document.getElementById("age-cancel");
    var confirmBtn = document.getElementById("age-confirm");
    close.addEventListener("click", hideAgeModal);
    cancel.addEventListener("click", hideAgeModal);
    overlay.addEventListener("click", function (event) {
      if (event.target === overlay) hideAgeModal();
    });
    confirmBtn.addEventListener("click", function () {
      adultConfirmed = true;
      hideAgeModal();
      runDescriptionSearch();
    });
  }

  function showAgeModal(message) {
    var overlay = document.getElementById("age-modal");
    var body = document.getElementById("age-modal-body");
    if (!overlay) return;
    body.textContent =
      message ||
      "Часть результатов может содержать контент для взрослых. Подтвердите, что вам есть 18 лет.";
    overlay.classList.add("open");
  }

  function hideAgeModal() {
    var overlay = document.getElementById("age-modal");
    if (overlay) overlay.classList.remove("open");
  }

  document.addEventListener("DOMContentLoaded", function () {
    if (findPage() === "title") initTitleSearch();
    else if (findPage() === "description") initDescriptionSearch();
  });
})();
