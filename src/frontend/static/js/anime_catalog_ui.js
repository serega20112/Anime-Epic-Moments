/* Anime Epic Moments — anime_catalog_ui.js
   Логика каталога с фильтрами (жанр, формат, статус, рейтинг, сортировка)
   и переключением вида отображения (сетка / список). */
(function () {
  "use strict";

  var NO_COVER = "/static/images/no-cover.svg";
  var VIEW_KEY = "aem_catalog_view";
  var PAGE_SIZE = 30;
  var currentPage = 0;
  var currentList = [];
  var isLoading = false;

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

  function listCard(anime) {
    var id = anime.anime_id || anime.external_id || anime.id;
    var title = anime.title || "Без названия";
    var originalTitle = anime.original_title || "";
    var cover = anime.cover_url || anime.image_url || NO_COVER;
    var rating = anime.rating;
    var year = anime.year;
    var genres = anime.genres || [];
    var episodeCount = anime.episode_count;
    var meta = [];
    if (year) meta.push(year);
    if (episodeCount) meta.push(episodeCount + " серий");
    var genreText = genres.length ? genres.slice(0, 3).join(", ") : "";
    return (
      '<a class="anime-card anime-card-list" href="/watch/' +
      id +
      '">' +
      '<div class="poster">' +
      '<img src="' +
      cover +
      '" alt="' +
      AEM.escapeHtml(title) +
      '" loading="lazy" onerror="this.onerror=null;this.src=\'' +
      NO_COVER +
      "';\">" +
      (rating ? '<span class="rating-badge">★ ' + rating + "</span>" : "") +
      "</div>" +
      '<div class="card-body">' +
      '<div class="card-title">' +
      '<span class="card-title-ru">' + AEM.escapeHtml(title) + "</span>" +
      (originalTitle && originalTitle !== title
        ? '<span class="card-title-original">' + AEM.escapeHtml(originalTitle) + "</span>"
        : "") +
      "</div>" +
      (meta.length
        ? '<div class="card-meta">' +
          meta
            .map(function (m) {
              return "<span>" + AEM.escapeHtml(String(m)) + "</span>";
            })
            .join('<span class="dot"></span>') +
          "</div>"
        : "") +
      (genreText
        ? '<div class="card-genres">' + AEM.escapeHtml(genreText) + "</div>"
        : "") +
      '<span class="btn btn-primary btn-sm">Смотреть</span>' +
      "</div>" +
      "</a>"
    );
  }

  function renderResults(list) {
    var grid = document.getElementById("results-grid");
    var empty = document.getElementById("results-empty");
    var count = document.getElementById("results-count");
    var view = getView();
    grid.innerHTML = "";
    grid.classList.toggle("results-list", view === "list");
    list.forEach(function (anime) {
      grid.appendChild(
        elementFromHtml(view === "list" ? listCard(anime) : card(anime)),
      );
    });
    if (count) {
      count.textContent = list.length
        ? "Найдено: " +
          list.length +
          (list.length === 1 ? " тайтл" : " тайтлов")
        : "";
    }
    if (empty) empty.classList.toggle("hidden", list.length > 0);
    updateLoadMore();
  }

  function updateLoadMore() {
    var wrap = document.getElementById("load-more-wrap");
    if (!wrap) return;
    var hasMore = currentList.length > (currentPage + 1) * PAGE_SIZE;
    wrap.classList.toggle("hidden", !hasMore);
  }

  function setLoading(on) {
    isLoading = on;
    var loading = document.getElementById("results-loading");
    if (loading) loading.classList.toggle("hidden", !on);
    var loadMore = document.getElementById("load-more");
    if (loadMore) loadMore.disabled = on;
  }

  function collectState() {
    var activeChips = document.querySelectorAll(
      "#genre-chips .filter-chip.active, #demographic-chips .filter-chip.active",
    );
    var categories = [];
    Array.prototype.forEach.call(activeChips, function (chip) {
      var value = chip.getAttribute("data-value");
      if (value) categories.push(value);
    });
    var type = document.getElementById("filter-type");
    var status = document.getElementById("filter-status");
    var score = document.getElementById("filter-score");
    var sort = document.getElementById("filter-sort");
    var yearFrom = document.getElementById("filter-year-from");
    var yearTo = document.getElementById("filter-year-to");
    var hasDubEl = document.getElementById("filter-has-dub");
    return {
      genre: categories.join(","),
      type: type ? type.value : "",
      status: status ? status.value : "",
      min_score: score ? score.value : "",
      year_from: yearFrom ? yearFrom.value : "",
      year_to: yearTo ? yearTo.value : "",
      sort: sort ? sort.value : "rating",
      has_dub: hasDubEl && hasDubEl.checked ? "1" : "",
    };
  }

  function loadCatalog() {
    var state = collectState();
    var params = new URLSearchParams();
    params.set("limit", "100");
    params.set("order", "desc");
    [
      "genre",
      "type",
      "status",
      "min_score",
      "year_from",
      "year_to",
      "sort",
      "has_dub",
    ].forEach(function (name) {
      if (state[name]) params.set(name, state[name]);
    });
    setLoading(true);
    AEM.api("/anime/api/catalog?" + params.toString())
      .then(function (list) {
        setLoading(false);
        currentList = Array.isArray(list) ? list : [];
        currentPage = 0;
        renderResults(currentList.slice(0, PAGE_SIZE));
      })
      .catch(function () {
        setLoading(false);
        var empty = document.getElementById("results-empty");
        if (empty) empty.classList.remove("hidden");
        AEM.toast("Не удалось загрузить каталог. Попробуйте ещё раз.", "error");
      });
  }

  function loadMore() {
    if (isLoading) return;
    currentPage += 1;
    var grid = document.getElementById("results-grid");
    var view = getView();
    var slice = currentList.slice(0, (currentPage + 1) * PAGE_SIZE);
    grid.innerHTML = "";
    slice.forEach(function (anime) {
      grid.appendChild(
        elementFromHtml(view === "list" ? listCard(anime) : card(anime)),
      );
    });
    var count = document.getElementById("results-count");
    if (count) {
      count.textContent = slice.length
        ? "Найдено: " +
          slice.length +
          (slice.length === 1 ? " тайтл" : " тайтлов")
        : "";
    }
    updateLoadMore();
  }

  function bindGenreChips() {
    var chips = document.querySelectorAll(
      "#genre-chips .filter-chip, #demographic-chips .filter-chip",
    );
    var anyChip = document.querySelector(
      '#genre-chips .filter-chip[data-value=""]',
    );
    Array.prototype.forEach.call(chips, function (chip) {
      chip.addEventListener("click", function () {
        if (chip.getAttribute("data-value") === "") {
          Array.prototype.forEach.call(chips, function (other) {
            other.classList.toggle("active", other === chip);
          });
          return;
        }
        chip.classList.toggle("active");
        var anyActive = false;
        Array.prototype.forEach.call(chips, function (other) {
          if (
            other.getAttribute("data-value") !== "" &&
            other.classList.contains("active")
          ) {
            anyActive = true;
          }
        });
        if (anyChip) anyChip.classList.toggle("active", !anyActive);
      });
    });
  }

  function bindControls() {
    var apply = document.getElementById("filter-apply");
    var reset = document.getElementById("filter-reset");
    var loadMoreBtn = document.getElementById("load-more");
    var selects = [
      "filter-type",
      "filter-status",
      "filter-score",
      "filter-sort",
    ];
    if (apply) apply.addEventListener("click", loadCatalog);
    if (loadMoreBtn) loadMoreBtn.addEventListener("click", loadMore);
    selects.forEach(function (id) {
      var el = document.getElementById(id);
      if (el) el.addEventListener("change", loadCatalog);
    });
    var hasDubEl = document.getElementById("filter-has-dub");
    if (hasDubEl) hasDubEl.addEventListener("change", loadCatalog);
    if (reset) {
      reset.addEventListener("click", function () {
        var chips = document.querySelectorAll(
          "#genre-chips .filter-chip, #demographic-chips .filter-chip",
        );
        Array.prototype.forEach.call(chips, function (chip) {
          chip.classList.toggle(
            "active",
            chip.getAttribute("data-value") === "",
          );
        });
        selects.forEach(function (id) {
          var el = document.getElementById(id);
          if (el) el.value = "";
        });
        var sort = document.getElementById("filter-sort");
        if (sort) sort.value = "rating";
        var yearFrom = document.getElementById("filter-year-from");
        var yearTo = document.getElementById("filter-year-to");
        if (yearFrom) yearFrom.value = "";
        if (yearTo) yearTo.value = "";
        loadCatalog();
      });
    }
  }

  function getView() {
    try {
      return localStorage.getItem(VIEW_KEY) === "list" ? "list" : "grid";
    } catch (e) {
      return "grid";
    }
  }

  function setView(view) {
    try {
      localStorage.setItem(VIEW_KEY, view);
    } catch (e) {}
    var buttons = document.querySelectorAll(".view-toggle-btn");
    Array.prototype.forEach.call(buttons, function (btn) {
      btn.classList.toggle("active", btn.getAttribute("data-view") === view);
    });
    var grid = document.getElementById("results-grid");
    if (grid) grid.classList.toggle("results-list", view === "list");
  }

  function handleScroll() {
    if (isLoading) return;
    var wrap = document.getElementById("load-more-wrap");
    if (!wrap || wrap.classList.contains("hidden")) return;
    var scrollY = window.scrollY || window.pageYOffset;
    var innerHeight = window.innerHeight;
    var docHeight = document.documentElement.scrollHeight;
    if (docHeight - (scrollY + innerHeight) < 400) {
      loadMore();
    }
  }

  function bindViewToggle() {
    var buttons = document.querySelectorAll(".view-toggle-btn");
    Array.prototype.forEach.call(buttons, function (btn) {
      btn.addEventListener("click", function () {
        var view = btn.getAttribute("data-view") === "list" ? "list" : "grid";
        setView(view);
        var grid = document.getElementById("results-grid");
        if (grid && grid.children.length) {
          var list = Array.prototype.map.call(grid.children, function (child) {
            return child;
          });
          grid.innerHTML = "";
          list.forEach(function (child) {
            grid.appendChild(child);
          });
        }
      });
    });
  }

  function applyInitial() {
    var initial = (window.AEMCatalogPage || {}).initial || {};
    var selected = String(initial.genre || "")
      .split(",")
      .map(function (value) {
        return value.trim();
      });
    var chips = document.querySelectorAll(
      "#genre-chips .filter-chip, #demographic-chips .filter-chip",
    );
    Array.prototype.forEach.call(chips, function (chip) {
      var on = selected.indexOf(chip.getAttribute("data-value")) !== -1;
      chip.classList.toggle("active", on);
    });
    var map = {
      type: "filter-type",
      status: "filter-status",
      min_score: "filter-score",
      sort: "filter-sort",
      year_from: "filter-year-from",
      year_to: "filter-year-to",
    };
    Object.keys(map).forEach(function (key) {
      var el = document.getElementById(map[key]);
      if (el && initial[key]) el.value = initial[key];
    });
    var hasDubEl = document.getElementById("filter-has-dub");
    if (hasDubEl) {
      try {
        hasDubEl.checked = Boolean(initial.has_dub) && String(initial.has_dub) !== "";
      } catch (e) {
        hasDubEl.checked = false;
      }
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    var grid = document.getElementById("results-grid");
    if (!grid) return;
    bindGenreChips();
    bindControls();
    bindViewToggle();
    applyInitial();
    setView(getView());
    window.addEventListener("scroll", handleScroll);
    loadCatalog();
  });
})();
