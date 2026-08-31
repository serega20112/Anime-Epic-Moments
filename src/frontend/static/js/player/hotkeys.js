/* Player hotkeys — keyboard shortcuts with focus filtering */
"use strict";

import core from "./core.js";

var s = core.state;

function isInputFocused() {
  var el = document.activeElement;
  if (!el) return false;
  var tag = el.tagName;
  return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || el.isContentEditable;
}

function isEditorOpen() {
  return !!document.getElementById("pc-highlight-editor");
}

function bindHotkeys() {
  core.on(document, "keydown", function (event) {
    if (!s.video) return;
    if (isInputFocused()) return;

    var code = event.code || event.key;

    if (code === "Escape") {
      event.preventDefault();
      if (isEditorOpen()) {
        var editor = document.getElementById("pc-highlight-editor");
        if (editor) editor.remove();
        return;
      }
      if (document.fullscreenElement) document.exitFullscreen();
      return;
    }

    if (code === "Space" || code === "KeyK") {
      event.preventDefault();
      core.togglePlay();
      return;
    }
    if (code === "ArrowLeft" || code === "KeyJ") {
      event.preventDefault();
      core.seekBy(-10);
      core.emit("hotkeyAction", "seek-10");
      return;
    }
    if (code === "ArrowRight" || code === "KeyL") {
      event.preventDefault();
      core.seekBy(10);
      core.emit("hotkeyAction", "seek+10");
      return;
    }
    if (code === "ArrowUp") {
      event.preventDefault();
      core.setVolumeFraction(Math.min(1, (s.video.volume || 0) + 0.1));
      try { localStorage.setItem("aem_volume", String(s.video.volume)); } catch (e) {}
      return;
    }
    if (code === "ArrowDown") {
      event.preventDefault();
      core.setVolumeFraction(Math.max(0, (s.video.volume || 0) - 0.1));
      try { localStorage.setItem("aem_volume", String(s.video.volume)); } catch (e) {}
      return;
    }
    if (code === "KeyM") {
      event.preventDefault();
      if (s.video.muted) {
        s.video.muted = false;
        core.setVolumeFraction(s.lastVolume > 0 ? s.lastVolume : 0.7);
      } else {
        s.lastVolume = s.video.volume;
        s.video.muted = true;
        core.setVolumeFraction(0);
      }
      return;
    }
    if (code === "KeyF") {
      event.preventDefault();
      if (document.fullscreenElement) document.exitFullscreen();
      else if (s.shell.requestFullscreen) s.shell.requestFullscreen();
      return;
    }
    if (code === "KeyT") {
      event.preventDefault();
      if (core.toggleTheater) core.toggleTheater();
      return;
    }
    if (code === "KeyP") {
      event.preventDefault();
      if (document.pictureInPictureElement) document.exitPictureInPicture().catch(function () {});
      else if (s.video.requestPictureInPicture) s.video.requestPictureInPicture().catch(function () {});
      return;
    }
    if (code === "KeyC") {
      event.preventDefault();
      if (s.video.textTracks && s.video.textTracks.length) {
        var t = s.video.textTracks[0];
        t.mode = t.mode === "showing" ? "disabled" : "showing";
      }
      return;
    }
    if (/^Digit[0-9]$/.test(code) || /^[0-9]$/.test(event.key)) {
      var digit = code.replace("Digit", "");
      if (digit === "") digit = event.key;
      var pct = (Number(digit) || 0) * 0.1;
      core.seekToPercent(pct);
      return;
    }
    if (code === "KeyS") {
      event.preventDefault();
      core.seekBy(90);
      core.emit("hotkeyAction", "skip+90");
      return;
    }
    if (code === "KeyH") {
      event.preventDefault();
      core.emit("openHighlightEditor");
      return;
    }
  });
}

export function initHotkeys() {
  bindHotkeys();
}
