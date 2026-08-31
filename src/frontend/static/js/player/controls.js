/* Player controls — YouTube-style UI: playback, timeline, volume, settings */
"use strict";

import core from "./core.js";

var s = core.state;

function buildControlsHTML() {
  return (
    '<div class="controls-row">' +

    /* LEFT group: playback */
    '<div class="pc-group pc-group-left">' +
      '<button class="pc-btn pc-btn-play" id="pc-play" aria-label="Воспроизведение">▶</button>' +
      '<button class="pc-btn pc-btn-skip pc-btn-skip-long" id="pc-skip90" aria-label="Вперёд 90 секунд" title="+1:30 (S)">+1:30</button>' +
      '<div class="pc-volume-group">' +
        '<button class="pc-btn pc-btn-icon" id="pc-mute" aria-label="Звук">🔊</button>' +
        '<div class="pc-volume" id="pc-volume" role="slider" aria-label="Громкость" aria-valuemin="0" aria-valuemax="1" aria-valuenow="1">' +
          '<div class="pc-vol-fill" id="pc-vol-fill"></div>' +
          '<div class="pc-vol-handle" id="pc-vol-handle"></div>' +
        '</div>' +
      '</div>' +
    '</div>' +

    /* CENTER: timeline */
    '<div class="pc-group pc-group-center">' +
      '<span class="pc-time" id="pc-cur">00:00</span>' +
      '<div class="pc-timeline" id="pc-timeline" role="slider" aria-label="Прогресс воспроизведения" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0">' +
        '<div class="pc-tl-buffer" id="pc-tl-buffer"></div>' +
        '<div class="pc-tl-fill" id="pc-tl-fill"></div>' +
        '<div class="pc-tl-handle" id="pc-tl-handle"></div>' +
        '<div class="pc-tl-heatmap" id="pc-tl-heatmap"></div>' +
      '</div>' +
      '<span class="pc-time" id="pc-dur">00:00</span>' +
    '</div>' +

    /* RIGHT group: settings */
    '<div class="pc-group pc-group-right">' +
      '<div class="pc-settings-menu" id="pc-settings-menu">' +
        '<button class="pc-btn pc-btn-icon" id="pc-settings-btn" aria-label="Настройки" title="Настройки">⚙️</button>' +
        '<div class="pc-settings-dropdown" id="pc-settings-dropdown">' +
          '<div class="pc-settings-section">' +
            '<div class="pc-settings-label">Качество</div>' +
            '<select id="pc-quality-select" class="pc-settings-select" aria-label="Качество видео (HLS)"></select>' +
          '</div>' +
          '<div class="pc-settings-section">' +
            '<div class="pc-settings-label">Озвучка</div>' +
            '<select id="pc-source-select" class="pc-settings-select" aria-label="Озвучка / Источник"></select>' +
          '</div>' +
        '</div>' +
      '</div>' +
      '<button class="pc-btn pc-btn-icon" id="pc-mark-highlight" aria-label="Отметить момент" title="Отметить момент (H)">★</button>' +
      '<button class="pc-btn pc-btn-icon pc-btn-hide-mobile" id="pc-theater-btn" aria-label="Театральный режим" title="Театральный режим (T)">🎬</button>' +
      '<button class="pc-btn pc-btn-icon pc-btn-hide-mobile" id="pc-pip-btn" aria-label="Картинка-в-картинке" title="Картинка-в-картинке (P)">🖼</button>' +
      '<button class="pc-btn pc-btn-icon" id="pc-fullscreen" aria-label="Полноэкранный режим" title="Полноэкранный режим (F)">⛶</button>' +
    '</div>' +

    '</div>'
  );
}

function buildShell() {
  core.teardown();
  s.shell.innerHTML = "";

  var videoEl = document.createElement("video");
  videoEl.setAttribute("playsinline", "");
  videoEl.setAttribute("preload", "metadata");
  videoEl.className = "player-video";
  s.shell.appendChild(videoEl);
  s.video = videoEl;

  var dtOverlay = document.createElement("div");
  dtOverlay.className = "pc-double-tap-overlay";
  var left = document.createElement("div"); left.className = "pc-dt-zone";
  var right = document.createElement("div"); right.className = "pc-dt-zone";
  dtOverlay.appendChild(left); dtOverlay.appendChild(right);
  s.shell.appendChild(dtOverlay);

  var controls = document.createElement("div");
  controls.className = "controls";
  controls.innerHTML = buildControlsHTML();
  s.shell.appendChild(controls);

  var playCenter = document.createElement("button");
  playCenter.className = "pc-play-center";
  playCenter.id = "pc-play-center";
  playCenter.textContent = "▶";
  s.shell.appendChild(playCenter);

  var errorBox = document.createElement("div");
  errorBox.id = "pc-error";
  errorBox.className = "pc-error";
  s.shell.appendChild(errorBox);

  s.shell.classList.add("controls-visible");
  setTimeout(function () { s.shell.classList.remove("controls-visible"); }, 1200);

  var src = core.activeSource();
  if (src) core.loadSource(src); else core.setStatus("Нет источников");

  setupDoubleTap(left, right);
}

