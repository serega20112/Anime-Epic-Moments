/* Player highlights — inline editor with emotions, mini-timeline, preview */
"use strict";

import core from "./core.js";

var s = core.state;

var EMOTIONS = [
  { key: "epic", emoji: "\uD83D\uDD25", label: "EPIC" },
  { key: "cry", emoji: "\uD83D\uDE2D", label: "CRY" },
  { key: "love", emoji: "\u2764\uFE0F", label: "LOVE" },
  { key: "funny", emoji: "\uD83D\uDE02", label: "FUNNY" },
  { key: "wtf", emoji: "\uD83D\uDE28", label: "WTF" },
  { key: "cold", emoji: "\uD83E\uDD76", label: "COLD" },
  { key: "beautiful", emoji: "\u2728", label: "BEAUTIFUL" }
];

function openInlineEditor() {
  if (!s.cfg.isAuthenticated) {
    var opener = core.qs("open-highlight-form-btn");
    if (opener) opener.click();
    return;
  }
  var existing = core.qs("pc-highlight-editor");
  if (existing) return;

  if (!s.video.paused) s.video.pause();

  var startVal = Math.max(0, Math.floor(s.video.currentTime || 0));
  var endVal = Math.min(s.video.duration || startVal + 5, Math.floor((s.video.currentTime || 0) + 5));
  var selectedEmotion = "epic";
  var isPreviewing = false;
  var previewInterval = null;

  var editor = document.createElement("div");
  editor.id = "pc-highlight-editor";
  editor.className = "pc-highlight-editor";
  editor.innerHTML =
    '<div class="phe-header">' +
      '<span class="phe-label">\u2702\uFE0F \u041E\u0442\u043C\u0435\u0442\u0438\u0442\u044C \u043C\u043E\u043C\u0435\u043D\u0442</span>' +
      '<button class="phe-close" id="phe-close">\u2715</button>' +
    '</div>' +

    '<div class="phe-timeline" id="phe-timeline">' +
      '<div class="phe-range" id="phe-range"></div>' +
      '<div class="phe-handle phe-handle-in" id="phe-handle-in"></div>' +
      '<div class="phe-handle phe-handle-out" id="phe-handle-out"></div>' +
    '</div>' +

    '<div class="phe-times">' +
      '<button class="pc-btn phe-time-btn" id="phe-set-in">IN <span id="phe-in">00:00</span></button>' +
      '<button class="pc-btn phe-time-btn" id="phe-set-out">OUT <span id="phe-out">00:05</span></button>' +
    '</div>' +

    '<input type="text" id="phe-title" class="phe-input" placeholder="\u041D\u0430\u0437\u0432\u0430\u043D\u0438\u0435 \u043C\u043E\u043C\u0435\u043D\u0442\u0430" maxlength="120">' +

    '<div class="phe-emotions" id="phe-emotions">' +
      EMOTIONS.map(function (em) {
        return '<button type="button" class="phe-emoji' + (em.key === selectedEmotion ? " active" : "") + '" data-emotion="' + em.key + '" title="' + em.label + '">' + em.emoji + '</button>';
      }).join("") +
    '</div>' +

    '<input type="text" id="phe-description" class="phe-input" placeholder="\u041F\u043E\u0447\u0435\u043C\u0443 \u044D\u0442\u043E\u0442 \u043C\u043E\u043C\u0435\u043D\u0442 \u044D\u043F\u0438\u0447\u043D\u044B\u0439?" maxlength="600">' +

    '<label class="phe-spoiler">' +
      '<input type="checkbox" id="phe-spoiler"> \u0421\u043F\u043E\u0439\u043B\u0435\u0440' +
    '</label>' +

    '<div class="phe-actions">' +
      '<button class="pc-btn" id="phe-preview">\u25B6 \u041F\u0440\u0435\u0434\u043F\u0440\u043E\u0441\u043C\u043E\u0442\u0440</button>' +
      '<button class="pc-btn pc-btn-primary" id="phe-save">\u0421\u043E\u0445\u0440\u0430\u043D\u0438\u0442\u044C</button>' +
    '</div>';

  s.shell.appendChild(editor);

  var inEl = core.qs("phe-in");
  var outEl = core.qs("phe-out");
  var titleEl = core.qs("phe-title");
  var spoilerEl = core.qs("phe-spoiler");
  var descEl = core.qs("phe-description");
  var rangeEl = core.qs("phe-range");
  var handleIn = core.qs("phe-handle-in");
  var handleOut = core.qs("phe-handle-out");
  var pheTimeline = core.qs("phe-timeline");

  function fmt(v) { return core.fmtTime(v); }

  function refresh() {
    if (inEl) inEl.textContent = fmt(startVal);
    if (outEl) outEl.textContent = fmt(endVal);
    updateRange();
  }

  function updateRange() {
    if (!pheTimeline || !rangeEl) return;
    var dur = s.video.duration || 1;
    var leftPct = (startVal / dur) * 100;
    var widthPct = ((endVal - startVal) / dur) * 100;
    rangeEl.style.left = leftPct + "%";
    rangeEl.style.width = Math.max(1, widthPct) + "%";
    if (handleIn) handleIn.style.left = leftPct + "%";
    if (handleOut) handleOut.style.left = (leftPct + widthPct) + "%";
  }

  core.on(core.qs("phe-set-in"), "click", function () {
    startVal = Math.max(0, Math.floor(s.video.currentTime || 0));
    if (endVal <= startVal) endVal = Math.min(s.video.duration || startVal + 5, startVal + 5);
    refresh();
  });

  core.on(core.qs("phe-set-out"), "click", function () {
    endVal = Math.min(s.video.duration || Math.floor(s.video.currentTime || 0) + 5, Math.floor(s.video.currentTime || 0));
    if (endVal <= startVal) startVal = Math.max(0, endVal - 5);
    refresh();
  });

  core.on(core.qs("phe-close"), "click", function () {
    stopPreview();
    editor.remove();
  });

  core.on(editor, "click", function (e) {
    if (e.target === editor) { stopPreview(); editor.remove(); }
  });

  core.on(core.qs("phe-preview"), "click", function () {
    if (isPreviewing) { stopPreview(); return; }
    isPreviewing = true;
    s.video.currentTime = startVal;
    s.video.play().catch(function () {});
    previewInterval = setInterval(function () {
      if (s.video.currentTime >= endVal) {
        s.video.currentTime = startVal;
      }
    }, 200);
    var previewBtn = core.qs("phe-preview");
    if (previewBtn) previewBtn.textContent = "\u23F9 \u0421\u0442\u043E\u043F";
  });

  function stopPreview() {
    if (previewInterval) { clearInterval(previewInterval); previewInterval = null; }
    isPreviewing = false;
    var previewBtn = core.qs("phe-preview");
    if (previewBtn) previewBtn.textContent = "\u25B6 \u041F\u0440\u0435\u0434\u043F\u0440\u043E\u0441\u043C\u043E\u0442\u0440";
  }

  var emotionsEl = core.qs("phe-emotions");
  if (emotionsEl) {
    core.on(emotionsEl, "click", function (e) {
      var btn = e.target.closest("[data-emotion]");
      if (!btn) return;
      selectedEmotion = btn.getAttribute("data-emotion");
      emotionsEl.querySelectorAll(".phe-emoji").forEach(function (b) { b.classList.remove("active"); });
      btn.classList.add("active");
    });
  }

  core.on(core.qs("phe-save"), "click", function () {
    stopPreview();
    var body = {
      episode: s.cfg.episode,
      title: titleEl ? titleEl.value : "",
      start_timestamp: startVal,
      end_timestamp: endVal,
      emotion: selectedEmotion,
      description: descEl ? descEl.value : "",
      is_spoiler: spoilerEl ? !!spoilerEl.checked : false
    };
    var src = core.activeSource();
    if (src && src.id != null) body.watch_source_id = src.id;
    if (src && src.translationId != null) body.translation_id = src.translationId;

    AEM.api("/watch/" + s.cfg.animeId + "/highlights", { method: "POST", body: body })
      .then(function () {
        AEM.toast("\u0425\u0430\u0439\u043B\u0430\u0439\u0442 \u0441\u043E\u0437\u0434\u0430\u043D", "success");
        editor.remove();
        core.emit("highlightCreated", body);
      })
      .catch(function (err) {
        AEM.toast((err && err.message) || "\u041E\u0448\u0438\u0431\u043A\u0430 \u0441\u043E\u0437\u0434\u0430\u043D\u0438\u044F", "error");
      });
  });

  refresh();
}

