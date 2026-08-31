/* Anime Epic Moments — Player entry point (ES module) */
"use strict";

import core from "./player/core.js";
import { initControls } from "./player/controls.js";
import { initHotkeys } from "./player/hotkeys.js";
import { initHighlights } from "./player/highlights.js";
import { initErrors } from "./player/errors.js";
import { initGestures } from "./player/gestures.js";
import { initProgress } from "./player/progress.js";
import { initWatchTabs } from "./player/tabs.js";

function boot() {
  core.initCore();
  initWatchTabs();
  if (!core.state.shell) return;

  initErrors();
  initControls();
  initHotkeys();
  initHighlights();
  initGestures();
  initProgress();

  core.state.shell.addEventListener("mousemove", function () {
    var s = core.state;
    s.shell.classList.add("controls-visible");
    s.shell.classList.remove("controls-hidden");
    if (s.hideTimer) clearTimeout(s.hideTimer);
    s.hideTimer = setTimeout(function () {
      s.shell.classList.remove("controls-visible");
    }, 2500);
  });

  core.state.shell.addEventListener("click", function (ev) {
    if (ev.target.closest && ev.target.closest(".controls-row")) return;
    if (ev.target.closest && ev.target.closest(".pc-highlight-editor")) return;
    if (ev.target.closest && ev.target.closest(".pc-resume-popup")) return;
    core.togglePlay();
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", boot);
} else {
  boot();
}
