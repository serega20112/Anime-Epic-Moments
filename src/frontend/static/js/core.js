/* Anime Epic Moments — core.js
   Общие утилиты: CSRF, fetch-обёртка, тосты, модалка, дропдауны. */
(function () {
  "use strict";

  var THEME_KEYS = ["neon", "dark", "light", "rose"];
  var THEME_LABELS = {
    neon: "Неон",
    dark: "Тёмная",
    light: "Светлая",
    rose: "Сакура",
  };

  function csrfToken() {
    var meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute("content") : "";
  }

  function api(url, options) {
    options = options || {};
    options.method = options.method || "GET";
    options.headers = Object.assign(
      {
        "X-CSRF-Token": csrfToken(),
        Accept: "application/json",
      },
      options.headers || {},
    );
    if (
      options.body &&
      typeof options.body !== "string" &&
      !(options.body instanceof FormData)
    ) {
      options.headers["Content-Type"] = "application/json";
      options.body = JSON.stringify(options.body);
    }
    if (options.body instanceof FormData && !options.headers["X-CSRF-Token"]) {
      options.headers["X-CSRF-Token"] = csrfToken();
    }
    options.credentials = "same-origin";
    return fetch(url, options).then(function (response) {
      if (response.status >= 400) {
        return response.json().then(function (data) {
          var error = new Error((data && data.error) || "Ошибка запроса");
          error.status = response.status;
          error.payload = data;
          throw error;
        });
      }
      if (response.status === 204) return null;
      var contentType = response.headers.get("content-type") || "";
      if (contentType.indexOf("application/json") !== -1)
        return response.json();
      return response.text();
    });
  }

  function toast(message, type, timeout) {
    var container = document.getElementById("toast-container");
    if (!container) return;
    var el = document.createElement("div");
    el.className = "toast " + (type || "info");
    var span = document.createElement("span");
    span.textContent = message;
    var close = document.createElement("button");
    close.className = "toast-close";
    close.setAttribute("aria-label", "Закрыть");
    close.textContent = "\u00d7";
    close.addEventListener("click", function () {
      el.remove();
    });
    el.appendChild(span);
    el.appendChild(close);
    container.appendChild(el);
    var ms = timeout || 3200;
    setTimeout(function () {
      el.style.opacity = "0";
      el.style.transition = "opacity .3s";
      setTimeout(function () {
        el.remove();
      }, 320);
    }, ms);
    return el;
  }

  function openModal(title, bodyHtml) {
    var overlay = document.getElementById("modal-overlay");
    var titleEl = document.getElementById("modal-title");
    var bodyEl = document.getElementById("modal-body");
    if (!overlay) return;
    if (titleEl) titleEl.textContent = title || "";
    if (bodyEl) bodyEl.innerHTML = bodyHtml || "";
    overlay.classList.add("open");
    document.body.style.overflow = "hidden";
  }

  function closeModal() {
    var overlay = document.getElementById("modal-overlay");
    if (!overlay) return;
    overlay.classList.remove("open");
    document.body.style.overflow = "";
  }

  function bindDropdown() {
    var btn = document.getElementById("user-menu-btn");
    var menu = document.getElementById("user-dropdown");
    if (!btn || !menu) return;
    btn.addEventListener("click", function (event) {
      event.stopPropagation();
      var open = menu.classList.toggle("open");
      btn.setAttribute("aria-expanded", open ? "true" : "false");
    });
    document.addEventListener("click", function (event) {
      if (!menu.contains(event.target)) {
        menu.classList.remove("open");
        btn.setAttribute("aria-expanded", "false");
      }
    });
  }

  function escapeHtml(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  var NO_COVER = "/static/images/no-cover.svg";

  function animeCard(anime, opts) {
    opts = opts || {};
    var id = anime.anime_id || anime.external_id || anime.id;
    var title = anime.title || "Без названия";
    var cover = anime.cover_url || anime.image_url || NO_COVER;
    var rating = anime.rating;
    var year = anime.year;
    var genres = anime.genres || [];
    var episodeCount = anime.episode_count;
    var watchUrl =
      opts.watchUrl ||
      "/watch/" + id + (anime.episode ? "?episode=" + anime.episode : "");
    var meta = [];
    if (year) meta.push(year);
    if (episodeCount) meta.push(episodeCount + " серий");
    if (!meta.length && genres.length) meta.push(genres[0]);
    return (
      '<a class="anime-card" href="' +
      watchUrl +
      '">' +
      '<div class="poster">' +
      '<img src="' +
      cover +
      '" alt="' +
      escapeHtml(title) +
      '" loading="lazy" onerror="this.onerror=null;this.src=\'' +
      NO_COVER +
      "';\">" +
      (rating ? '<span class="rating-badge">★ ' + rating + "</span>" : "") +
      (genres.length
        ? '<span class="type-badge">' + escapeHtml(genres[0]) + "</span>"
        : "") +
      '<span class="poster-actions"><button type="button" class="btn btn-sm fav-btn" data-fav-id="' +
      escapeHtml(String(id)) +
      '" title="В избранное">🤍</button><span class="btn btn-primary btn-sm">Смотреть</span></span>' +
      "</div>" +
      '<div class="card-body">' +
      '<div class="card-title">' +
      escapeHtml(title) +
      "</div>" +
      (meta.length
        ? '<div class="card-meta">' +
          meta
            .map(function (m) {
              return "<span>" + escapeHtml(String(m)) + "</span>";
            })
            .join('<span class="dot"></span>') +
          "</div>"
        : "") +
      "</div>" +
      "</a>"
    );
  }

  function autoHideFlashes() {
    var flashes = document.querySelectorAll("#flash-messages .flash");
    flashes.forEach(function (el) {
      setTimeout(function () {
        el.style.opacity = "0";
        el.style.transition = "opacity .4s";
        setTimeout(function () {
          el.remove();
        }, 420);
      }, 5200);
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    bindDropdown();
    autoHideFlashes();
    var closeBtn = document.getElementById("modal-close");
    var overlay = document.getElementById("modal-overlay");
    if (closeBtn) closeBtn.addEventListener("click", closeModal);
    if (overlay)
      overlay.addEventListener("click", function (event) {
        if (event.target === overlay) closeModal();
      });
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") closeModal();
    });
  });

  window.AEM = {
    api: api,
    csrfToken: csrfToken,
    toast: toast,
    openModal: openModal,
    closeModal: closeModal,
    animeCard: animeCard,
    escapeHtml: escapeHtml,
    themeKeys: THEME_KEYS,
    themeLabels: THEME_LABELS,
  };
})();
