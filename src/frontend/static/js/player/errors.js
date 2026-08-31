/* Player errors — unified error component with classification and retry */
"use strict";

import core from "./core.js";

var s = core.state;

var ERROR_MESSAGES = {
  network: "\u041D\u0435\u0442 \u0441\u043E\u0435\u0434\u0438\u043D\u0435\u043D\u0438\u044F \u0441 \u0441\u0435\u0440\u0432\u0435\u0440\u043E\u043C. \u041F\u0440\u043E\u0432\u0435\u0440\u044C\u0442\u0435 \u0438\u043D\u0442\u0435\u0440\u043D\u0435\u0442.",
  media: "\u0424\u043E\u0440\u043C\u0430\u0442 \u043D\u0435 \u043F\u043E\u0434\u0434\u0435\u0440\u0436\u0438\u0432\u0430\u0435\u0442\u0441\u044F.",
  general: "\u0418\u0441\u0442\u043E\u0447\u043D\u0438\u043A \u043D\u0435\u0434\u043E\u0441\u0442\u0443\u043F\u0435\u043D.",
  noSources: "\u0412\u0441\u0435 \u0434\u043E\u0441\u0442\u0443\u043F\u043D\u044B\u0435 \u0438\u0441\u0442\u043E\u0447\u043D\u0438\u043A\u0438 \u043D\u0435\u0434\u043E\u0441\u0442\u0443\u043F\u043D\u044B."
};

var retryCount = 0;
var MAX_RETRIES = 3;

function classifyHlsError(data) {
  if (!data) return "general";
  if (data.type === Hls.ErrorTypes.NETWORK_ERROR) return "network";
  if (data.type === Hls.ErrorTypes.MEDIA_ERROR) return "media";
  return "general";
}

function showError(message, opts) {
  var box = core.qs("pc-error");
  if (!box) return;

  var hasAlternatives = opts && opts.hasAlternatives;
  box.innerHTML =
    '<div class="pc-error-inner">' +
      '<div class="pc-error-icon">\u26A0\uFE0F</div>' +
      '<div class="pc-error-msg">' + (message || "\u041E\u0448\u0438\u0431\u043A\u0430") + '</div>' +
      '<div class="pc-error-actions">' +
        '<button class="pc-btn pc-error-retry" id="pc-error-retry">\u041F\u043E\u0432\u0442\u043E\u0440\u0438\u0442\u044C</button>' +
        (hasAlternatives ?
          '<button class="pc-btn pc-error-change" id="pc-error-change">\u0421\u043C\u0435\u043D\u0438\u0442\u044C \u0438\u0441\u0442\u043E\u0447\u043D\u0438\u043A</button>' : '') +
      '</div>' +
    '</div>';
  box.style.display = "flex";

  var retryBtn = core.qs("pc-error-retry");
  var changeBtn = core.qs("pc-error-change");

  if (retryBtn) {
    core.on(retryBtn, "click", function () {
      box.style.display = "none";
      retryCount++;
      if (opts && typeof opts.retry === "function") opts.retry();
    });
  }
  if (changeBtn) {
    core.on(changeBtn, "click", function () {
      box.style.display = "none";
      retryCount = 0;
      if (opts && typeof opts.change === "function") opts.change();
    });
  }
}

function hideError() {
  var box = core.qs("pc-error");
  if (box) box.style.display = "none";
}

function handleHlsError(source, data) {
  if (!data || !data.fatal) return;

  var type = classifyHlsError(data);

  if (type === "media" && retryCount < MAX_RETRIES) {
    try {
      s.hls.recoverMediaError();
      core.setStatus("\u0412\u043E\u0441\u0441\u0442\u0430\u043D\u0430\u0432\u043B\u0438\u0432\u0430\u044E \u043C\u0435\u0434\u0438\u0430\u2026");
      retryCount++;
      return;
    } catch (e) {}
  }

  retryCount = 0;
  trySwitchToNextSource(source, ERROR_MESSAGES[type] || ERROR_MESSAGES.general);
}

function trySwitchToNextSource(failedSource, errorMsg) {
  var sources = s.cfg.sources || [];
  var match = null;
  for (var i = 0; i < sources.length; i++) {
    var sr = sources[i];
    if (sr.id === failedSource.id) continue;
    if (failedSource.translationId != null && sr.translationId != null &&
        String(sr.translationId) === String(failedSource.translationId)) {
      match = sr;
      break;
    }
  }

  if (match) {
    for (var j = 0; j < sources.length; j++) sources[j].active = sources[j].id === match.id;
    core.loadSource(match);
    return;
  }

  var altSources = sources.filter(function (sr) { return sr.id !== failedSource.id; });
  showError(errorMsg || ERROR_MESSAGES.general, {
    hasAlternatives: altSources.length > 0,
    retry: function () { core.loadSource(failedSource); },
    change: function () {
      var dropdown = core.qs("pc-settings-dropdown");
      if (dropdown) dropdown.classList.add("open");
    }
  });
}

export function initErrors() {
  core.subscribe("hlsError", function (evt) {
    handleHlsError(evt.source, evt.data);
  });

  core.subscribe("sourceLoaded", function () {
    retryCount = 0;
    hideError();
  });
}

export { showError, hideError, trySwitchToNextSource };
