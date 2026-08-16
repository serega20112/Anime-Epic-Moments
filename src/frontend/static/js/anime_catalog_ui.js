/* Anime Epic Moments — anime_catalog_ui.js
   Логика каталога с фильтрами (жанр, формат, статус, рейтинг, сортировка). */
(function () {
  "use strict";

  var NO_COVER = "/static/images/no-cover.svg";

  function elementFromHtml(html) {
    var template = document.createElement("template");
    template.innerHTML = html.trim();
    return template.content.firstChild;
  }

  function card(anime) {
    return AEM.animeCard(anime, {
      watchUrl: "/watch/" + (anime.anime_id || anime.external_id || anime.id),
    });
  }

  function renderResults(list) {
    var grid = document.getElementById("results-grid");
    var empty = document.getElementById("results-empty");
    var count = document.getElementById("results-count");
    grid.innerHTML = "";
    list.forEach(function (anime) {
      grid.appendChild(elementFromHtml(card(anime)));
    });
    if (count) {
      count.textContent = list.length
        ? "Найдено: " + list.length + (list.length === 1 ? " тайтл" : " тайтлов")
        : "";
    }
    if (empty) empty.classList.toggle("hidden", list.length > 0);
  }

  function setLoading(on) {
    var loading = document.getElementById("results-loading");
    if (loading) loading.classList.toggle("hidden", !on);
  }

  function collectState() {
    var genreChip = document.querySelector("#genre-chips .filter-chip.active");
    var type = document.getElementById("filter-type");
    var status = document.getElementById("filter-status");
    var score = document.getElementById("filter-score");
    var sort = document.getElementById("filter-sort");
    return {
      genre: genreChip ? genreChip.getAttribute("data-value") : "",
      type: type ? type.value : "",
      status: status ? status.value : "",
      min_score: score ? score.value : "",
      sort: sort ? sort.value : "rating",
    };
  }

  function loadCatalog() {
    var state = collectState();
    var params = new URLSearchParams();
    params.set("limit", "30");
    params.set("order", "desc");
    ["genre", "type", "status", "min_score", "sort"].forEach(function (name) {
      if (state[name]) params.set(name, state[name]);
    });
    setLoading(true);
    AEM.api("/anime/api/catalog?" + params.toString())
      .then(function (list) {
        setLoading(false);
        renderResults(Array.isArray(list) ? list : []);
      })
      .catch(function () {
        setLoading(false);
        var empty = document.getElementById("results-empty");
        if (empty) empty.classList.remove("hidden");
        AEM.toast("Не удалось загрузить каталог. Попробуйте ещё раз.", "error");
      });
  }

  function bindGenreChips() {
    var chips = document.querySelectorAll("#genre-chips .filter-chip");
    Array.prototype.forEach.call(chips, function (chip) {
      chip.addEventListener("click", function () {
        Array.prototype.forEach.call(chips, function (other) {
          other.classList.toggle("active", other === chip);
        });
      });
    });
  }

  function bindControls() {
    var apply = document.getElementById("filter-apply");
    var reset = document.getElementById("filter-reset");
    var selects = ["filter-type", "filter-status", "filter-score", "filter-sort"];
    if (apply) apply.addEventListener("click", loadCatalog);
    selects.forEach(function (id) {
      var el = document.getElementById(id);
      if (el) el.addEventListener("change", loadCatalog);
    });
    if (reset) {
      reset.addEventListener("click", function () {
        var chips = document.querySelectorAll("#genre-chips .filter-chip");
        Array.prototype.forEach.call(chips, function (chip) {
          chip.classList.toggle("active", chip.getAttribute("data-value") === "");
        });
        selects.forEach(function (id) {
          var el = document.getElementById(id);
          if (el) el.value = "";
        });
        var sort = document.getElementById("filter-sort");
        if (sort) sort.value = "rating";
        loadCatalog();
      });
    }
  }

  function applyInitial() {
    var initial = (window.AEMCatalogPage || {}).initial || {};
    var chips = document.querySelectorAll("#genre-chips .filter-chip");
    Array.prototype.forEach.call(chips, function (chip) {
      var on = chip.getAttribute("data-value") === (initial.genre || "");
      chip.classList.toggle("active", on);
    });
    var map = { type: "filter-type", status: "filter-status" };
    Object.keys(map).forEach(function (key) {
      var el = document.getElementById(map[key]);
      if (el && initial[key]) el.value = initial[key];
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    var grid = document.getElementById("results-grid");
    if (!grid) return;
    bindGenreChips();
    bindControls();
    applyInitial();
    loadCatalog();
  });
})();