/* Player core — state, lifecycle, event bus, utilities */
"use strict";

var cfg = window.AEMWatchPage || {};
var state = {
  cfg: cfg,
  video: null,
  hls: null,
  shell: null,
  overlay: null,
  statusText: null,
  attachedListeners: [],
  saveTimer: null,
  lastVolume: cfg.savedVolume != null ? Number(cfg.savedVolume) : 1,
  currentVolume: cfg.savedVolume != null ? Number(cfg.savedVolume) : 1,
  isTheater: false,
  hideTimer: null,
  listeners: {}
};

function on(node, event, fn) {
  if (!node || !node.addEventListener) return;
  node.addEventListener(event, fn);
  state.attachedListeners.push({ node: node, event: event, fn: fn });
}

function offAll() {
  state.attachedListeners.forEach(function (item) {
    try { item.node.removeEventListener(item.event, item.fn); } catch (e) {}
  });
  state.attachedListeners = [];
}

function teardown() {
  try { offAll(); } catch (e) {}
  try { if (state.saveTimer) { clearInterval(state.saveTimer); state.saveTimer = null; } } catch (e) {}
  try { if (state.hls) { state.hls.destroy(); state.hls = null; } } catch (e) {}
  try {
    if (state.video) {
      state.video.pause();
      state.video.removeAttribute("src");
      state.video.load();
    }
  } catch (e) {}
}

function qs(id) { return document.getElementById(id); }

function activeSource() {
  var sources = state.cfg.sources || [];
  for (var i = 0; i < sources.length; i++) {
    if (sources[i].active) return sources[i];
  }
  return sources[0] || null;
}

function setStatus(text) {
  if (state.statusText) state.statusText.textContent = text;
}

function fmtTime(t) {
  if (!isFinite(t) || t < 0) t = 0;
  var m = Math.floor(t / 60);
  var s = Math.floor(t % 60);
  return (m < 10 ? "0" : "") + m + ":" + (s < 10 ? "0" : "") + s;
}

function emit(event, data) {
  var handlers = state.listeners[event];
  if (handlers) {
    handlers.forEach(function (fn) {
      try { fn(data); } catch (e) { console.error("Player event error:", event, e); }
    });
  }
}

function subscribe(event, fn) {
  if (!state.listeners[event]) state.listeners[event] = [];
  state.listeners[event].push(fn);
}

function loadSource(source) {
  if (!source) return;
  if (state.hls) { try { state.hls.destroy(); } catch (e) {} state.hls = null; }
  state.video.pause();
  state.video.removeAttribute("src");
  state.video.load();

  if (/\.m3u8($|\?)/i.test(source.url) && window.Hls && Hls.isSupported()) {
    state.hls = new Hls();
    state.hls.loadSource(source.url);
    state.hls.attachMedia(state.video);
    state.hls.on(Hls.Events.MANIFEST_PARSED, function () {
      emit("manifestParsed", source);
    });
    state.hls.on(Hls.Events.ERROR, function (ev, data) {
      emit("hlsError", { source: source, event: ev, data: data });
    });
  } else {
    state.video.src = source.url;
  }

  try {
    var qsel = qs("pc-quality-select");
    if (qsel) qsel.disabled = !state.hls;
  } catch (e) {}

  state.video.volume = state.currentVolume;
  state.video.play().catch(function () {});
  setStatus("Смотрю");
  emit("sourceLoaded", source);
}

function switchSource(sourceId) {
  var sources = state.cfg.sources || [];
  var src = null;
  for (var i = 0; i < sources.length; i++) {
    if (String(sources[i].id) === String(sourceId)) { src = sources[i]; break; }
  }
  if (src) {
    for (var j = 0; j < sources.length; j++) sources[j].active = sources[j].id === src.id;
    try {
      localStorage.setItem("aem_src_" + state.cfg.animeId, String(src.id));
      if (src.translationId != null) localStorage.setItem("aem_dub_" + state.cfg.animeId, String(src.translationId));
    } catch (e) {}
    loadSource(src);
  }
}

function setVolumeFraction(frac) {
  frac = Math.min(1, Math.max(0, frac));
  state.currentVolume = frac;
  if (state.video) {
    state.video.volume = state.currentVolume;
    state.video.muted = state.currentVolume === 0;
  }
  emit("volumeChanged", state.currentVolume);
}

function togglePlay() {
  if (!state.video) return;
  if (state.video.paused) state.video.play().catch(function () {});
  else state.video.pause();
}

function seekBy(seconds) {
  if (!state.video || !state.video.duration) return;
  state.video.currentTime = Math.min(
    state.video.duration,
    Math.max(0, (state.video.currentTime || 0) + seconds)
  );
}

function seekToPercent(pct) {
  if (!state.video || !state.video.duration) return;
  state.video.currentTime = Math.min(
    state.video.duration,
    Math.max(0, pct * state.video.duration)
  );
}

function initCore() {
  state.shell = qs("player-shell");
  state.overlay = qs("player-overlay");
  state.statusText = qs("player-status-text");
}

var core = {
  state: state,
  cfg: cfg,
  on: on,
  offAll: offAll,
  teardown: teardown,
  qs: qs,
  activeSource: activeSource,
  setStatus: setStatus,
  fmtTime: fmtTime,
  emit: emit,
  subscribe: subscribe,
  loadSource: loadSource,
  switchSource: switchSource,
  setVolumeFraction: setVolumeFraction,
  togglePlay: togglePlay,
  seekBy: seekBy,
  seekToPercent: seekToPercent,
  initCore: initCore
};

export default core;