function wireSidebarForm() {
  var form = core.qs("highlight-form");
  if (!form) return;
  core.on(form, "submit", function (e) {
    e.preventDefault();
    if (!s.cfg.isAuthenticated) return;

    var startInput = core.qs("hf-start");
    var endInput = core.qs("hf-end");
    var titleInput = core.qs("hf-title");
    var descInput = core.qs("hf-description");
    var spoilerInput = core.qs("hf-spoiler");

    var startTs = parseTimestamp(startInput ? startInput.value : "00:00");
    var endTs = parseTimestamp(endInput ? endInput.value : "00:10");
    var emotion = "epic";
    var activeSticker = form.querySelector(".hf-emotion[style*='border-color']");
    if (activeSticker) emotion = activeSticker.getAttribute("data-emotion") || "epic";

    var body = {
      episode: s.cfg.episode,
      title: titleInput ? titleInput.value : "",
      start_timestamp: startTs,
      end_timestamp: endTs,
      emotion: emotion,
      description: descInput ? descInput.value : "",
      is_spoiler: spoilerInput ? !!spoilerInput.checked : false
    };
    var src = core.activeSource();
    if (src && src.id != null) body.watch_source_id = src.id;
    if (src && src.translationId != null) body.translation_id = src.translationId;

    AEM.api("/watch/" + s.cfg.animeId + "/highlights", { method: "POST", body: body })
      .then(function () {
        AEM.toast("\u0425\u0430\u0439\u043B\u0430\u0439\u0442 \u0441\u043E\u0437\u0434\u0430\u043D", "success");
        form.reset();
        core.emit("highlightCreated", body);
      })
      .catch(function (err) {
        AEM.toast((err && err.message) || "\u041E\u0448\u043B\u0431\u043A\u0430 \u0441\u043E\u0437\u0434\u0430\u043D\u0438\u044F", "error");
      });
  });

  var emotionsContainer = form.querySelector(".hf-emotions");
  if (emotionsContainer) {
    core.on(emotionsContainer, "click", function (e) {
      var btn = e.target.closest(".hf-emotion");
      if (!btn) return;
      emotionsContainer.querySelectorAll(".hf-emotion").forEach(function (b) { b.style.borderColor = ""; });
      btn.style.borderColor = "var(--color-accent)";
    });
  }
}

function parseTimestamp(str) {
  var parts = (str || "00:00").split(":");
  if (parts.length === 2) return parseInt(parts[0], 10) * 60 + parseInt(parts[1], 10);
  if (parts.length === 3) return parseInt(parts[0], 10) * 3600 + parseInt(parts[1], 10) * 60 + parseInt(parts[2], 10);
  return 0;
}

export function initHighlights() {
  var markBtn = core.qs("pc-mark-highlight");
  if (markBtn) {
    core.on(markBtn, "click", function (e) { e.stopPropagation(); openInlineEditor(); });
  }
  core.subscribe("openHighlightEditor", openInlineEditor);
  wireSidebarForm();
}
