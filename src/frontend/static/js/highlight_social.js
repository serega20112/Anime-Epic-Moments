/* Anime Epic Moments — highlight_social.js
   Соц-взаимодействия на карточках хайлайтов: лайки, сохранения, комментарии. */
(function () {
  "use strict";

  var AEM = window.AEM;
  if (!AEM) return;

  function loggedIn() {
    return !!window.AEMHighlightSocial && !!window.AEMHighlightSocial.loggedIn;
  }

  function requireAuth(action) {
    if (loggedIn()) return true;
    AEM.toast("Войдите, чтобы совершить это действие", "warning");
    setTimeout(function () {
      window.location.href = "/login";
    }, 1200);
    return false;
  }

  function card(btn) {
    return btn.closest(".highlight-card");
  }

  function updateCount(btn, label) {
    var countEl = btn.querySelector(".hc-count");
    if (!countEl) return;
    var current = parseInt(countEl.textContent || "0", 10) || 0;
    var liked = btn.classList.contains("active");
    countEl.textContent = Math.max(0, current + (liked ? 1 : -1));
  }

  function toggleLike(btn) {
    var id = btn.getAttribute("data-id");
    var c = card(btn);
    var willLike = !btn.classList.contains("active");
    if (!requireAuth(willLike)) return;
    btn.disabled = true;
    AEM.api("/highlights/" + id + "/likes", {
      method: willLike ? "POST" : "DELETE",
    })
      .then(function () {
        btn.classList.toggle("active", willLike);
        btn.setAttribute("aria-pressed", willLike ? "true" : "false");
        if (c) c.setAttribute("data-liked", willLike ? "1" : "0");
        updateCount(btn, "likes");
        btn.disabled = false;
      })
      .catch(function (err) {
        btn.disabled = false;
        AEM.toast(
          err.status === 401
            ? "Войдите, чтобы поставить лайк"
            : "Не удалось обновить лайк",
          "error",
        );
      });
  }

  function toggleSave(btn) {
    var id = btn.getAttribute("data-id");
    var c = card(btn);
    var willSave = !btn.classList.contains("active");
    if (!requireAuth(willSave)) return;
    btn.disabled = true;
    AEM.api("/highlights/" + id + "/save", {
      method: willSave ? "POST" : "DELETE",
    })
      .then(function () {
        btn.classList.toggle("active", willSave);
        btn.setAttribute("aria-pressed", willSave ? "true" : "false");
        if (c) c.setAttribute("data-saved", willSave ? "1" : "0");
        AEM.toast(
          willSave ? "Хайлайт сохранён" : "Удалён из сохранённых",
          "success",
        );
        btn.disabled = false;
      })
      .catch(function (err) {
        btn.disabled = false;
        AEM.toast(
          err.status === 401
            ? "Войдите, чтобы сохранить"
            : "Не удалось сохранить",
          "error",
        );
      });
  }

  function openShare(btn) {
    var shareUrl =
      location.origin + "/highlights/share/" + btn.getAttribute("data-id");
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(shareUrl).then(function () {
        AEM.toast("Ссылка скопирована", "success");
      });
    } else {
      AEM.toast(shareUrl, "info");
    }
  }

  function openComments(btn) {
    var id = btn.getAttribute("data-id");
    if (!requireAuth(true)) return;
    AEM.openModal(
      "Комментарии",
      '<div class="comments-loading"><div class="spinner"></div></div>',
    );
    AEM.api("/highlights/" + id + "/comments")
      .then(function (data) {
        var items = (data && data.items) || [];
        var html = '<div class="comments-list">';
        if (!items.length) {
          html += '<p class="muted">Пока нет комментариев. Будьте первым!</p>';
        }
        items.forEach(function (item) {
          html +=
            '<div class="comment"><div class="comment-head"><b>' +
            AEM.escapeHtml(item.username) +
            "</b>" +
            '<span class="muted">' +
            AEM.escapeHtml(String(item.created_at || "")) +
            "</span></div>" +
            "<p>" +
            AEM.escapeHtml(item.content) +
            "</p></div>";
        });
        html += "</div>";
        html +=
          '<div class="comment-form"><input type="text" id="new-comment-input" placeholder="Напишите комментарий…" maxlength="500">' +
          '<button class="btn btn-primary btn-sm" id="new-comment-send">Отправить</button></div>';
        AEM.openModal("Комментарии", html);
        var input = document.getElementById("new-comment-input");
        var send = document.getElementById("new-comment-send");
        function submit() {
          var text = (input.value || "").trim();
          if (!text) return;
          send.disabled = true;
          AEM.api("/highlights/" + id + "/comments", {
            method: "POST",
            body: { content: text },
          })
            .then(function () {
              AEM.closeModal();
              AEM.toast("Комментарий добавлен", "success");
              window.dispatchEvent(
                new CustomEvent("aem:comment-added", { detail: { id: id } }),
              );
            })
            .catch(function () {
              send.disabled = false;
              AEM.toast("Не удалось добавить комментарий", "error");
            });
        }
        send.addEventListener("click", submit);
        input.addEventListener("keydown", function (event) {
          if (event.key === "Enter") submit();
        });
      })
      .catch(function () {
        AEM.openModal(
          "Комментарии",
          '<p class="muted">Не удалось загрузить комментарии.</p>',
        );
      });
  }

  document.addEventListener("click", function (event) {
    var btn = event.target.closest(".hc-action");
    if (!btn) return;
    var action = btn.getAttribute("data-action");
    if (action === "like") toggleLike(btn);
    else if (action === "save") toggleSave(btn);
    else if (action === "comment") openComments(btn);
  });

  window.AEMHighlightSocial = { loggedIn: !!window.AEM_LOGGED_IN };
})();
