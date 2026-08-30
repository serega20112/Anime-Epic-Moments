/* Anime Epic Moments — search.js
   Автокомплит в шапке + поиск по названию. */
(function () {
  "use strict";

  var input,
    box,
    clearBtn,
    timer = null,
    items = [],
    activeIndex = -1,
    abort = null;

  function init() {
    input = document.getElementById("header-search-input");
    box = document.getElementById("autocomplete");
    clearBtn = document.getElementById("search-clear");
    if (!input || !box) return;

    /* Живой автокомплит при вводе отключён: результаты показываем
       только после отправки формы (Enter). Здесь — поведение Enter/Escape. */
    input.addEventListener("keydown", onKeydown);
    if (clearBtn) {
      clearBtn.addEventListener("click", function () {
        input.value = "";
        box.classList.remove("open");
        input.focus();
      });
    }
  }

  function onInput() {
    if (timer) clearTimeout(timer);
    var query = input.value.trim();
    if (!query) {
      close();
      return;
    }
    timer = setTimeout(function () {
      fetchSuggestions(query);
    }, 220);
  }

  function fetchSuggestions(query) {
    if (abort) abort.abort();
    abort = new AbortController();
    fetch(
      "/anime/api/autocomplete?query=" + encodeURIComponent(query) + "&limit=6",
      {
        signal: abort.signal,
        credentials: "same-origin",
      },
    )
      .then(function (response) {
        return response.json();
      })
      .then(function (data) {
        items = Array.isArray(data) ? data : [];
        activeIndex = -1;
        render();
      })
      .catch(function (err) {
        if (err.name !== "AbortError") close();
      });
  }

  function render() {
    if (!items.length) {
      box.innerHTML =
        '<div class="autocomplete-empty">Ничего не найдено…</div>';
      box.classList.add("open");
      return;
    }
    var html = "";
    items.forEach(function (anime, i) {
      var title = anime.title || "Без названия";
      var cover = anime.cover_url || "/static/images/no-cover.svg";
      var meta = [];
      if (anime.year) meta.push(anime.year);
      if (anime.episode_count) meta.push(anime.episode_count + " сер.");
      if (anime.rating) meta.push("★ " + anime.rating);
      html +=
        '<div class="autocomplete-item' +
        (i === activeIndex ? " active" : "") +
        '" data-index="' +
        i +
        '" role="option">' +
        '<img src="' +
        cover +
        '" alt="" loading="lazy" onerror="this.onerror=null;this.src=\'/static/images/no-cover.svg\';">' +
        "<div>" +
        '<div class="ac-title">' +
        escapeHtml(title) +
        "</div>" +
        (meta.length
          ? '<div class="ac-meta">' + escapeHtml(meta.join(" · ")) + "</div>"
          : "") +
        "</div>" +
        "</div>";
    });
    box.innerHTML = html;
    box.classList.add("open");
    Array.prototype.forEach.call(
      box.querySelectorAll(".autocomplete-item"),
      function (el) {
        el.addEventListener("click", function () {
          var anime = items[Number(el.getAttribute("data-index"))];
          goTo(anime);
        });
        el.addEventListener("mousemove", function () {
          activeIndex = Number(el.getAttribute("data-index"));
          updateActive();
        });
      },
    );
  }

  function onKeydown(event) {
    if (!box.classList.contains("open") || !items.length) return;
    if (event.key === "ArrowDown") {
      event.preventDefault();
      activeIndex = (activeIndex + 1) % items.length;
      updateActive();
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      activeIndex = (activeIndex - 1 + items.length) % items.length;
      updateActive();
    } else if (event.key === "Enter" && activeIndex >= 0) {
      event.preventDefault();
      goTo(items[activeIndex]);
    } else if (event.key === "Escape") {
      box.classList.remove("open");
    }
  }

  function updateActive() {
    var els = box.querySelectorAll(".autocomplete-item");
    Array.prototype.forEach.call(els, function (el, i) {
      el.classList.toggle("active", i === activeIndex);
    });
  }

  function goTo(anime) {
    box.classList.remove("open");
    var id = anime.anime_id || anime.external_id || anime.id;
    if (!id) return;
    window.location.href = "/watch/" + id;
  }

  function close() {
    items = [];
    activeIndex = -1;
    box.classList.remove("open");
  }

  function escapeHtml(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