function initSourceSelect() {
  var select = core.qs("pc-source-select");
  if (!select || !s.cfg.sources) return;
  select.innerHTML = s.cfg.sources.map(function (sr) {
    var label = sr.translationName || sr.label || "Источник";
    return '<option value="' + (sr.id != null ? sr.id : sr.url) + '" ' + (sr.active ? "selected" : "") + '>' + label + '</option>';
  }).join("");
  core.on(select, "change", function () {
    core.switchSource(select.value);
  });

  try {
    var savedKey = "aem_src_" + (s.cfg.animeId || "");
    var saved = localStorage.getItem(savedKey);
    if (saved) {
      var found = false;
      for (var i = 0; i < select.options.length; i++) {
        if (String(select.options[i].value) === String(saved)) {
          select.value = saved;
          found = true;
          break;
        }
      }
      if (found) {
        var evt = document.createEvent("Event");
        evt.initEvent("change", true, true);
        select.dispatchEvent(evt);
      }
    }
  } catch (e) {}
}

function populateHlsLevels(source) {
  var select = core.qs("pc-quality-select");
  if (!select) return;

  var sourceKey = "aem_quality_" + (s.cfg.animeId || "") + "_" + (source && source.id != null ? source.id : encodeURIComponent(source.url));
  var hasLevels = s.hls && s.hls.levels && s.hls.levels.length > 0;

  select.innerHTML = "";
  var autoOpt = document.createElement("option");
  autoOpt.value = "auto";
  autoOpt.textContent = "Авто";
  select.appendChild(autoOpt);

  if (hasLevels) {
    s.hls.levels.forEach(function (l, idx) {
      var opt = document.createElement("option");
      opt.value = String(idx);
      opt.textContent = l.height ? (l.height + "p") : (Math.round((l.bitrate || 0) / 1000) + "kbps");
      select.appendChild(opt);
    });
  }

  select.disabled = !hasLevels;

  // Determine the level to select: saved preference first, else the active HLS level.
  var desired = null;
  try {
    var saved = sourceKey && localStorage.getItem(sourceKey);
    if (saved != null && saved !== "") desired = saved;
  } catch (e) {}
  if (desired == null) {
    var cur = s.hls && s.hls.currentLevel;
    desired = cur === -1 || cur == null ? "auto" : String(cur);
  }

  if (desired === "auto" && s.hls) s.hls.currentLevel = -1;
  else if (desired != null && !isNaN(Number(desired)) && desired !== "auto" && s.hls) s.hls.currentLevel = Number(desired);
  select.value = (desired === "auto" || !select.options[desired]) ? "auto" : desired;

  // Single onchange handler (property assignment overwrites previous), no accumulation.
  select.onchange = function () {
    var v = select.value;
    try { if (sourceKey) localStorage.setItem(sourceKey, v); } catch (e) {}
    if (!s.hls) return;
    if (v === "auto") s.hls.currentLevel = -1;
    else s.hls.currentLevel = Number(v);
  };
}

function bindPlayback() {
  var playBtn = core.qs("pc-play");
  var playCenter = core.qs("pc-play-center");
  var skip90 = core.qs("pc-skip90");

  function updatePlayIcon() {
    if (playBtn) playBtn.textContent = s.video && !s.video.paused ? "⏸" : "▶";
  }

  if (playBtn) core.on(playBtn, "click", function (e) { e.stopPropagation(); core.togglePlay(); });
  if (playCenter) core.on(playCenter, "click", function (e) { e.stopPropagation(); core.togglePlay(); });
  if (skip90) core.on(skip90, "click", function (e) { e.stopPropagation(); core.seekBy(90); });

  if (s.video) {
    core.on(s.video, "play", function () {
      s.shell.classList.remove("controls-visible");
      showControlsBrief();
      updatePlayIcon();
      core.setStatus("Смотрю");
      core.emit("play");
    });
    core.on(s.video, "pause", function () {
      s.shell.classList.add("controls-visible");
      updatePlayIcon();
      core.setStatus("Пауза");
      core.emit("pause");
    });
    core.on(s.video, "timeupdate", updateTimeline);
    core.on(s.video, "progress", updateTimeline);
    core.on(s.video, "loadedmetadata", updateTimeline);
    core.on(s.video, "ended", function () { core.emit("ended"); });
  }
}

