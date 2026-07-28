(function () {
  const escapeHtml = (value) =>
    String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\"/g, "&quot;")
      .replace(/'/g, "&#39;");

  const showToast = (message) => {
    const toast = document.createElement("div");
    toast.textContent = message;
    toast.style.position = "fixed";
    toast.style.right = "16px";
    toast.style.bottom = "16px";
    toast.style.padding = "12px 16px";
    toast.style.background = "rgba(12, 18, 34, 0.96)";
    toast.style.color = "#fff";
    toast.style.borderRadius = "12px";
    toast.style.zIndex = "9999";
    document.body.appendChild(toast);
    window.setTimeout(() => toast.remove(), 2200);
  };

  const requestJson = async (url, options) => {
    const response = await fetch(url, options);
    let payload = null;
    try {
      payload = await response.json();
    } catch (_error) {
      payload = null;
    }
    if (!response.ok) {
      throw new Error(payload?.error || "request_failed");
    }
    return payload;
  };

  const renderComments = (highlightId, items) => {
    const list = document.querySelector(
      `[data-comments-list="${highlightId}"]`,
    );
    if (!list) {
      return;
    }
    if (!items.length) {
      list.innerHTML = "<p>Комментариев пока нет.</p>";
      return;
    }
    list.innerHTML = items
      .map(
        (item) => `
          <article class="comment-item">
            <strong>${escapeHtml(item.username)}</strong>
            <span>${escapeHtml(item.created_at)}</span>
            <p>${escapeHtml(item.content)}</p>
          </article>
        `,
      )
      .join("");
  };

  document.querySelectorAll(".reveal-spoiler-button").forEach((button) => {
    button.addEventListener("click", () => {
      const id = button.dataset.highlightId;
      const description = document.querySelector(
        `[data-highlight-description="${id}"]`,
      );
      const veil = button.closest(".spoiler-veil");
      if (description) {
        description.classList.remove("is-hidden");
      }
      if (veil) {
        veil.remove();
      }
    });
  });

  document.querySelectorAll(".highlight-share-button").forEach((button) => {
    button.addEventListener("click", async () => {
      const shareUrl = `${window.location.origin}${button.dataset.shareUrl}`;
      try {
        await navigator.clipboard.writeText(shareUrl);
        showToast("Ссылка скопирована");
      } catch (_error) {
        window.prompt("Скопируй ссылку", shareUrl);
      }
    });
  });

  document.querySelectorAll(".highlight-like-button").forEach((button) => {
    button.addEventListener("click", async () => {
      const highlightId = button.dataset.highlightId;
      const liked = button.dataset.liked === "1";
      const payload = await requestJson(`/highlights/${highlightId}/likes`, {
        method: liked ? "DELETE" : "POST",
      }).catch(() => null);
      if (!payload) {
        showToast("Не удалось обновить лайк");
        return;
      }
      button.dataset.liked = liked ? "0" : "1";
      button.textContent = liked ? "Лайк" : "Убрать лайк";
      const badge = document.querySelector(
        `[data-highlight-likes-badge="${highlightId}"]`,
      );
      if (badge) {
        badge.textContent = `${payload.likes_count} лайков`;
      }
      showToast(liked ? "Лайк снят" : "Лайк сохранен");
    });
  });

  document.querySelectorAll(".highlight-save-button").forEach((button) => {
    button.addEventListener("click", async () => {
      const highlightId = button.dataset.highlightId;
      const saved = button.dataset.saved === "1";
      const payload = await requestJson(`/highlights/${highlightId}/save`, {
        method: saved ? "DELETE" : "POST",
      }).catch(() => null);
      if (!payload) {
        showToast("Не удалось обновить сохранение");
        return;
      }
      button.dataset.saved = payload.saved ? "1" : "0";
      button.textContent = payload.saved
        ? "Убрать из сохраненных"
        : "Сохранить";
      showToast(
        payload.saved ? "Хайлайт сохранен" : "Хайлайт удален из сохраненных",
      );
    });
  });

  document.querySelectorAll(".highlight-likers-button").forEach((button) => {
    button.addEventListener("click", async () => {
      const highlightId = button.dataset.highlightId;
      const payload = await requestJson(`/highlights/${highlightId}/likes`, {
        method: "GET",
      }).catch(() => null);
      if (!payload) {
        showToast("Не удалось загрузить список лайков");
        return;
      }
      const message = payload.items.length
        ? payload.items
            .map((item) => `${item.username} • ${item.created_at}`)
            .join("\n")
        : "Пока никто не лайкнул";
      window.alert(message);
    });
  });

  document.querySelectorAll(".highlight-comments-toggle").forEach((button) => {
    button.addEventListener("click", async () => {
      const highlightId = button.dataset.highlightId;
      const panel = document.querySelector(
        `[data-comments-panel="${highlightId}"]`,
      );
      if (!panel) {
        return;
      }
      const shouldOpen = panel.hidden;
      panel.hidden = !shouldOpen;
      if (!shouldOpen) {
        return;
      }
      const payload = await requestJson(`/highlights/${highlightId}/comments`, {
        method: "GET",
      }).catch(() => null);
      if (!payload) {
        showToast("Не удалось загрузить комментарии");
        return;
      }
      renderComments(highlightId, payload.items || []);
    });
  });

  document.querySelectorAll(".highlight-comment-form").forEach((form) => {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const highlightId = form.dataset.highlightId;
      const textarea = form.querySelector("textarea[name='content']");
      const payload = await requestJson(`/highlights/${highlightId}/comments`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: textarea?.value || "" }),
      }).catch(() => null);
      if (!payload) {
        showToast("Не удалось добавить комментарий");
        return;
      }
      textarea.value = "";
      const panel = document.querySelector(
        `[data-comments-panel="${highlightId}"]`,
      );
      if (panel) {
        panel.hidden = false;
      }
      const commentsPayload = await requestJson(
        `/highlights/${highlightId}/comments`,
        {
          method: "GET",
        },
      ).catch(() => null);
      if (commentsPayload) {
        renderComments(highlightId, commentsPayload.items || []);
      }
      const badge = document.querySelector(
        `[data-highlight-comments-badge="${highlightId}"]`,
      );
      if (badge) {
        const nextCount = commentsPayload?.items?.length || 1;
        badge.textContent = `${nextCount} комментариев`;
      }
      showToast("Комментарий добавлен");
    });
  });

  document.querySelectorAll(".highlight-delete-button").forEach((button) => {
    button.addEventListener("click", async () => {
      const highlightId = button.dataset.highlightId;
      const response = await fetch(`/highlights/${highlightId}`, {
        method: "DELETE",
      });
      if (!response.ok) {
        showToast("Не удалось удалить хайлайт");
        return;
      }
      document.getElementById(`highlight-${highlightId}`)?.remove();
      showToast("Хайлайт удален");
    });
  });

  document.querySelectorAll(".highlight-edit-button").forEach((button) => {
    button.addEventListener("click", async () => {
      const highlightId = button.dataset.highlightId;
      const title = window.prompt("Название", button.dataset.title);
      if (title === null) {
        return;
      }
      const category = window.prompt(
        "Категория",
        button.dataset.category || "",
      );
      if (category === null) {
        return;
      }
      const episode = window.prompt("Серия", button.dataset.episode);
      if (episode === null) {
        return;
      }
      const startTimestamp = window.prompt(
        "Начало MM:SS",
        button.dataset.start,
      );
      if (startTimestamp === null) {
        return;
      }
      const endTimestamp = window.prompt("Конец MM:SS", button.dataset.end);
      if (endTimestamp === null) {
        return;
      }
      const description = window.prompt("Описание", button.dataset.description);
      if (description === null) {
        return;
      }
      const emotion = window.prompt("Эмоция", button.dataset.emotion);
      if (emotion === null) {
        return;
      }
      const isSpoiler = window.confirm("Отметить как спойлер?");
      const response = await fetch(`/highlights/${highlightId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title,
          category,
          episode,
          start_timestamp: startTimestamp,
          end_timestamp: endTimestamp,
          description,
          is_spoiler: isSpoiler,
          emotion,
        }),
      });
      if (!response.ok) {
        showToast("Не удалось обновить хайлайт");
        return;
      }
      window.location.reload();
    });
  });
})();
