/* Anime Epic Moments — filter_modal.js
   Кнопка «фильтры» (3 полоски) рядом с поиском в шапке:
   открывает модалку с жанрами и фильтрами в стиле Anixart,
   «Показать» ведёт на /anime/catalog с выбранными параметрами. */
(function () {
  "use strict";

  var GENRES = [
    ["", "Любой"],
    ["Action", "Экшен"],
    ["Adventure", "Приключения"],
    ["Comedy", "Комедия"],
    ["Drama", "Драма"],
    ["Fantasy", "Фэнтези"],
    ["Horror", "Ужасы"],
    ["Mystery", "Детектив"],
    ["Psychological", "Психологическое"],
    ["Romance", "Романтика"],
    ["Sci-Fi", "Фантастика"],
    ["Slice of Life", "Повседневность"],
    ["Sports", "Спорт"],
    ["Supernatural", "Сверхъестественное"],
    ["Thriller", "Триллер"],
    ["Mecha", "Меха"],
    ["School", "Школа"],
    ["Ecchi", "Этти"],
    ["Hentai", "Хентай"],
  ];

  var DEMOGRAPHICS = [
    ["Shounen", "Сёнэн"],
    ["Shoujo", "Сёдзё"],
    ["Seinen", "Сэйнэн"],
    ["Josei", "Дзёсэй"],
    ["Kids", "Кодомо"],
  ];

  function chip(value, label) {
    return (
      '<button type="button" class="filter-chip fm-chip' +
      '" data-value="' + window.AEM.escapeHtml(value) + '">' +
      window.AEM.escapeHtml(label) +
      "</button>"
    );
  }

  function chipGroup(values, extraClass) {
    return values
      .map(function (pair) {
        return chip(pair[0], pair[1]);
      })
      .join("");
  }

  function selectField(id, label, options, selected) {
    var opts = options
      .map(function (pair) {
        var on = (pair[0] || "") === (selected || "") ? " selected" : "";
        return '<option value="' + window.AEM.escapeHtml(pair[0]) + '"' + on + ">" +
          window.AEM.escapeHtml(pair[1]) + "</option>";
      })
      .join("");
    return (
      '<div class="filter-field">' +
      '<span class="filter-label">' + window.AEM.escapeHtml(label) + "</span>" +
      '<select id="' + id + '" class="filter-select">' + opts + "</select>" +
      "</div>"
    );
  }

  function currentParams() {
    return new URLSearchParams(window.location.search);
  }

  function buildBody(initial) {
    return (
      '<div class="fm-filters">' +
        '<div class="filter-group">' +
          '<span class="filter-label">Жанр</span>' +
          '<div class="filter-chips" id="fm-genre-chips">' + chipGroup(GENRES) + "</div>" +
        "</div>" +
        '<div class="filter-group">' +
          '<span class="filter-label">Аудитория</span>' +
          '<div class="filter-chips" id="fm-demographic-chips">' + chipGroup(DEMOGRAPHICS) + "</div>" +
        "</div>" +
        '<div class="filter-row">' +
          selectField("fm-type", "Формат", [
            ["", "Любой"],
            ["tv", "ТВ-сериал"],
            ["movie", "Фильм"],
            ["ova", "OVA"],
            ["ona", "ONA"],
            ["special", "Спецвыпуск"],
          ], initial.get("type")) +
          selectField("fm-status", "Статус", [
            ["", "Любой"],
            ["airing", "Онгоинг"],
            ["complete", "Завершено"],
            ["upcoming", "Анонс"],
          ], initial.get("status")) +
          selectField("fm-score", "Рейтинг", [
            ["", "Любой"],
            ["9", "9+"],
            ["8", "8+"],
            ["7", "7+"],
            ["6", "6+"],
          ], initial.get("min_score")) +
          selectField("fm-sort", "Сортировка", [
            ["rating", "По рейтингу"],
            ["popularity", "По популярности"],
            ["newest", "По новизне"],
            ["title", "По алфавиту"],
          ], initial.get("sort") || "rating") +
        "</div>" +
        '<div class="filter-row">' +
          '<div class="filter-field">' +
            '<span class="filter-label">Год от</span>' +
            '<input type="number" id="fm-year-from" class="filter-select" min="1950" max="2100" placeholder="1960" value="' +
              window.AEM.escapeHtml(initial.get("year_from") || "") + '">' +
          "</div>" +
          '<div class="filter-field">' +
            '<span class="filter-label">Год до</span>' +
            '<input type="number" id="fm-year-to" class="filter-select" min="1950" max="2100" placeholder="2026" value="' +
              window.AEM.escapeHtml(initial.get("year_to") || "") + '">' +
          "</div>" +
        "</div>" +
        '<div class="fm-actions">' +
          '<button type="button" class="btn btn-ghost" id="fm-reset">Сбросить</button>' +
          '<button type="button" class="btn btn-primary" id="fm-apply">Показать</button>' +
        "</div>" +
      "</div>"
  );
  }

  function markActiveChips(root, values) {
    var chips = root.querySelectorAll(".fm-chip");
    Array.prototype.forEach.call(chips, function (chipEl) {
      chipEl.classList.toggle("active", values.indexOf(chipEl.getAttribute("data-value")) !== -1);
    });
  }

  function selectedCategories(root) {
    var values = [];
    Array.prototype.forEach.call(root.querySelectorAll(".fm-chip.active"), function (chipEl) {
      var value = chipEl.getAttribute("data-value");
      if (value) values.push(value);
    });
    return values;
  }

  function openModal() {
    var initial = currentParams();
    var body = buildBody(initial);
    window.AEM.openModal("Фильтры аниме", body);
    var overlay = document.getElementById("modal-overlay");
    if (!overlay) return;

    var initialCategories = String(initial.get("genre") || "")
      .split(",")
      .map(function (value) {
        return value.trim();
      });
    markActiveChips(overlay, initialCategories);

    var chips = overlay.querySelectorAll(".fm-chip");
    var anyChip = overlay.querySelector('.fm-chip[data-value=""]');
    Array.prototype.forEach.call(chips, function (chipEl) {
      chipEl.addEventListener("click", function () {
        if (chipEl.getAttribute("data-value") === "") {
          markActiveChips(overlay, [""]);
          return;
        }
        chipEl.classList.toggle("active");
        var anyActive = selectedCategories(overlay).length > 0;
        if (anyChip) anyChip.classList.toggle("active", !anyActive);
      });
    });

    var apply = document.getElementById("fm-apply");
    var reset = document.getElementById("fm-reset");
    if (apply) {
      apply.addEventListener("click", function () {
        var params = new URLSearchParams();
        params.set("limit", "30");
        params.set("order", "desc");
        var categories = selectedCategories(overlay);
        if (categories.length) params.set("genre", categories.join(","));
        [
          ["type", "fm-type"],
          ["status", "fm-status"],
          ["min_score", "fm-score"],
          ["sort", "fm-sort"],
          ["year_from", "fm-year-from"],
          ["year_to", "fm-year-to"],
        ].forEach(function (pair) {
          var el = document.getElementById(pair[1]);
          var value = el && el.value ? String(el.value).trim() : "";
          if (value) params.set(pair[0], value);
        });
        window.AEM.closeModal();
        window.location.href = "/anime/catalog?" + params.toString();
      });
    }
    if (reset) {
      reset.addEventListener("click", function () {
        markActiveChips(overlay, [""]);
        ["fm-type", "fm-status", "fm-score"].forEach(function (id) {
          var el = document.getElementById(id);
          if (el) el.value = "";
        });
        var sort = document.getElementById("fm-sort");
        if (sort) sort.value = "rating";
        var from = document.getElementById("fm-year-from");
        var to = document.getElementById("fm-year-to");
        if (from) from.value = "";
        if (to) to.value = "";
      });
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    var btn = document.getElementById("search-filter-btn");
    if (!btn) return;
    btn.addEventListener("click", openModal);
  });
})();