function updateTimeline() {
  if (!s.video || !s.video.duration) return;
  var cur = core.qs("pc-cur");
  var dur = core.qs("pc-dur");
  var tlFill = core.qs("pc-tl-fill");
  var tlBuffer = core.qs("pc-tl-buffer");
  var tlHandle = core.qs("pc-tl-handle");

  if (cur) cur.textContent = core.fmtTime(s.video.currentTime);
  if (dur) dur.textContent = core.fmtTime(s.video.duration);

  var pct = s.video.duration ? s.video.currentTime / s.video.duration : 0;
  if (tlFill) tlFill.style.width = (pct * 100) + "%";
  if (tlHandle) tlHandle.style.left = (pct * 100) + "%";

  if (tlBuffer && s.video.buffered && s.video.buffered.length) {
    var be = s.video.buffered.end(s.video.buffered.length - 1);
    tlBuffer.style.width = (Math.min(1, be / s.video.duration) * 100) + "%";
  }

  var timeline = core.qs("pc-timeline");
  if (timeline) timeline.setAttribute("aria-valuenow", Math.round(pct * 100));
}

function bindTimeline() {
  var timeline = core.qs("pc-timeline");
  var scrubbing = false;

  function pctFromEvent(ev) {
    var r = timeline.getBoundingClientRect();
    if (r.width <= 0) return 0;
    return Math.min(1, Math.max(0, (ev.clientX - r.left) / r.width));
  }

  function seekTo(pct) {
    if (!s.video || !s.video.duration) return;
    s.video.currentTime = Math.min(s.video.duration, Math.max(0, pct * s.video.duration));
    updateTimeline();
  }

  if (timeline) {
    core.on(timeline, "pointerdown", function (ev) {
      ev.preventDefault(); ev.stopPropagation();
      scrubbing = true;
      if (timeline.setPointerCapture) try { timeline.setPointerCapture(ev.pointerId); } catch (e) {}
      seekTo(pctFromEvent(ev));
    });
  }
  core.on(document, "pointermove", function (ev) {
    if (!scrubbing) return;
    seekTo(pctFromEvent(ev));
  });
  core.on(document, "pointerup", function () {
    if (!scrubbing) return;
    scrubbing = false;
    core.emit("seeked");
  });
}

function bindVolume() {
  var muteBtn = core.qs("pc-mute");
  var vol = core.qs("pc-volume");
  var volFill = core.qs("pc-vol-fill");
  var volHandle = core.qs("pc-vol-handle");
  var scrubbingVol = false;

  function updateVolumeUI() {
    var frac = s.currentVolume;
    if (muteBtn) muteBtn.textContent = (s.video && (s.video.muted || s.video.volume === 0)) ? "🔇" : "🔊";
    if (volFill) volFill.style.width = (frac * 100) + "%";
    if (volHandle) volHandle.style.left = (frac * 100) + "%";
    if (vol) vol.setAttribute("aria-valuenow", String(frac));
  }

  core.subscribe("volumeChanged", updateVolumeUI);

  function volFromX(clientX) {
    if (!vol) return s.currentVolume;
    var rect = vol.getBoundingClientRect();
    if (rect.width <= 0) return s.currentVolume;
    return (clientX - rect.left) / rect.width;
  }

  if (vol) {
    core.on(vol, "pointerdown", function (ev) {
      if (ev.button !== undefined && ev.button !== 0) return;
      scrubbingVol = true;
      if (vol.setPointerCapture) try { vol.setPointerCapture(ev.pointerId); } catch (e) {}
      ev.preventDefault(); ev.stopPropagation();
      core.setVolumeFraction(volFromX(ev.clientX));
    });
    core.on(vol, "pointermove", function (ev) {
      if (!scrubbingVol) return;
      core.setVolumeFraction(volFromX(ev.clientX));
    });
    core.on(vol, "pointerup", function () {
      scrubbingVol = false;
      try { localStorage.setItem("aem_volume", String(s.currentVolume)); } catch (e) {}
    });
    core.on(vol, "pointercancel", function () { scrubbingVol = false; });
    updateVolumeUI();
  }

  if (muteBtn) {
    core.on(muteBtn, "click", function (e) {
      e.stopPropagation();
      if (s.video.muted || s.video.volume === 0) {
        s.video.muted = false;
        core.setVolumeFraction(s.lastVolume > 0 ? s.lastVolume : 0.7);
      } else {
        s.lastVolume = s.video.volume;
        s.video.muted = true;
        core.setVolumeFraction(0);
      }
    });
  }
}

function bindFullscreen() {
  var fsBtn = core.qs("pc-fullscreen");
  if (fsBtn) {
    core.on(fsBtn, "click", function (e) {
      e.stopPropagation();
      if (document.fullscreenElement) document.exitFullscreen();
      else if (s.shell.requestFullscreen) s.shell.requestFullscreen();
    });
  }
}

