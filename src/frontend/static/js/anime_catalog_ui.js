/* Anime Epic Moments — anime_catalog_ui.js
   Каталог с пагинацией, мультивыбором жанров и фильтром по озвучке.

   Фильтры живут в обычной GET-форме, поэтому состояние всегда
   воспроизводится из адресной строки и страницу можно переслать ссылкой.
   Скрипт перехватывает отправку, чтобы не перезагружать страницу, и
   синхронизирует адресную строку через History API. */
(function () {
  "use strict";

  var NO_COVER = "/static/images/no-cover.svg";
  var VIEW_KEY = "aem_catalog_view";
  var PAGE_WINDOW = 2;
  var FACET_LIMIT = 60;

  var form = document.getElementById("catalog-filters");
  var grid = document.getElementById("results-grid");
  var emptyState = document.getElementById("results-empty");
  var countLabel = document.getElementById("results-count");
  var loadingState = document.getElementById("results-loading");
  var pagination = document.getElementById("pagination");
  var pageNumbers = document.getElementById("page-numbers");
  var genreMenu = document.getElementById("genre-menu");
  var genreMenuEmpty = document.getElementById("genre-menu-empty");
  var genreTrigger = document.getElementById("genre-trigger");
  var genreTriggerLabel = document.getElementById("genre-trigger-label");
  var genreChosen = document.getElementById("genre-chosen");

  var state = {
    genres: [],
    genreMode: "all",
    type: "",
    status: "",
    minScore: "",
    yearFrom: "",
    yearTo: "",
    sort: "rating",
    hasDub: false,
    page: 1,
    perPage: 25,
    totalPages: 1,
    total: 0,
  };
  var knownGenres = [];
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
    var meta = [];
    if (anime.year) meta.push(anime.year);
    if (anime.episode_count) meta.push(anime.episode_count + " серий");
    var genreText = (anime.genres || []).slice(0, 3).join(", ");

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
      (anime.rating
        ? '<span class="rating-badge">★ ' + anime.rating + "</span>"
        : "") +
      "</div>" +
      '<div class="card-body">' +
      '<div class="card-title">' +
      '<span class="card-title-ru">' +
      AEM.escapeHtml(title) +
      "</span>" +
      (originalTitle && originalTitle !== title
        ? '<span class="card-title-original">' +
          AEM.escapeHtml(originalTitle) +
          "</span>"
        : "") +
      "</div>" +
      (meta.length
        ? '<div class="card-meta">' +
          meta
            .map(function (item) {
              return "<span>" + AEM.escapeHtml(String(item)) + "</span>";
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

  function renderResults(items) {
    var view = getView();
    grid.innerHTML = "";
    grid.classList.toggle("results-list", view === "list");
    items.forEach(function (anime) {
      grid.appendChild(
        elementFromHtml(view === "list" ? listCard(anime) : card(anime)),
      );
    });
    if (emptyState) emptyState.classList.toggle("hidden", items.length > 0);
  }

  function pluralizePages(total) {
    if (!total) return "";
    return total + " " + (total === 1 ? "страница" : "страниц");
  }

  function renderCount(payload) {
    if (!countLabel) return;
    var total = payload.total || 0;
    if (!total) {
      countLabel.textContent = "";
      return;
    }
    var suffix = payload.total_is_exact ? "" : "+";
    countLabel.textContent =
      "Найдено: " + total + suffix + " · " + pluralizePages(payload.total_pages);
  }

  function renderPagination(payload) {
    if (!pagination || !pageNumbers) return;
    var totalPages = payload.total_pages || 1;
    state.totalPages = totalPages;
    state.total = payload.total || 0;

    pagination.classList.toggle("hidden", totalPages <= 1);
    pageNumbers.innerHTML = "";

    if (totalPages <= 1) return;

    var current = payload.page || 1;
    setDisabled("page-first", current <= 1);
    setDisabled("page-prev", current <= 1);
    setDisabled("page-next", current >= totalPages);
    setDisabled("page-last", current >= totalPages);

    buildPageList(current, totalPages);
  }

  function buildPageList(current, totalPages) {
    var start = Math.max(1, current - PAGE_WINDOW);
    var end = Math.min(totalPages, current + PAGE_WINDOW);

    if (start > 1) {
      appendPageButton(1, current);
      if (start > 2) appendPageGap();
    }
    for (var index = start; index <= end; index += 1) {
      appendPageButton(index, current);
    }
    if (end < totalPages) {
      if (end < totalPages - 1) appendPageGap();
      appendPageButton(totalPages, current);
    }
  }

  function appendPageGap() {
    var gap = document.createElement("span");
    gap.className = "page-gap";
    gap.textContent = "…";
    pageNumbers.appendChild(gap);
  }

  function appendPageButton(number, current) {
    var button = document.createElement("button");
    button.type = "button";
    button.className = "page-number";
    button.textContent = String(number);
    button.setAttribute("aria-label", "Страница " + number);
    if (number === current) {
      button.classList.add("active");
      button.setAttribute("aria-current", "page");
    } else {
      button.addEventListener("click", function () {
        goToPage(number);
      });
    }
    pageNumbers.appendChild(button);
  }

  function setDisabled(id, disabled) {
    var button = document.getElementById(id);
    if (button) button.disabled = disabled;
  }

  function setLoading(on) {
    isLoading = on;
    if (loadingState) loadingState.classList.toggle("hidden", !on);
  }

  function readForm() {
    return {
      genres: state.genres.slice(),
      genreMode: readGenreMode(),
      type: valueOf("filter-type"),
      status: valueOf("filter-status"),
      minScore: valueOf("filter-score"),
      yearFrom: valueOf("filter-year-from"),
      yearTo: valueOf("filter-year-to"),
      sort: valueOf("filter-sort") || "rating",
      hasDub: isDubChecked(),
      page: 1,
      perPage: Number(valueOf("filter-per-page")) || 25,
    };
  }

  function valueOf(id) {
    var node = document.getElementById(id);
    return node ? String(node.value || "").trim() : "";
  }

  function isDubChecked() {
    var node = document.getElementById("filter-has-dub");
    return Boolean(node && node.checked);
  }

  function readGenreMode() {
    var checked = document.querySelector(
      'input[name="genre_mode"]:checked',
    );
    return checked ? checked.value : "all";
  }

  function buildParams() {
    var params = new URLSearchParams();
    state.genres.forEach(function (genre) {
      params.append("genre", genre);
    });
    if (state.genreMode === "any") params.set("genre_mode", "any");
    ["type", "status", "min_score", "year_from", "year_to", "sort"].forEach(
      function (key) {
        var source = {
          type: state.type,
          status: state.status,
          min_score: state.minScore,
          year_from: state.yearFrom,
          year_to: state.yearTo,
          sort: state.sort,
        }[key];
        if (source) params.set(key, source);
      },
    );
    if (state.hasDub) params.set("has_dub", "1");
    if (state.page > 1) params.set("page", String(state.page));
    params.set("per_page", String(state.perPage));
    return params;
  }

  function syncUrl() {
    var query = buildParams().toString();
    window.history.replaceState({}, "", window.location.pathname + "?" + query);
  }

  function loadCatalog() {
    setLoading(true);
    AEM.api("/anime/api/catalog?" + buildParams().toString())
      .then(function (payload) {
        setLoading(false);
        if (!payload || typeof payload !== "object") {
          renderResults([]);
          renderCount({});
          renderPagination({ page: 1, total_pages: 1, total: 0 });
          return;
        }
        state.page = payload.page || 1;
        state.perPage = payload.per_page || state.perPage;
        renderResults(payload.items || []);
        renderCount(payload);
        renderPagination(payload);
        updateGenres(payload.genre_facets || []);
        syncUrl();
      })
      .catch(function () {
        setLoading(false);
        if (emptyState) emptyState.classList.remove("hidden");
        AEM.toast("Не удалось загрузить каталог. Попробуйте ещё раз.", "error");
      });
  }

  function goToPage(page) {
    var target = Math.min(Math.max(1, page), state.totalPages);
    if (target === state.page) return;
    state.page = target;
    syncUrl();
    loadCatalog();
    var section = document.getElementById("results-grid");
    if (section) {
      var top = section.getBoundingClientRect().top + window.pageYOffset - 90;
      window.scrollTo({ top: top, behavior: "smooth" });
    }
  }

  function updateGenres(facets) {
    var counts = {};
    facets.forEach(function (facet) {
      counts[facet.name] = facet.count;
    });

    var names = [];
    state.genres.forEach(function (genre) {
      names.push({ name: genre, count: counts[genre] || null, chosen: true });
    });
    facets.slice(0, FACET_LIMIT).forEach(function (facet) {
      if (names.some(function (item) { return item.name === facet.name; })) return;
      names.push({ name: facet.name, count: facet.count, chosen: false });
    });

    knownGenres = names;
    renderGenreMenu(names);
    renderChosenChips();
  }

  function renderGenreMenu(names) {
    if (!genreMenu) return;
    genreMenu.innerHTML = "";

    if (!names.length) {
      var empty = document.createElement("p");
      empty.className = "genre-picker-empty";
      empty.textContent = "Жанры появятся после загрузки каталога";
      genreMenu.appendChild(empty);
      return;
    }

    names.forEach(function (item) {
      var option = document.createElement("button");
      option.type = "button";
      option.className = "genre-option";
      option.setAttribute("role", "option");
      option.setAttribute("data-value", item.name);
      option.setAttribute("aria-selected", item.chosen ? "true" : "false");
      option.classList.toggle("is-active", item.chosen);

      var box = document.createElement("span");
      box.className = "genre-option-box";
      box.textContent = item.chosen ? "✓" : "";
      option.appendChild(box);

      var label = document.createElement("span");
      label.className = "genre-option-label";
      label.textContent = item.name;
      option.appendChild(label);

      if (typeof item.count === "number") {
        var counter = document.createElement("span");
        counter.className = "genre-option-count";
        counter.textContent = String(item.count);
        option.appendChild(counter);
      }

      genreMenu.appendChild(option);
    });
  }

  function renderChosenChips() {
    if (!genreChosen || !genreTriggerLabel) return;

    genreChosen.innerHTML = "";
    if (!state.genres.length) {
      genreTriggerLabel.textContent = "Любые жанры";
      return;
    }
    genreTriggerLabel.textContent =
      state.genres.length === 1
        ? state.genres[0]
        : "Выбрано: " + state.genres.length;

    state.genres.forEach(function (genre) {
      var chip = document.createElement("button");
      chip.type = "button";
      chip.className = "genre-chip";
      chip.setAttribute("data-value", genre);
      chip.setAttribute("title", "Убрать " + genre);
      chip.textContent = genre + " ×";
      chip.addEventListener("click", function () {
        toggleGenre(genre);
      });
      genreChosen.appendChild(chip);
    });
  }

  function toggleGenre(genre) {
    var index = state.genres.indexOf(genre);
    if (index === -1) state.genres.push(genre);
    else state.genres.splice(index, 1);

    renderGenreMenu(knownGenres);
    renderChosenChips();
    state.page = 1;
    loadCatalog();
  }

  function openGenreMenu() {
    if (!genreMenu || !genreTrigger) return;
    genreMenu.classList.remove("hidden");
    genreTrigger.setAttribute("aria-expanded", "true");
  }

  function closeGenreMenu() {
    if (!genreMenu || !genreTrigger) return;
    genreMenu.classList.add("hidden");
    genreTrigger.setAttribute("aria-expanded", "false");
  }

  function toggleGenreMenu() {
    if (genreMenu && genreMenu.classList.contains("hidden")) openGenreMenu();
    else closeGenreMenu();
  }

  function bindGenres() {
    if (genreTrigger) {
      genreTrigger.addEventListener("click", function (event) {
        event.preventDefault();
        toggleGenreMenu();
      });
    }
    if (genreMenu) {
      genreMenu.addEventListener("click", function (event) {
        var option = event.target.closest(".genre-option");
        if (!option) return;
        event.preventDefault();
        toggleGenre(option.getAttribute("data-value"));
      });
    }
    document.addEventListener("click", function (event) {
      if (!genreMenu || genreMenu.classList.contains("hidden")) return;
      if (event.target.closest("#genre-picker")) return;
      closeGenreMenu();
    });

    Array.prototype.forEach.call(
      document.querySelectorAll('input[name="genre_mode"]'),
      function (radio) {
        radio.addEventListener("change", function () {
          if (state.genreMode !== radio.value && radio.checked) {
            state.genreMode = radio.value;
            state.page = 1;
            loadCatalog();
          }
        });
      },
    );
  }

  function bindPagination() {
    var bindings = [
      ["page-first", function () { return 1; }],
      ["page-prev", function () { return state.page - 1; }],
      ["page-next", function () { return state.page + 1; }],
      ["page-last", function () { return state.totalPages; }],
    ];
    bindings.forEach(function (binding) {
      var button = document.getElementById(binding[0]);
      if (!button) return;
      button.addEventListener("click", function () {
        goToPage(binding[1]());
      });
    });
  }

  function bindForm() {
    if (!form) return;
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      var next = readForm();
      state.genres = next.genres;
      state.genreMode = next.genreMode;
      state.type = next.type;
      state.status = next.status;
      state.minScore = next.minScore;
      state.yearFrom = next.yearFrom;
      state.yearTo = next.yearTo;
      state.sort = next.sort;
      state.hasDub = next.hasDub;
      state.perPage = next.perPage;
      state.page = 1;
      closeGenreMenu();
      loadCatalog();
    });

    var reset = document.getElementById("filter-reset");
    if (reset) {
      reset.addEventListener("click", function () {
        state.genres = [];
        state.genreMode = "all";
        state.page = 1;
        form.reset();
        var allMode = document.querySelector(
          'input[name="genre_mode"][value="all"]',
        );
        if (allMode) allMode.checked = true;
        var sortField = document.getElementById("filter-sort");
        if (sortField) sortField.value = "rating";
        renderChosenChips();
        renderGenreMenu(knownGenres);
        loadCatalog();
      });
    }
  }

  function getView() {
    try {
      return localStorage.getItem(VIEW_KEY) === "list" ? "list" : "grid";
    } catch (error) {
      return "grid";
    }
  }

  function setView(view) {
    try {
      localStorage.setItem(VIEW_KEY, view);
    } catch (error) {
      /* localStorage is unavailable in private mode */
    }
    Array.prototype.forEach.call(
      document.querySelectorAll(".view-toggle-btn"),
      function (button) {
        button.classList.toggle(
          "active",
          button.getAttribute("data-view") === view,
        );
      },
    );
    if (grid) grid.classList.toggle("results-list", view === "list");
  }

  function bindViewToggle() {
    Array.prototype.forEach.call(
      document.querySelectorAll(".view-toggle-btn"),
      function (button) {
        button.addEventListener("click", function () {
          var view = button.getAttribute("data-view") === "list" ? "list" : "grid";
          setView(view);
          if (!grid || !grid.children.length) return;
          var children = Array.prototype.slice.call(grid.children);
          grid.innerHTML = "";
          children.forEach(function (child) {
            grid.appendChild(child);
          });
        });
      },
    );
  }

  function applyInitial(initial) {
    state.genres = (initial.genres || []).filter(Boolean);
    state.genreMode = initial.genre_mode === "any" ? "any" : "all";
    state.page = Math.max(1, parseInt(initial.page, 10) || 1);
    state.perPage = parseInt(initial.per_page, 10) || 25;

    var fields = {
      type: "filter-type",
      status: "filter-status",
      min_score: "filter-score",
      year_from: "filter-year-from",
      year_to: "filter-year-to",
      sort: "filter-sort",
      per_page: "filter-per-page",
    };
    Object.keys(fields).forEach(function (key) {
      var node = document.getElementById(fields[key]);
      if (node && initial[key]) node.value = initial[key];
    });

    var dubField = document.getElementById("filter-has-dub");
    if (dubField) dubField.checked = initial.has_dub === "1" || initial.has_dub === "true";

    var modeField = document.querySelector(
      'input[name="genre_mode"][value="' + state.genreMode + '"]',
    );
    if (modeField) modeField.checked = true;

    renderChosenChips();
  }

  function bindPopState() {
    window.addEventListener("popstate", function () {
      var params = new URLSearchParams(window.location.search);
      applyInitial({
        genres: params.getAll("genre"),
        genre_mode: params.get("genre_mode"),
        page: params.get("page"),
        per_page: params.get("per_page"),
        type: params.get("type"),
        status: params.get("status"),
        min_score: params.get("min_score"),
        year_from: params.get("year_from"),
        year_to: params.get("year_to"),
        sort: params.get("sort"),
        has_dub: params.get("has_dub"),
      });
      state.type = params.get("type") || "";
      state.status = params.get("status") || "";
      state.minScore = params.get("min_score") || "";
      state.yearFrom = params.get("year_from") || "";
      state.yearTo = params.get("year_to") || "";
      state.sort = params.get("sort") || "rating";
      state.hasDub = params.get("has_dub") === "1";
      loadCatalog();
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    if (!grid) return;

    var initial = (window.AEMCatalogPage || {}).initial || {};
    applyInitial(initial);
    state.type = initial.type || "";
    state.status = initial.status || "";
    state.minScore = initial.min_score || "";
    state.yearFrom = initial.year_from || "";
    state.yearTo = initial.year_to || "";
    state.sort = initial.sort || "rating";
    state.hasDub = initial.has_dub === "1" || initial.has_dub === "true";

    bindGenres();
    bindForm();
    bindPagination();
    bindViewToggle();
    bindPopState();
    setView(getView());
    loadCatalog();
  });
})();