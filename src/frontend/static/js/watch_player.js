/* Anime Epic Moments — watch_player.js
   Кастомный плеер-шелл: HLS (hls.js) + iframe-эмбеды + внешние источники,
   прогресс просмотра, статус, создание хайлайтов из плеера, дискуссия. */
(function () {
  "use strict";

  var cfg = window.AEMWatchPage || {};
  var shell, overlay, statusChip, statusText;
  var video = null, hls = null;
  var controlsVisible = false;
  var saveTimer = null;
  var activeEmotion = "epic";
  var isPlaying = false;

  var EMOTIONS = ["epic", "cry", "love", "funny", "wtf", "cold", "beautiful"];

  /* ================= PLAYER CORE ================= */

  function activeSource() {
    for (var i = 0; i < cfg.sources.length; i++) {
      if (cfg.sources[i].active) return cfg.sources[i];
    }
    return cfg.sources[0] || null;
  }

  function sourceById(id) {
    for (var i = 0; i < cfg.sources.length; i++) {
      if (cfg.sources[i].id != null && cfg.sources[i].id == id) return cfg.sources[i];
    }
    return null;
  }

  function setStatus(text, cls) {
    if (statusChip) statusChip.className = "po-status-chip" + (cls ? " " + cls : "");
    if (statusText) statusText.textContent = text;
  }

  function buildStreamPlayer() {
    shell.innerHTML = "";
    var controls = document.createElement("div");
    controls.className = "player-controls";
    controls.innerHTML =
      '<div class="pc-row pc-row-timeline">' +
        '<span class="pc-time pc-time-cur" id="pc-cur">00:00</span>' +
        '<div class="pc-timeline" id="pc-timeline" role="slider" aria-label="Перемотка" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0">' +
          '<div class="pc-tl-buffer" id="pc-tl-buffer"></div>' +
          '<div class="pc-tl-fill" id="pc-tl-fill"></div>' +
          '<div class="pc-tl-handle" id="pc-tl-handle"></div>' +
        '</div>' +
        '<span class="pc-time pc-time-dur" id="pc-dur">00:00</span>' +
      '</div>' +
      '<div class="pc-row">' +
        '<button class="pc-btn" id="pc-play" aria-label="Пауза">⏸</button>' +
        '<div style="flex:1"></div>' +
        '<select class="pc-quality-select" id="pc-quality-select" aria-label="Качество"></select>' +
        '<button class="pc-btn" id="pc-mute" aria-label="Звук">🔊</button>'
        +
        '<div class="pc-volume" id="pc-volume" role="slider" aria-label="Громкость" aria-valuemin="0" aria-valuemax="1" aria-valuenow="1" title="Громкость">' +
          '<div class="pc-vol-fill" id="pc-vol-fill"></div>' +
          '<div class="pc-vol-handle" id="pc-vol-handle"></div>' +
        '</div>' +
        '<button class="pc-btn" id="pc-fullscreen" aria-label="На весь экран">⛶</button>' +
      "</div>";
    shell.appendChild(controls);
    var playCenter = document.createElement("button");
    playCenter.className = "pc-play-center";
    playCenter.id = "pc-play-center";
    playCenter.setAttribute("aria-label", "Играть");
    playCenter.textContent = "▶";
    shell.appendChild(playCenter);

    video = document.createElement("video");
    video.setAttribute("playsinline", "");
    video.setAttribute("preload", "metadata");
    video.src = "";
    shell.appendChild(video);

    controlsVisible = true;
    shell.classList.add("controls-visible");
    overlay.classList.add("hidden");
    setStatus("Загрузка источника…", "buffering");

    wireControls();
    initQualitySelect();
    loadStream();
  }

  function initQualitySelect() {
    var select = document.getElementById("pc-quality-select");
    if (!select) return;
    var active = activeSource();
    if (!active) {
      select.innerHTML = "<option>Auto</option>";
      select.disabled = true;
      return;
    }
    var options = cfg.sources.filter(function (s) {
      return (
        s.id !== active.id &&
        s.type === "stream" &&
        s.translationId != null &&
        String(s.translationId) === String(active.translationId)
      );
    });
    if (options.length === 0) {
      select.innerHTML = "<option>" + escapeHtml(active.qualityLabel || "Auto") + "</option>";
      select.disabled = true;
      return;
    }
    select.disabled = false;
    var items = cfg.sources.filter(function (s) {
      return (
        s.type === "stream" &&
        s.translationId != null &&
        String(s.translationId) === String(active.translationId)
      );
    });
    select.innerHTML = items
      .map(function (s) {
        return (
          '<option value="' + s.id + '"' + (s.id === active.id ? " selected" : "") + ">" +
          escapeHtml(s.qualityLabel || "Авто") + "</option>"
        );
      })
      .join("");
    if (select.onchange) return;
    select.addEventListener("change", function () {
      switchQuality(Number(select.value));
    });
  }

  function switchQuality(sourceId) {
    var target = sourceById(sourceId);
    if (!target || target.type !== "stream") return;
    for (var i = 0; i < cfg.sources.length; i++) {
      cfg.sources[i].active = cfg.sources[i].id === target.id;
    }
    try {
      localStorage.setItem("aem_src_" + cfg.animeId, String(target.id));
      if (target.translationId != null) {
        localStorage.setItem("aem_dub_" + cfg.animeId, String(target.translationId));
      }
    } catch (e) {}
    var select = document.getElementById("pc-quality-select");
    if (select) select.value = String(target.id);
    setStatus("Меняю качество…", "buffering");
    if (hls) {
      hls.destroy();
      hls = null;
    }
    video.removeAttribute("src");
    video.load();
    if (/\.m3u8/i.test(target.url)) {
      loadHls(target.url);
    } else {
      video.src = target.url;
      video.volume = cfg.savedVolume != null ? cfg.savedVolume : 1;
      video.play().catch(function () {});
    }
    saveProgress();
  }

  function loadStream() {
    var source = activeSource();
    if (!source) {
      setStatus("Источники не найдены");
      overlay.classList.remove("hidden");
      return;
    }
    var url = source.url;
    if (!url) {
      setStatus("У источника нет ссылки");
      return;
    }
    if (/\.m3u8($|\?)/i.test(url)) {
      loadHls(url);
    } else {
      video.src = url;
      video.currentTime = startSeconds();
      video.volume = cfg.savedVolume != null ? cfg.savedVolume : 1;
      video.play().catch(function () {});
    }
  }

  function loadHls(url) {
    if (window.Hls && Hls.isSupported()) {
      hls = new Hls({
        maxBufferLength: 30,
        startPosition: startSeconds(),
      });
      hls.loadSource(url);
      hls.attachMedia(video);
      hls.on(Hls.Events.ERROR, function (_event, data) {
        if (data && data.fatal) {
          setStatus("Ошибка потока. Попробуйте другой источник", "buffering");
        }
      });
      video.volume = cfg.savedVolume != null ? cfg.savedVolume : 1;
      video.play().catch(function () {});
    } else if (video.canPlayType("application/vnd.apple.mpegurl")) {
      video.src = url;
      video.currentTime = startSeconds();
      video.volume = cfg.savedVolume != null ? cfg.savedVolume : 1;
      video.play().catch(function () {});
    } else {
      setStatus("Ваш браузер не поддерживает HLS");
      overlay.classList.remove("hidden");
    }
  }

  function startSeconds() {
    var value = 0;
    if (cfg.lastPositionSeconds && cfg.lastPositionSeconds > 5) value = cfg.lastPositionSeconds;
    if (cfg.preferredStartSeconds && cfg.preferredStartSeconds > 0) value = cfg.preferredStartSeconds;
    return value;
  }

  function buildEmbedPlayer() {
    var source = activeSource();
    shell.innerHTML = "";
    var frame = document.createElement("iframe");
    frame.src = source ? source.url : "";
    frame.setAttribute("allowfullscreen", "");
    frame.setAttribute("allow", "autoplay; fullscreen; encrypted-media; picture-in-picture");
    frame.setAttribute("referrerpolicy", "no-referrer");
    frame.id = "embed-frame";
    shell.appendChild(frame);
    overlay.classList.add("hidden");
    setStatus("Эмбед загружается…", "buffering");
    frame.addEventListener("load", function () {
      setStatus("Эмбед-плеер");
    });
  }

  function buildExternalPlayer() {
    var source = activeSource();
    shell.innerHTML = "";
    var box = document.createElement("div");
    box.className = "player-overlay";
    box.style.position = "absolute";
    box.style.inset = "0";
    box.innerHTML =
      '<span class="po-eyebrow">внешний источник</span>' +
      '<h1 class="po-title">Просмотр в новой вкладке</h1>' +
      '<p class="po-sub">Источник ' + escapeAttr(source ? source.label : "") + " открывается у провайдера.</p>" +
      '<div class="po-actions">' +
        '<a class="btn btn-primary" href="' + escapeAttr(source ? source.url : "#") + '" target="_blank" rel="noopener nofollow">Открыть источник ↗</a>' +
        '<button class="btn btn-ghost" id="back-to-player">← Вернуться к другим источникам</button>' +
      "</div>";
    shell.appendChild(box);
    overlay.classList.add("hidden");
    setStatus("Внешний источник");
    var back = box.querySelector("#back-to-player");
    if (back) {
      back.addEventListener("click", function () {
        var fallback = null;
        for (var i = 0; i < cfg.sources.length; i++) {
          if (cfg.sources[i].type !== "external") {
            fallback = cfg.sources[i];
            break;
          }
        }
        if (fallback) {
          window.location.href =
            "/watch/" + cfg.animeId + "?episode=" + cfg.episode + "&source_id=" + fallback.id;
        }
      });
    }
  }

  function initPlayer() {
    shell = document.getElementById("player-shell");
    overlay = document.getElementById("player-overlay");
    statusChip = document.querySelector(".po-status-chip");
    statusText = document.getElementById("player-status-text");
    if (!shell) return;

    var source = activeSource();
    if (!source) {
      setStatus("Источники не найдены");
      var discover = document.getElementById("discover-btn");
      if (discover) discover.classList.remove("hidden");
      return;
    }

    var remDub = rememberedDubId();
    var remSrc = rememberedSourceId();
    if (remDub != null) {
      var groups = groupByTranslation();
      for (var i = 0; i < groups.length; i++) {
        if (groups[i].id === remDub) {
          source = groups[i].chosen;
          break;
        }
      }
    }
    if (remSrc != null) {
      var byRememberedId = sourceById(remSrc);
      if (byRememberedId) source = byRememberedId;
    }

    var firstId = cfg.sources.length ? cfg.sources[0].id : null;
    var explicit = cfg.selectedSourceId != null && cfg.selectedSourceId !== firstId;
    var hasDubChoice = groupByTranslation().length > 1;

    if (hasDubChoice && !explicit && remDub == null) {
      buildDubPicker();
      return;
    }

    overlay.classList.add("hidden");
    if (source.type === "embed") buildEmbedPlayer();
    else if (source.type === "external") buildExternalPlayer();
    else buildStreamPlayer();
    bindShellCommon();
  }

  function rememberedDubId() {
    if (!("localStorage" in window)) return null;
    try {
      var value = localStorage.getItem("aem_dub_" + cfg.animeId);
      return value != null && value !== "" ? String(value) : null;
    } catch (e) {
      return null;
    }
  }

  function rememberedSourceId() {
    if (!("localStorage" in window)) return null;
    try {
      var value = localStorage.getItem("aem_src_" + cfg.animeId);
      return value != null && value !== "" ? String(value) : null;
    } catch (e) {
      return null;
    }
  }

  function groupByTranslation() {
    var order = [];
    var map = {};
    cfg.sources.forEach(function (s) {
      var key = s.translationId != null && s.translationId !== "" ? String(s.translationId) : "src:" + s.id;
      if (!map[key]) {
        var group = {
          id: key,
          name: s.translationName || s.label || "Источник",
          sources: [],
          sample: s,
          chosen: s,
        };
        map[key] = group;
        order.push(group);
      }
      map[key].sources.push(s);
    });
    order.forEach(function (group) {
      group.count = group.sources.length;
      group.sample = group.sources[0];
      group.badge = group.sample.qualityLabel ? String(group.sample.qualityLabel) : null;
      group.provider = group.sample.providerName ? String(group.sample.providerName) : null;
      var activeOf = null;
      for (var i = 0; i < group.sources.length; i++) {
        if (group.sources[i].active) { activeOf = group.sources[i]; break; }
      }
      group.chosen = activeOf || group.sample;
    });
    return order;
  }

  function buildDubPicker() {
    if (!overlay) return;
    var groups = groupByTranslation();
    if (!groups.length) return;
    var box = document.createElement("div");
    box.className = "pc-dub-picker";
    box.id = "pc-dub-picker";
    var items = groups
      .map(function (group) {
        var isActive = group.chosen && group.chosen.active;
        var meta = "";
        if (group.badge) meta += '<span class="pc-dub-chip">' + escapeHtml(group.badge) + "</span>";
        if (group.provider) meta += '<span class="pc-dub-chip pc-dub-chip-soft">' + escapeHtml(group.provider) + "</span>";
        return (
          '<button type="button" class="pc-dub-option' + (isActive ? " is-active" : "") + '" data-dub-id="' + escapeAttr(group.id) + '">' +
          '<span class="pc-dub-icon">🎙️</span>' +
          '<span class="pc-dub-body">' +
            '<span class="pc-dub-name">' + escapeHtml(group.name) + "</span>" +
            '<span class="pc-dub-meta">' + meta + "</span>" +
          "</span>" +
          '<span class="pc-dub-count">' + group.count + "</span>" +
          "</button>"
        );
      })
      .join("");
    box.innerHTML =
      '<span class="po-eyebrow">выбери озвучку</span>' +
      '<h3 class="pc-dub-title">С чего начнём?</h3>' +
      '<p class="pc-dub-sub">Кликни по озвучке, чтобы начать. Выбор запомнится — менять можно во вкладке «Источники».</p>' +
      '<div class="pc-dub-list">' + items + "</div>";
    box.addEventListener("click", function (event) {
      var btn = event.target && event.target.closest ? event.target.closest("[data-dub-id]") : null;
      if (!btn) return;
      selectDub(String(btn.getAttribute("data-dub-id")));
    });
    overlay.appendChild(box);
    overlay.classList.remove("hidden");
  }

  function selectDub(dubId) {
    var groups = groupByTranslation();
    var group = null;
    for (var i = 0; i < groups.length; i++) {
      if (groups[i].id === dubId) { group = groups[i]; break; }
    }
    if (!group) return;
    var chosen = group.chosen;
    for (var j = 0; j < cfg.sources.length; j++) {
      cfg.sources[j].active = cfg.sources[j].id === chosen.id;
    }
    try {
      localStorage.setItem("aem_dub_" + cfg.animeId, dubId);
      localStorage.setItem("aem_src_" + cfg.animeId, String(chosen.id));
    } catch (e) {}
    var picker = document.getElementById("pc-dub-picker");
    if (picker && picker.parentNode) picker.parentNode.removeChild(picker);
    overlay.classList.add("hidden");
    setStatus("Загрузка источника…", "buffering");
    if (chosen.type === "embed") buildEmbedPlayer();
    else if (chosen.type === "external") buildExternalPlayer();
    else buildStreamPlayer();
    bindShellCommon();
  }

  /* ================= СТРИМ-КОНТРОЛЬ ================= */

  function fmtTime(seconds) {
    if (!isFinite(seconds) || seconds < 0) seconds = 0;
    var m = Math.floor(seconds / 60);
    var s = Math.floor(seconds % 60);
    return (m < 10 ? "0" : "") + m + ":" + (s < 10 ? "0" : "") + s;
  }

  function wireControls() {
    var playBtn = document.getElementById("pc-play");
    var playCenter = document.getElementById("pc-play-center");
    var timeline = document.getElementById("pc-timeline");
    var tlFill = document.getElementById("pc-tl-fill");
    var tlBuffer = document.getElementById("pc-tl-buffer");
    var tlHandle = document.getElementById("pc-tl-handle");
    var vol = document.getElementById("pc-volume");
    var volFill = document.getElementById("pc-vol-fill");
    var volHandle = document.getElementById("pc-vol-handle");
    var muteBtn = document.getElementById("pc-mute");
    var fullBtn = document.getElementById("pc-fullscreen");
    var scrubbing = false;

    function setTimelineFrame(pct) {
      pct = Math.min(1, Math.max(0, pct));
      if (tlFill) tlFill.style.width = pct * 100 + "%";
      if (tlHandle) tlHandle.style.left = pct * 100 + "%";
    }

    function pctFromX(clientX) {
      if (!timeline) return 0;
      var rect = timeline.getBoundingClientRect();
      if (rect.width <= 0) return 0;
      return (clientX - rect.left) / rect.width;
    }

    function seekFraction(pct) {
      if (!video || !video.duration) return;
      var time = pct * video.duration;
      if (isFinite(time) && time >= 0) video.currentTime = Math.min(time, video.duration);
    }

    function togglePlay() {
      if (video.paused) {
        video.play().catch(function () {});
      } else {
        video.pause();
      }
    }

    if (playBtn) playBtn.addEventListener("click", togglePlay);
    if (playCenter) playCenter.addEventListener("click", togglePlay);
    shell.addEventListener("click", function (event) {
      if (event.target === shell || event.target === video) togglePlay();
    });

    video.addEventListener("play", function () {
      isPlaying = true;
      shell.classList.add("playing");
      if (playBtn) playBtn.textContent = "⏸";
      setStatus("Смотрю");
      startSaveLoop();
    });
    video.addEventListener("pause", function () {
      isPlaying = false;
      shell.classList.remove("playing");
      if (playBtn) playBtn.textContent = "▶";
      setStatus("На паузе");
      saveProgress();
    });
    video.addEventListener("waiting", function () {
      setStatus("Буферизация…", "buffering");
    });
    video.addEventListener("playing", function () {
      setStatus("Смотрю");
    });
    video.addEventListener("ended", function () {
      isPlaying = false;
      shell.classList.remove("playing");
      if (playBtn) playBtn.textContent = "↻";
    });
    video.addEventListener("error", function () {
      setStatus("Не удалось воспроизвести этот источник", "buffering");
    });

    video.addEventListener("loadedmetadata", function () {
      var queue = startSeconds();
      if (queue > 0.5 && video.duration > queue + 2) video.currentTime = queue;
      syncTimeline();
    });
    video.addEventListener("timeupdate", function () {
      if (!video.duration) return;
      syncTimeline();
    });
    video.addEventListener("progress", syncTimeline);

    function syncTimeline() {
      var cur = document.getElementById("pc-cur");
      var dur = document.getElementById("pc-dur");
      if (cur) cur.textContent = fmtTime(video.currentTime);
      if (dur) dur.textContent = fmtTime(video.duration);
      var pct = video.duration ? video.currentTime / video.duration : 0;
      if (!scrubbing) setTimelineFrame(pct);
      if (tlBuffer && video.buffered && video.buffered.length) {
        var bufferedEnd = video.buffered.end(video.buffered.length - 1);
        var bp = video.duration ? bufferedEnd / video.duration : 0;
        tlBuffer.style.width = Math.min(100, bp * 100) + "%";
      }
    }

    if (timeline) {
      timeline.addEventListener("pointerdown", function (event) {
        if (event.button !== undefined && event.button !== 0) return;
        scrubbing = true;
        if (timeline.setPointerCapture) {
          try { timeline.setPointerCapture(event.pointerId); } catch (e) {}
        }
        event.preventDefault();
        var pct = pctFromX(event.clientX);
        setTimelineFrame(pct);
        seekFraction(pct);
      });
      timeline.addEventListener("pointermove", function (event) {
        if (!scrubbing) return;
        var pct = pctFromX(event.clientX);
        setTimelineFrame(pct);
        seekFraction(pct);
      });
      function endScrub(event) {
        if (!scrubbing) return;
        scrubbing = false;
        var pct = pctFromX(event.clientX);
        setTimelineFrame(pct);
        seekFraction(pct);
        saveProgress();
      }
      timeline.addEventListener("pointerup", endScrub);
      timeline.addEventListener("pointercancel", function () { scrubbing = false; });
    }

    var scrubbingVol = false;
    var currentVolume = cfg.savedVolume != null ? Number(cfg.savedVolume) : 1;
    if (!isFinite(currentVolume)) currentVolume = 1;
    currentVolume = Math.min(1, Math.max(0, currentVolume));
    var lastVolume = currentVolume;

    function setVolumeFraction(frac) {
      frac = Math.min(1, Math.max(0, frac));
      currentVolume = frac;
      if (video) {
        video.volume = currentVolume;
        video.muted = currentVolume === 0;
      }
      if (muteBtn) muteBtn.textContent = video && (video.muted || video.volume === 0) ? "🔇" : "🔊";
      if (volFill) volFill.style.width = currentVolume * 100 + "%";
      if (volHandle) volHandle.style.left = currentVolume * 100 + "%";
      if (vol) vol.setAttribute("aria-valuenow", String(currentVolume));
    }

    function volFromX(clientX) {
      if (!vol) return currentVolume;
      var rect = vol.getBoundingClientRect();
      if (rect.width <= 0) return currentVolume;
      return (clientX - rect.left) / rect.width;
    }

    if (vol) {
      vol.addEventListener("pointerdown", function (event) {
        if (event.button !== undefined && event.button !== 0) return;
        scrubbingVol = true;
        if (vol.setPointerCapture) {
          try { vol.setPointerCapture(event.pointerId); } catch (e) {}
        }
        event.preventDefault();
        setVolumeFraction(volFromX(event.clientX));
      });
      vol.addEventListener("pointermove", function (event) {
        if (!scrubbingVol) return;
        setVolumeFraction(volFromX(event.clientX));
      });
      function endVolume(event) {
        scrubbingVol = false;
        setVolumeFraction(volFromX(event.clientX));
        try { localStorage.setItem("aem_volume", String(currentVolume)); } catch (e) {}
      }
      vol.addEventListener("pointerup", endVolume);
      vol.addEventListener("pointercancel", function () { scrubbingVol = false; });
      setVolumeFraction(currentVolume);
    }
    if (muteBtn) {
      muteBtn.addEventListener("click", function () {
        if (!video) return;
        if (video.muted) {
          video.muted = false;
          setVolumeFraction(lastVolume > 0 ? lastVolume : 0.7);
        } else {
          lastVolume = currentVolume;
          video.muted = true;
          setVolumeFraction(0);
        }
        muteBtn.textContent = video.muted ? "🔇" : "🔊";
      });
    }
    if (fullBtn) {
      fullBtn.addEventListener("click", function () {
        if (document.fullscreenElement) {
          document.exitFullscreen();
        } else if (shell.requestFullscreen) {
          shell.requestFullscreen();
        }
      });
    }

    shell.addEventListener("click", function () {
      shell.classList.add("controls-visible");
    });
    var hideTimer = null;
    shell.addEventListener("mousemove", function () {
      shell.classList.add("controls-visible");
      if (hideTimer) clearTimeout(hideTimer);
      hideTimer = setTimeout(function () {
        if (isPlaying) shell.classList.remove("controls-visible");
      }, 2600);
    });

    document.addEventListener("keydown", function (event) {
      if (!video) return;
      var tag = event.target && event.target.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;
      if (event.code === "ArrowLeft" || event.code === "ArrowRight") {
        event.preventDefault();
        var delta = event.code === "ArrowRight" ? 10 : -10;
        var next = video.currentTime + delta;
        var max = video.duration || Infinity;
        if (next < 0) next = 0;
        if (next > max) next = max;
        video.currentTime = next;
      }
    });
  }

  function bindShellCommon() {
    var highlightBtn = document.getElementById("open-highlight-form-btn");
    if (highlightBtn) {
      highlightBtn.addEventListener("click", function () {
        var tab = document.querySelector('[data-tab="highlights"]');
        if (tab) tab.click();
        var panel = document.querySelector('[data-tab-content="highlights"]');
        if (panel) {
          panel.scrollIntoView({ behavior: "smooth", block: "center" });
        }
      });
    }
  }

  /* ================= ПРОГРЕСС ================= */

  function startSaveLoop() {
    if (!cfg.isAuthenticated) return;
    if (saveTimer) clearInterval(saveTimer);
    saveTimer = setInterval(saveProgress, 10000);
    window.addEventListener("beforeunload", saveProgress);
  }

  function saveProgress() {
    if (!cfg.isAuthenticated || !video || !video.duration) return;
    var source = activeSource();
    var body = {
      episode: cfg.episode,
      watch_source_id: source ? source.id : null,
      position_seconds: Math.round(video.currentTime),
      volume: video.volume,
      quality_label: cfg.savedQualityLabel || "Auto",
      is_paused: video.paused,
    };
    AEM.api("/watch/" + cfg.animeId + "/session", { method: "POST", body: body }).catch(function () {});
  }

  /* ================= СТАТУС ПРОСМОТРА ================= */

  function initStatus() {
    var select = document.getElementById("status-select");
    if (!select || !cfg.isAuthenticated) return;
    select.addEventListener("change", function () {
      var value = select.value;
      AEM.api("/watch/" + cfg.animeId + "/status", {
        method: "POST",
        body: { status: value },
      })
        .then(function () {
          AEM.toast("Статус сохранён", "success");
        })
        .catch(function () {
          AEM.toast("Не удалось сохранить статус", "error");
        });
    });
  }

  function initFavoriteBadge() {
    var btn = document.getElementById("favorite-badge-btn");
    if (!btn) return;
    btn.addEventListener("click", function () {
      if (!cfg.isAuthenticated) {
        window.location.href = "/auth/login";
        return;
      }
      AEM.api("/favorites/", {
        method: "POST",
        body: {
          user_id: cfg.currentUserId,
          anime_id: cfg.animeId,
          title: cfg.animeTitle || "",
          description: "",
          cover_url: cfg.coverUrl || null,
          genres: cfg.genres || [],
        },
      })
        .then(function () {
          AEM.toast("Добавлено в избранное", "success");
          btn.classList.add("active");
        })
        .catch(function () {
          AEM.toast("Не удалось добавить в избранное", "error");
        });
    });
  }

  /* ================= ХАЙЛАЙТ ИЗ ПЛЕЕРА ================= */

  function initHighlightForm() {
    var form = document.getElementById("highlight-form");
    if (!form || !cfg.isAuthenticated) return;

    form.querySelectorAll(".hf-emotion").forEach(function (btn) {
      btn.addEventListener("click", function () {
        activeEmotion = btn.getAttribute("data-emotion");
        form.querySelectorAll(".hf-emotion").forEach(function (other) {
          other.style.borderColor = "";
        });
        btn.style.borderColor = "var(--color-accent)";
      });
    });

    var startInput = document.getElementById("hf-start");
    var endInput = document.getElementById("hf-end");
    if (startInput) startInput.value = video ? fmtTime(video.currentTime) : "00:00";

    function snapshot() {
      if (!video) return;
      var cur = fmtTime(video.currentTime);
      if (startInput) startInput.value = cur;
      if (endInput) endInput.value = fmtTime(video.currentTime + 10);
    }
    var snapBtn = document.createElement("button");
    snapBtn.type = "button";
    snapBtn.className = "btn btn-ghost btn-sm";
    snapBtn.textContent = "⏱ Взять текущий момент";
    snapBtn.style.marginTop = "-4px";
    if (form.querySelector(".hf-time-row")) {
      form.querySelector(".hf-time-row").parentNode.insertBefore(
        snapBtn,
        form.querySelector(".hf-time-row").nextSibling
      );
    }
    snapBtn.addEventListener("click", snapshot);

    form.addEventListener("submit", function (event) {
      event.preventDefault();
      var source = activeSource();
      var body = {
        episode: cfg.episode,
        start_timestamp: parseTime(startInput ? startInput.value : ""),
        end_timestamp: parseTime(endInput ? endInput.value : ""),
        title: document.getElementById("hf-title").value.trim(),
        description: document.getElementById("hf-description").value.trim(),
        emotion: activeEmotion,
        is_spoiler: document.getElementById("hf-spoiler").checked,
        watch_source_id: source ? source.id : null,
        translation_id: null,
      };
      AEM.api("/watch/" + cfg.animeId + "/highlights", { method: "POST", body: body })
        .then(function (result) {
          AEM.toast("Момент сохранён! 🎉", "success");
          form.reset();
          if (result && result.highlight_id) {
            var sel = document.querySelector('[data-tab="highlights"]');
            if (sel) sel.click();
          }
        })
        .catch(function (err) {
          AEM.toast(
            err && err.message ? "Не удалось сохранить: " + err.message : "Не удалось сохранить момент",
            "error"
          );
        });
    });
  }

  function parseTime(value) {
    var text = String(value || "").trim();
    if (/^\d+:\d{2}$/.test(text)) {
      var parts = text.split(":");
      return Number(parts[0]) * 60 + Number(parts[1]);
    }
    var num = Number(text);
    return isNaN(num) ? 0 : num;
  }

  /* ================= ДИСКУССИЯ ================= */

  function initDiscussion() {
    var form = document.getElementById("discussion-form");
    var list = document.getElementById("discussion-list");
    if (!form || !list || !cfg.isAuthenticated) return;

    form.addEventListener("submit", function (event) {
      event.preventDefault();
      var input = document.getElementById("discussion-input");
      var content = input.value.trim();
      if (!content) return;
      AEM.api("/watch/" + cfg.animeId + "/discussion", {
        method: "POST",
        body: { content: content },
      })
        .then(function (comment) {
          input.value = "";
          var empty = document.getElementById("discussion-empty");
          if (empty) empty.remove();
          var item = document.createElement("div");
          item.className = "discussion-item";
          item.setAttribute("data-comment-id", comment.id);
          item.innerHTML =
            '<div class="di-head"><strong class="di-username">' + escapeHtml(comment.username) +
            '</strong><span class="di-time">только что</span></div>' +
            '<p class="di-content">' + escapeHtml(comment.content) + "</p>" +
            '<button class="di-like" data-comment-id="' + comment.id +
            '">❤️ <span class="like-count">0</span></button>';
          list.appendChild(item);
          bindLike(item.querySelector(".di-like"));
          list.scrollTop = list.scrollHeight;
        })
        .catch(function () {
          AEM.toast("Не удалось отправить комментарий", "error");
        });
    });

    list.querySelectorAll(".di-like").forEach(bindLike);
  }

  function bindLike(btn) {
    if (!btn) return;
    btn.addEventListener("click", function () {
      if (!cfg.isAuthenticated) {
        window.location.href = "/auth/login";
        return;
      }
      var id = btn.getAttribute("data-comment-id");
      var liked = btn.classList.contains("liked");
      var method = liked ? "DELETE" : "POST";
      AEM.api("/watch/discussion/comments/" + id + "/likes", { method: method })
        .then(function (result) {
          btn.classList.toggle("liked", !liked);
          var count = btn.querySelector(".like-count");
          if (count) count.textContent = liked ? Math.max(0, Number(count.textContent) - 1) : Number(count.textContent) + 1;
        })
        .catch(function () {
          AEM.toast("Не удалось обновить лайк", "error");
        });
    });
  }

  /* ================= ВКЛАДКИ САЙДБАРА ================= */
  function initTabs() {
    var tabs = document.querySelectorAll(".tab-btn");
    tabs.forEach(function (btn) {
      btn.addEventListener("click", function () {
        tabs.forEach(function (other) { other.classList.remove("active"); });
        btn.classList.add("active");
        document.querySelectorAll("[data-tab-content]").forEach(function (panel) {
          panel.classList.toggle("active", panel.getAttribute("data-tab-content") === btn.getAttribute("data-tab"));
        });
      });
    });
  }

  /* ================= DISCOVERY ================= */
  function initDiscover() {
    var btn = document.getElementById("discover-btn");
    if (!btn) return;
    btn.addEventListener("click", function () {
      btn.disabled = true;
      var original = btn.textContent;
      btn.textContent = "Ищем источники…";
      AEM.api("/watch/" + cfg.animeId + "/sources/discover", {
        method: "POST",
        body: { episode: cfg.episode },
      })
        .then(function (result) {
          var count = result && result.sources_count ? Number(result.sources_count) : 0;
          btn.disabled = false;
          btn.textContent = original;
          if (count > 0) {
            AEM.toast("Источники найдены: " + count + ". Обновляем…", "success");
            window.location.reload();
          } else {
            AEM.toast("Источники не найдены. Попробуйте позже или проверьте название", "error");
          }
        })
        .catch(function (err) {
          btn.disabled = false;
          btn.textContent = original;
          var message = err && err.error ? err.error : "";
          if (message === "no_sources_found") {
            AEM.toast("Провайдер не нашёл источники для этого тайтла", "error");
          } else if (message === "provider_timeout") {
            AEM.toast("Провайдер не ответил вовремя, попробуйте ещё раз", "error");
          } else {
            AEM.toast("Источники пока не найдены", "error");
          }
        });
    });
  }

  function escapeHtml(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }
  function escapeAttr(value) {
    return escapeHtml(value).replace(/'/g, "&#39;");
  }

  document.addEventListener("DOMContentLoaded", function () {
    initTabs();
    initDiscover();
    initStatus();
    initHighlightForm();
    initDiscussion();
    initPlayer();
  });
})();