function bindTheater() {
  var theaterBtn = core.qs("pc-theater-btn");
  function toggleTheater() {
    s.isTheater = !s.isTheater;
    s.shell.classList.toggle("theater", s.isTheater);
    var layout = document.querySelector(".watch-layout");
    if (layout) layout.classList.toggle("theater", s.isTheater);
    if (theaterBtn) theaterBtn.classList.toggle("active", s.isTheater);
  }
  if (theaterBtn) core.on(theaterBtn, "click", function (e) { e.stopPropagation(); toggleTheater(); });
  core.toggleTheater = toggleTheater;
}

function bindPiP() {
  var pipBtn = core.qs("pc-pip-btn");
  if (pipBtn) {
    core.on(pipBtn, "click", function (e) {
      e.stopPropagation();
      if (document.pictureInPictureElement) document.exitPictureInPicture().catch(function () {});
      else if (s.video.requestPictureInPicture) s.video.requestPictureInPicture().catch(function () {});
    });
  }
}

function bindSettingsMenu() {
  var btn = core.qs("pc-settings-btn");
  var dropdown = core.qs("pc-settings-dropdown");
  if (!btn || !dropdown) return;

  core.on(btn, "click", function (e) {
    e.stopPropagation();
    dropdown.classList.toggle("open");
  });
  core.on(document, "click", function (e) {
    if (!dropdown.contains(e.target) && e.target !== btn) dropdown.classList.remove("open");
  });
}

function showControlsBrief() {
  s.shell.classList.add("controls-visible");
  s.shell.classList.remove("controls-hidden");
  if (s.hideTimer) clearTimeout(s.hideTimer);
  s.hideTimer = setTimeout(function () {
    s.shell.classList.remove("controls-visible");
  }, 2500);
}

function setupDoubleTap(leftEl, rightEl) {
  var lastLeft = 0, lastRight = 0, WINDOW = 350;
  function flash(text, x, y) {
    var f = document.createElement("div");
    f.className = "pc-dt-hint";
    f.textContent = text;
    f.style.position = "absolute";
    f.style.left = x || "50%";
    f.style.top = y || "50%";
    f.style.transform = "translate(-50%,-50%)";
    f.style.padding = "8px 10px";
    f.style.background = "rgba(0,0,0,0.6)";
    f.style.color = "#fff";
    f.style.borderRadius = "6px";
    f.style.fontSize = "14px";
    f.style.fontWeight = "600";
    f.style.pointerEvents = "none";
    f.style.zIndex = "20";
    s.shell.appendChild(f);
    requestAnimationFrame(function () {
      f.style.transition = "opacity .2s, transform .2s";
      f.style.opacity = "1";
      f.style.transform = "translate(-50%,-60%)";
    });
    setTimeout(function () { f.remove(); }, 700);
  }

  function togglePlaySilent() {
    if (!s.video) return;
    if (s.video.paused) s.video.play().catch(function () {}); else s.video.pause();
  }

  leftEl.addEventListener("pointerup", function (ev) {
    ev.stopPropagation(); ev.preventDefault();
    var now = Date.now();
    if (now - lastLeft <= WINDOW) {
      if (s.video) s.video.currentTime = Math.max(0, (s.video.currentTime || 0) - 10);
      flash("−10s", ev.clientX + "px", ev.clientY + "px");
      lastLeft = 0;
    } else {
      lastLeft = now;
      setTimeout(function () {
        if (Date.now() - lastLeft >= WINDOW) { togglePlaySilent(); lastLeft = 0; }
      }, WINDOW + 20);
    }
  });

  rightEl.addEventListener("pointerup", function (ev) {
    ev.stopPropagation(); ev.preventDefault();
    var now = Date.now();
    if (now - lastRight <= WINDOW) {
      if (s.video && s.video.duration) s.video.currentTime = Math.min(s.video.duration, s.video.currentTime + 10);
      flash("+10s", ev.clientX + "px", ev.clientY + "px");
      lastRight = 0;
    } else {
      lastRight = now;
      setTimeout(function () {
        if (Date.now() - lastRight >= WINDOW) { togglePlaySilent(); lastRight = 0; }
      }, WINDOW + 20);
    }
  });
}

export function initControls() {
  buildShell();
  initSourceSelect();
  bindPlayback();
  bindTimeline();
  bindVolume();
  bindFullscreen();
  bindTheater();
  bindPiP();
  bindSettingsMenu();

  core.on("manifestParsed", function (source) {
    try { populateHlsLevels(source); } catch (e) {}
  });
}

export { showControlsBrief, populateHlsLevels };
