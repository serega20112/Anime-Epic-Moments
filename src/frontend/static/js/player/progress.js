/* Player progress — save position, resume popup, completion event */
"use strict";

import core from "./core.js";

var s = core.state;
var saveTimer = null;
var hasResumed = false;

function startSaveLoop() {
  if (!s.cfg.isAuthenticated) return;
  if (saveTimer) clearInterval(saveTimer);
  saveTimer = setInterval(saveProgress, 10000);
  window.addEventListener("beforeunload", saveProgress);
}

function stopSaveLoop() {
  if (saveTimer) { clearInterval(saveTimer); saveTimer = null; }
}

function saveProgress() {
  if (!s.cfg.isAuthenticated || !s.video || !s.video.duration) return;
  var source = core.activeSource();
  var body = {
    episode: s.cfg.episode,
    watch_source_id: source ? source.id : null,
    position_seconds: Math.round(s.video.currentTime),
    volume: s.video.volume,
    is_paused: s.video.paused
  };
  AEM.api("/watch/" + s.cfg.animeId + "/session", { method: "POST", body: body }).catch(function () {});
}

function showResumePopup() {
  if (hasResumed) return;
  var lastPos = s.cfg.lastPositionSeconds || s.cfg.preferredStartSeconds;
  if (!lastPos || lastPos < 10) return;
  hasResumed = true;

  var popup = document.createElement("div");
  popup.className = "pc-resume-popup";
  popup.innerHTML =
    '<div class="pc-resume-inner">' +
      '<span class="pc-resume-text">\u041F\u0440\u043E\u0434\u043E\u043B\u0436\u0438\u0442\u044C \u0441 ' + core.fmtTime(lastPos) + '?</span>' +
      '<div class="pc-resume-actions">' +
        '<button class="pc-btn pc-btn-primary pc-resume-yes" id="pc-resume-yes">\u0414\u0430</button>' +
        '<button class="pc-btn pc-resume-no" id="pc-resume-no">\u0421\u043D\u0430\u0447\u0430\u043B\u0430</button>' +
      '</div>' +
    '</div>';
  s.shell.appendChild(popup);

  var yesBtn = core.qs("pc-resume-yes");
  var noBtn = core.qs("pc-resume-no");

  if (yesBtn) {
    core.on(yesBtn, "click", function () {
      s.video.currentTime = lastPos;
      popup.remove();
    });
  }
  if (noBtn) {
    core.on(noBtn, "click", function () {
      popup.remove();
    });
  }

  setTimeout(function () {
    if (popup.parentNode) popup.remove();
  }, 8000);
}

function sendCompletionEvent() {
  if (!s.cfg.isAuthenticated) return;
  var body = { episode: s.cfg.episode };
  AEM.api("/watch/" + s.cfg.animeId + "/episode/complete", { method: "POST", body: body }).catch(function () {});
}

export function initProgress() {
  core.subscribe("play", startSaveLoop);
  core.subscribe("pause", function () { saveProgress(); });
  core.subscribe("seeked", saveProgress);
  core.subscribe("ended", function () { saveProgress(); sendCompletionEvent(); });

  core.subscribe("sourceLoaded", function () {
    if (!hasResumed) {
      setTimeout(showResumePopup, 500);
    }
  });

  var completionFired = false;
  core.on(s.video, "timeupdate", function () {
    if (!s.video || !s.video.duration || completionFired) return;
    if (s.video.currentTime >= s.video.duration * 0.9) {
      completionFired = true;
      sendCompletionEvent();
    }
  });
}
