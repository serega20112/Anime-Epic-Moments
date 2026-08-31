/* Player gestures — mobile: vertical swipe for volume/brightness, double-tap */
"use strict";

import core from "./core.js";

var s = core.state;

function initGestures() {
  if (!s.shell || !s.video) return;

  var touchState = {
    startX: 0,
    startY: 0,
    startTime: 0,
    swiping: false,
    side: null,
    indicator: null
  };

  var SWIPE_THRESHOLD = 15;
  var INDICATOR_HIDE_DELAY = 800;

  function prefersReducedMotion() {
    return window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }

  function createIndicator() {
    if (touchState.indicator) touchState.indicator.remove();
    var el = document.createElement("div");
    el.className = "pc-gesture-indicator";
    el.style.cssText =
      "position:absolute;z-index:25;display:flex;flex-direction:column;align-items:center;" +
      "justify-content:center;width:60px;height:60px;border-radius:12px;" +
      "background:rgba(0,0,0,0.7);color:#fff;font-size:20px;pointer-events:none;" +
      "transition:opacity .3s;opacity:0;";
    s.shell.appendChild(el);
    touchState.indicator = el;
    return el;
  }

  function showIndicator(side, value) {
    var el = touchState.indicator || createIndicator();
    el.innerHTML = '<span style="font-size:22px">' + (side === "volume" ? "\uD83D\uDD0A" : "\uD83D\uDD06") + '</span>' +
      '<span style="font-size:11px;margin-top:2px">' + Math.round(value) + '%</span>';
    el.style.left = side === "volume" ? "calc(100% - 90px)" : "30px";
    el.style.top = "50%";
    el.style.transform = "translateY(-50%)";
    el.style.opacity = "1";

    if (touchState.hideTimer) clearTimeout(touchState.hideTimer);
    touchState.hideTimer = setTimeout(function () {
      el.style.opacity = "0";
    }, INDICATOR_HIDE_DELAY);
  }

  s.shell.addEventListener("touchstart", function (ev) {
    if (ev.touches.length !== 1) return;
    var t = ev.touches[0];
    touchState.startX = t.clientX;
    touchState.startY = t.clientY;
    touchState.startTime = Date.now();
    touchState.swiping = false;
    touchState.side = null;
  }, { passive: true });

  s.shell.addEventListener("touchmove", function (ev) {
    if (ev.touches.length !== 1) return;
    var t = ev.touches[0];
    var dx = t.clientX - touchState.startX;
    var dy = t.clientY - touchState.startY;

    if (!touchState.swiping && Math.abs(dy) > SWIPE_THRESHOLD && Math.abs(dy) > Math.abs(dx)) {
      touchState.swiping = true;
      var shellRect = s.shell.getBoundingClientRect();
      touchState.side = t.clientX < shellRect.left + shellRect.width / 2 ? "brightness" : "volume";
    }

    if (!touchState.swiping) return;
    ev.preventDefault();

    var shellRect = s.shell.getBoundingClientRect();
    var fraction = Math.min(1, Math.max(0, -dy / shellRect.height + 0.5));

    if (touchState.side === "volume") {
      core.setVolumeFraction(fraction);
      showIndicator("volume", fraction * 100);
      try { localStorage.setItem("aem_volume", String(fraction)); } catch (e) {}
    } else {
      var brightness = Math.min(2, Math.max(0.3, 0.5 + (-dy / shellRect.height)));
      s.shell.style.filter = "brightness(" + brightness + ")";
      showIndicator("brightness", brightness * 100);
    }
  }, { passive: false });

  s.shell.addEventListener("touchend", function () {
    if (touchState.swiping) {
      touchState.swiping = false;
      s.shell.style.filter = "";
    }
  }, { passive: true });
}

export { initGestures };
