(function () {
  const config = window.AEMWatchPage;
  if (!config) {
    return;
  }

  const playerShell = document.getElementById("watch-player-shell");
  const playerOverlay = document.getElementById("watch-player-overlay");
  const playerStatus = document.getElementById("watch-player-status");
  const playerStatusTitle = document.getElementById("watch-player-status-title");
  const playerStatusText = document.getElementById("watch-player-status-text");
  const video = document.getElementById("watch-video");
  const embedFrame = document.getElementById("watch-embed-frame");
  const externalPanel = document.getElementById("watch-external-panel");
  const externalTitle = document.getElementById("watch-external-title");
  const externalMeta = document.getElementById("watch-external-meta");
  const externalLink = document.getElementById("watch-external-link");
  const heroPlayToggle = document.getElementById("hero-play-toggle");
  const playToggle = document.getElementById("play-toggle");
  const muteToggle = document.getElementById("mute-toggle");
  const fullscreenToggle = document.getElementById("fullscreen-toggle");
  const translationSelect = document.getElementById("translation-select");
  const qualitySelect = document.getElementById("quality-select");
  const timelineRange = document.getElementById("timeline-range");
  const volumeRange = document.getElementById("volume-range");
  const currentTimeLabel = document.getElementById("current-time-label");
  const durationTimeLabel = document.getElementById("duration-time-label");
  const highlightStartButton = document.getElementById("highlight-start");
  const highlightEndButton = document.getElementById("highlight-end");
  const highlightForm = document.getElementById("watch-highlight-form");
  const episodeForm = document.getElementById("episode-form");
  const discoverSourcesButton = document.getElementById(
    "discover-sources-button",
  );
  const watchFavoriteButton = document.querySelector(".watch-favorite-button");
  const sourcesJson = document.getElementById("watch-sources-json");
  const allSources = sourcesJson
    ? JSON.parse(sourcesJson.textContent || "[]")
    : [];

  let hlsInstance = null;
  let hideControlsTimer = null;
  let highlightStart = null;
  let isScrubbing = false;

  const formatClock = (value) => {
    const totalSeconds = Math.max(Math.floor(Number(value || 0)), 0);
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;
    if (hours > 0) {
      return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
    }
    return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
  };

  const getQualityRank = (value) => {
    const match = String(value || "").match(/\d+/);
    return match ? Number(match[0]) : 0;
  };

  const parseTimestamp = (value) => {
    const text = String(value || "").trim();
    if (!text) {
      return 0;
    }
    const parts = text.split(":").map((item) => Number(item));
    if (parts.length === 3) {
      return parts[0] * 3600 + parts[1] * 60 + parts[2];
    }
    if (parts.length === 2) {
      return parts[0] * 60 + parts[1];
    }
    return Number(text) || 0;
  };

  const buildProxyUrl = (streamUrl) =>
    `/watch/proxy?url=${encodeURIComponent(String(streamUrl || "").trim())}`;

  const getPreferredStartSeconds = () =>
    Math.max(Number(config.preferredStartSeconds || 0), 0);

  const getResumePositionSeconds = () => {
    const currentTime = Number(video?.currentTime || 0);
    if (currentTime > 0) {
      return currentTime;
    }
    const preferredStart = getPreferredStartSeconds();
    if (preferredStart > 0) {
      return preferredStart;
    }
    return Math.max(Number(config.lastPositionSeconds || 0), 0);
  };

  const getSelectedSource = () =>
    allSources.find(
      (item) => Number(item.source_id) === Number(config.selectedSourceId),
    ) || null;

  const canUseNativeHls = () =>
    Boolean(
      video &&
        (video.canPlayType("application/vnd.apple.mpegurl") ||
          video.canPlayType("application/x-mpegURL")),
    );

  const isStreamSource = (source) =>
    !source || String(source.source_type || "stream") === "stream";

  const hidePlayerStatus = () => {
    if (playerStatus) {
      playerStatus.hidden = true;
    }
  };

  const showPlayerStatus = (title, text) => {
    console.warn("[WATCH_PLAYER]", title, text);
    if (playerStatusTitle) {
      playerStatusTitle.textContent = title;
    }
    if (playerStatusText) {
      playerStatusText.textContent = text;
    }
    if (playerStatus) {
      playerStatus.hidden = false;
    }
  };

  const getSourcesByTranslation = (translationId) =>
    allSources
      .filter((item) => String(item.translation_id) === String(translationId))
      .sort((left, right) => {
        const qualityDiff =
          getQualityRank(right.quality_label) - getQualityRank(left.quality_label);
        if (qualityDiff !== 0) {
          return qualityDiff;
        }
        const typePriority = {
          stream: 0,
          embed: 1,
          external: 2,
        };
        return (
          (typePriority[left.source_type || "stream"] ?? 3) -
          (typePriority[right.source_type || "stream"] ?? 3)
        );
      });

  const setPlayerVisualState = () => {
    const selectedSource = getSelectedSource();
    const streamMode = isStreamSource(selectedSource);
    if (!playerShell) {
      return;
    }
    playerShell.classList.toggle(
      "is-playing",
      Boolean(streamMode && video && !video.paused),
    );
    playerShell.classList.toggle(
      "is-paused",
      !streamMode || !video || video.paused,
    );
    playerShell.classList.toggle(
      "is-non-stream-source",
      Boolean(selectedSource && !streamMode),
    );
    if (playToggle) {
      playToggle.textContent =
        streamMode && video && !video.paused ? "II" : "▶";
      playToggle.setAttribute(
        "aria-label",
        streamMode && video && !video.paused ? "Pause" : "Play",
      );
    }
    if (muteToggle) {
      muteToggle.textContent =
        streamMode && video && !(video.muted || video.volume === 0) ? "🔊" : "🔇";
    }
  };

  const showControls = () => {
    if (!playerShell) {
      return;
    }
    playerShell.classList.remove("is-controls-hidden");
    if (hideControlsTimer) {
      window.clearTimeout(hideControlsTimer);
    }
    if (video && !video.paused && isStreamSource(getSelectedSource())) {
      hideControlsTimer = window.setTimeout(() => {
        playerShell.classList.add("is-controls-hidden");
      }, 2600);
    }
  };

  const seekTo = (value) => {
    if (!video || !isStreamSource(getSelectedSource())) {
      return;
    }
    const nextTime = Math.max(
      0,
      Math.min(Number(value || 0), Number(video.duration || 0)),
    );
    video.currentTime = nextTime;
    updateTimeline();
  };

  const updateTimeline = () => {
    if (!video || !isStreamSource(getSelectedSource())) {
      if (timelineRange) {
        timelineRange.max = "100";
        timelineRange.value = "0";
        updateTimelineProgressBar(0);
      }
      if (currentTimeLabel) {
        currentTimeLabel.textContent = "00:00";
      }
      if (durationTimeLabel) {
        durationTimeLabel.textContent = "00:00";
      }
      return;
    }
    const duration = Number(video.duration || 0);
    if (timelineRange) {
      timelineRange.max = duration > 0 ? String(duration) : "100";
      if (!isScrubbing) {
        timelineRange.value = String(video.currentTime || 0);
      }
      updateTimelineProgressBar(duration);
    }
    if (currentTimeLabel) {
      currentTimeLabel.textContent = formatClock(video.currentTime || 0);
    }
    if (durationTimeLabel) {
      durationTimeLabel.textContent = formatClock(duration);
    }
  };

  const updateTimelineProgressBar = (durationOverride) => {
    if (!timelineRange) {
      return;
    }
    const duration =
      Number(durationOverride ?? timelineRange.max ?? 0) ||
      Number(video?.duration || 0);
    const current = Number(timelineRange.value || 0);
    const ratio =
      duration > 0 ? Math.max(0, Math.min(current / duration, 1)) : 0;
    timelineRange.style.setProperty("--timeline-progress", `${ratio * 100}%`);
  };

  const updateVolumeProgressBar = () => {
    if (!volumeRange || !video) {
      return;
    }
    const value = video.muted ? 0 : Number(video.volume || 0);
    const ratio = Math.max(0, Math.min(value, 1));
    volumeRange.style.setProperty("--volume-progress", `${ratio * 100}%`);
  };

  const updateInteractionState = (source) => {
    const streamMode = isStreamSource(source);
    [playToggle, muteToggle, timelineRange, volumeRange].forEach((item) => {
      if (item) {
        item.disabled = !streamMode;
      }
    });
    [highlightStartButton, highlightEndButton].forEach((item) => {
      if (item) {
        item.disabled = !streamMode;
      }
    });
    if (heroPlayToggle) {
      heroPlayToggle.disabled = !streamMode;
    }
    setPlayerVisualState();
    updateTimeline();
  };

  const saveSession = async () => {
    const selectedSource = getSelectedSource();
    if (!config.isAuthenticated || !selectedSource) {
      return;
    }
    const streamMode = isStreamSource(selectedSource);
    await fetch(`/watch/${config.animeId}/session`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        episode: config.episode,
        watch_source_id: selectedSource.source_id,
        position_seconds: streamMode && video ? video.currentTime || 0 : 0,
        volume:
          streamMode && video ? (video.muted ? 0 : video.volume) : config.savedVolume,
        quality_label: qualitySelect
          ? qualitySelect.selectedOptions[0]?.textContent || "Auto"
          : "Auto",
        is_paused: streamMode && video ? video.paused : true,
      }),
    });
  };

  const togglePlayback = async () => {
    if (!video || !isStreamSource(getSelectedSource())) {
      return;
    }
    if (video.paused) {
      await video.play().catch(() => null);
    } else {
      video.pause();
    }
    setPlayerVisualState();
    showControls();
  };

  const toggleFullscreen = async () => {
    if (!playerShell) {
      return;
    }
    if (document.fullscreenElement) {
      await document.exitFullscreen().catch(() => null);
      return;
    }
    await playerShell.requestFullscreen?.().catch(() => null);
  };

  const clearStreamSource = () => {
    if (!video) {
      return;
    }
    if (hlsInstance) {
      hlsInstance.destroy();
      hlsInstance = null;
    }
    video.pause();
    video.removeAttribute("src");
    video.load();
    video.hidden = true;
  };

  const clearEmbedSource = () => {
    if (!embedFrame) {
      return;
    }
    embedFrame.src = "about:blank";
    embedFrame.hidden = true;
  };

  const clearExternalSource = () => {
    if (!externalPanel) {
      return;
    }
    externalPanel.hidden = true;
    if (externalLink) {
      externalLink.href = "#";
    }
  };

  const setEmbedSource = (source) => {
    clearStreamSource();
    clearExternalSource();
    hidePlayerStatus();
    if (!embedFrame) {
      return;
    }
    embedFrame.src = source.stream_url;
    embedFrame.hidden = false;
    updateInteractionState(source);
  };

  const setExternalSource = (source) => {
    clearStreamSource();
    clearEmbedSource();
    hidePlayerStatus();
    if (externalPanel) {
      externalPanel.hidden = false;
    }
    if (externalTitle) {
      externalTitle.textContent = source.translation_name || source.source_name;
    }
    if (externalMeta) {
      externalMeta.textContent = `${source.source_name} • ${source.quality_label} • ${source.provider_name}`;
    }
    if (externalLink) {
      externalLink.href = source.stream_url;
    }
    updateInteractionState(source);
  };

  const setStreamSource = (source) => {
    if (!video) {
      return;
    }
    clearEmbedSource();
    clearExternalSource();
    hidePlayerStatus();
    video.hidden = false;
    const currentTime = getResumePositionSeconds();
    if (hlsInstance) {
      hlsInstance.destroy();
      hlsInstance = null;
    }

    const onLoadedMetadata = () => {
      if (currentTime > 0) {
        video.currentTime = currentTime;
      }
      updateTimeline();
    };

    const streamUrl = String(source.stream_url || "").trim();
    if (!streamUrl) {
      showPlayerStatus(
        "Источник не найден",
        "У этой серии нет валидной ссылки на поток. Попробуй другую озвучку или обнови источники.",
      );
      updateInteractionState(null);
      return;
    }
    const isHlsStream = /\.m3u8($|\?)/i.test(streamUrl);
    const proxiedStreamUrl = buildProxyUrl(streamUrl);
    if (isHlsStream && window.Hls && window.Hls.isSupported()) {
      hlsInstance = new window.Hls();
      hlsInstance.on(window.Hls.Events.ERROR, (_event, data) => {
        console.error("[WATCH_PLAYER_HLS_ERROR]", data);
        if (!data || !data.fatal) {
          return;
        }
        const reason = [data.type, data.details].filter(Boolean).join(": ");
        showPlayerStatus(
          "Поток не открылся",
          reason
            ? `HLS ошибка: ${reason}. Попробуй другой источник или обнови список источников.`
            : "Серия не загрузилась через HLS. Попробуй другой источник или обнови список источников.",
        );
      });
      hlsInstance.loadSource(proxiedStreamUrl);
      hlsInstance.attachMedia(video);
      video.addEventListener("loadedmetadata", onLoadedMetadata, {
        once: true,
      });
    } else if (isHlsStream && !canUseNativeHls()) {
      showPlayerStatus(
        "HLS не поддерживается",
        "Браузер не смог включить поток этой серии. Локальный HLS-движок не загрузился или источник недоступен.",
      );
      updateInteractionState(null);
      return;
    } else {
      video.src = proxiedStreamUrl;
      video.load();
      video.addEventListener("loadedmetadata", onLoadedMetadata, {
        once: true,
      });
    }

    updateInteractionState(source);
  };

  const setActiveSource = (sourceId) => {
    const source = allSources.find(
      (item) => Number(item.source_id) === Number(sourceId),
    );
    if (!source) {
      clearStreamSource();
      clearEmbedSource();
      clearExternalSource();
      updateInteractionState(null);
      return;
    }

    config.selectedSourceId = source.source_id;
    config.selectedTranslationId = source.translation_id;

    if (String(source.source_type || "stream") === "embed") {
      setEmbedSource(source);
      return;
    }
    if (String(source.source_type || "stream") === "external") {
      setExternalSource(source);
      return;
    }
    setStreamSource(source);
  };

  const formatQualityOption = (item) => {
    if (String(item.source_type || "stream") === "embed") {
      return `${item.quality_label} • ${item.provider_name} • embed`;
    }
    if (String(item.source_type || "stream") === "external") {
      return `${item.quality_label} • ${item.provider_name} • open`;
    }
    return `${item.quality_label} • ${item.provider_name}`;
  };

  const syncQualityOptions = () => {
    if (!translationSelect || !qualitySelect) {
      return;
    }
    const translationId = translationSelect.value;
    const items = getSourcesByTranslation(translationId);
    qualitySelect.innerHTML = items
      .map(
        (item) => `
            <option value="${item.source_id}" ${Number(item.source_id) === Number(config.selectedSourceId) ? "selected" : ""}>
                ${formatQualityOption(item)}
            </option>
        `,
      )
      .join("");

    if (!items.length) {
      qualitySelect.innerHTML = "<option value=''>Нет источников</option>";
      setActiveSource(null);
      return;
    }

    const preferred =
      items.find((item) => item.quality_label === config.savedQualityLabel) ||
      items.find((item) => Number(item.source_id) === Number(config.selectedSourceId)) ||
      items[0];
    qualitySelect.value = String(preferred.source_id);
    config.selectedSourceId = preferred.source_id;
    setActiveSource(preferred.source_id);
  };

  const renderTranslationOptions = () => {
    if (!translationSelect) {
      return;
    }
    const seen = new Set();
    const translations = [];
    allSources.forEach((item) => {
      if (seen.has(item.translation_id)) {
        return;
      }
      seen.add(item.translation_id);
      translations.push({
        translation_id: item.translation_id,
        translation_name: item.translation_name,
      });
    });
    translationSelect.innerHTML = translations
      .map(
        (item) => `
            <option value="${item.translation_id}">${item.translation_name}</option>
        `,
      )
      .join("");
  };

  heroPlayToggle?.addEventListener("click", togglePlayback);
  playToggle?.addEventListener("click", togglePlayback);
  fullscreenToggle?.addEventListener("click", toggleFullscreen);

  muteToggle?.addEventListener("click", () => {
    if (!video || !isStreamSource(getSelectedSource())) {
      return;
    }
    if (video.muted || video.volume === 0) {
      video.muted = false;
      video.volume = Number(volumeRange?.value || config.savedVolume || 1) || 1;
    } else {
      video.muted = true;
    }
    updateVolumeProgressBar();
    setPlayerVisualState();
    saveSession();
    showControls();
  });

  volumeRange?.addEventListener("input", () => {
    if (!video || !isStreamSource(getSelectedSource())) {
      return;
    }
    const nextVolume = Number(volumeRange.value);
    video.muted = nextVolume === 0;
    video.volume = nextVolume;
    updateVolumeProgressBar();
    setPlayerVisualState();
    saveSession();
  });

  translationSelect?.addEventListener("change", () => {
    config.selectedTranslationId = Number(translationSelect.value);
    syncQualityOptions();
    saveSession();
    showControls();
  });

  qualitySelect?.addEventListener("change", () => {
    config.selectedSourceId = Number(qualitySelect.value);
    setActiveSource(config.selectedSourceId);
    saveSession();
    showControls();
  });

  timelineRange?.addEventListener("input", () => {
    if (!isStreamSource(getSelectedSource())) {
      return;
    }
    isScrubbing = true;
    if (currentTimeLabel) {
      currentTimeLabel.textContent = formatClock(timelineRange.value);
    }
    updateTimelineProgressBar();
    showControls();
  });

  timelineRange?.addEventListener("change", () => {
    if (!isStreamSource(getSelectedSource())) {
      return;
    }
    isScrubbing = false;
    seekTo(timelineRange.value);
    updateTimelineProgressBar();
    saveSession();
  });

  highlightStartButton?.addEventListener("click", () => {
    if (!video || !highlightForm || !isStreamSource(getSelectedSource())) {
      window.alert("Для этого источника таймкоды недоступны.");
      return;
    }
    highlightStart = video.currentTime || 0;
    highlightForm.elements.start_timestamp.value = formatClock(highlightStart);
    showControls();
  });

  highlightEndButton?.addEventListener("click", () => {
    if (!video || !highlightForm || !isStreamSource(getSelectedSource())) {
      window.alert("Для этого источника таймкоды недоступны.");
      return;
    }
    highlightForm.elements.end_timestamp.value = formatClock(
      video.currentTime || 0,
    );
    showControls();
  });

  highlightForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!config.isAuthenticated) {
      window.location.href = "/auth/login";
      return;
    }
    if (!isStreamSource(getSelectedSource())) {
      window.alert("Для embed и внешних источников сохранение таймкодов недоступно.");
      return;
    }
    const formData = new FormData(highlightForm);
    const startTimestamp = parseTimestamp(
      formData.get("start_timestamp") || highlightStart || 0,
    );
    const endTimestamp = parseTimestamp(
      formData.get("end_timestamp") || (video ? video.currentTime : 0),
    );
    if (endTimestamp <= startTimestamp) {
      window.alert("Конец хайлайта должен быть позже начала.");
      return;
    }
    if (!config.selectedSourceId || !config.selectedTranslationId) {
      window.alert("Сначала выбери источник и озвучку.");
      return;
    }
    const response = await fetch(`/watch/${config.animeId}/highlights`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        episode: config.episode,
        title: String(formData.get("title") || "").trim(),
        category: String(formData.get("category") || "").trim(),
        start_timestamp: startTimestamp,
        end_timestamp: endTimestamp,
        description: String(formData.get("description") || "").trim(),
        emotion: String(formData.get("emotion") || "").trim(),
        is_spoiler: Boolean(formData.get("is_spoiler")),
        watch_source_id: config.selectedSourceId,
        translation_id: config.selectedTranslationId,
      }),
    });
    if (!response.ok) {
      window.alert("Не удалось сохранить хайлайт.");
      return;
    }
    window.location.reload();
  });

  discoverSourcesButton?.addEventListener("click", async () => {
    discoverSourcesButton.disabled = true;
    const previousText = discoverSourcesButton.textContent;
    discoverSourcesButton.textContent = "Ищу источники...";
    const response = await fetch(`/watch/${config.animeId}/sources/discover`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ episode: config.episode }),
    });
    if (!response.ok) {
      window.alert("Не удалось подтянуть источники из провайдера.");
      discoverSourcesButton.disabled = false;
      discoverSourcesButton.textContent = previousText;
      return;
    }
    window.location.reload();
  });

  watchFavoriteButton?.addEventListener("click", async () => {
    if (
      !window.AEMAnimeUI ||
      typeof window.AEMAnimeUI.addFavorite !== "function"
    ) {
      return;
    }
    await window.AEMAnimeUI.addFavorite(
      watchFavoriteButton.dataset.animeId,
      watchFavoriteButton,
    );
  });

  document.querySelectorAll(".status-pill").forEach((button) => {
    button.addEventListener("click", async () => {
      const response = await fetch(`/watch/${config.animeId}/status`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: button.dataset.status }),
      });
      if (!response.ok) {
        window.alert("Не удалось обновить статус.");
        return;
      }
      document
        .querySelectorAll(".status-pill")
        .forEach((item) => item.classList.remove("is-active"));
      button.classList.add("is-active");
    });
  });

  episodeForm?.addEventListener("change", () => {
    const episodeField = document.getElementById("episode-select");
    const episode = episodeField
      ? Number(episodeField.value || config.episode)
      : config.episode;
    window.location.href = `/watch/${config.animeId}?episode=${episode}`;
  });

  playerShell?.addEventListener("mousemove", showControls);
  playerShell?.addEventListener("mouseenter", showControls);
  playerShell?.addEventListener("focusin", showControls);
  playerShell?.addEventListener("touchstart", showControls, { passive: true });
  playerShell?.addEventListener("mouseleave", () => {
    if (!video || video.paused || !isStreamSource(getSelectedSource())) {
      return;
    }
    playerShell.classList.add("is-controls-hidden");
  });
  playerShell?.addEventListener("dblclick", (event) => {
    if (
      event.target instanceof HTMLElement &&
      event.target.closest("button, input, select, textarea, form, a")
    ) {
      return;
    }
    toggleFullscreen();
  });

  video?.addEventListener("play", () => {
    hidePlayerStatus();
    setPlayerVisualState();
    showControls();
  });
  video?.addEventListener("pause", () => {
    setPlayerVisualState();
    showControls();
    saveSession();
  });
  video?.addEventListener("ended", () => {
    setPlayerVisualState();
    showControls();
    saveSession();
  });
  video?.addEventListener("timeupdate", updateTimeline);
  video?.addEventListener("durationchange", updateTimeline);
  video?.addEventListener("loadedmetadata", updateTimeline);
  video?.addEventListener("loadedmetadata", hidePlayerStatus);
  video?.addEventListener("error", () => {
    const mediaErrorCode = Number(video?.error?.code || 0);
    const mediaReasonMap = {
      1: "Загрузка видео была прервана.",
      2: "Сетевая ошибка при загрузке потока.",
      3: "Ошибка декодирования потока.",
      4: "Браузер не поддерживает формат потока.",
    };
    showPlayerStatus(
      "Видео не загрузилось",
      mediaReasonMap[mediaErrorCode] ||
        "Плеер не смог открыть поток. Попробуй сменить качество, озвучку или обновить источники.",
    );
  });

  document.addEventListener("keydown", (event) => {
    const target = event.target;
    if (
      target instanceof HTMLElement &&
      target.closest("input, textarea, select")
    ) {
      return;
    }
    if (!video || !isStreamSource(getSelectedSource())) {
      return;
    }
    if (event.code === "Space") {
      event.preventDefault();
      togglePlayback();
      return;
    }
    if (event.code === "ArrowRight") {
      event.preventDefault();
      seekTo((video.currentTime || 0) + 10);
      showControls();
      return;
    }
    if (event.code === "ArrowLeft") {
      event.preventDefault();
      seekTo((video.currentTime || 0) - 10);
      showControls();
      return;
    }
    if (event.code === "KeyM") {
      event.preventDefault();
      muteToggle?.click();
      return;
    }
    if (event.code === "KeyF") {
      event.preventDefault();
      toggleFullscreen();
    }
  });

  if (video) {
    video.volume = Number(config.savedVolume || 1);
    video.muted = video.volume === 0;
    updateVolumeProgressBar();
    window.setInterval(saveSession, 15000);
    setPlayerVisualState();
  }

  if (translationSelect) {
    renderTranslationOptions();
    const selectedTranslationId =
      config.selectedTranslationId || Number(translationSelect.value || 0);
    if (selectedTranslationId) {
      translationSelect.value = String(selectedTranslationId);
    } else if (translationSelect.options.length > 0) {
      translationSelect.value = translationSelect.options[0].value;
      config.selectedTranslationId = Number(translationSelect.value);
    }
    syncQualityOptions();
  }

  if (playerShell && playerOverlay) {
    playerShell.classList.add("is-paused");
    playerShell.classList.remove("is-controls-hidden");
  }
})();

(function () {
  const buttons = document.querySelectorAll(".anime-comment-like-button");
  if (!buttons.length) {
    return;
  }

  buttons.forEach((button) => {
    button.addEventListener("click", async () => {
      const commentId = button.getAttribute("data-comment-id");
      const liked = button.getAttribute("data-liked") === "1";
      const response = await fetch(`/watch/discussion/comments/${commentId}/likes`, {
        method: liked ? "DELETE" : "POST",
      });
      if (!response.ok) {
        return;
      }
      const payload = await response.json();
      button.setAttribute("data-liked", payload.is_liked ? "1" : "0");
      button.classList.toggle("neon-blue", Boolean(payload.is_liked));
      button.classList.toggle("neon-pink", !payload.is_liked);
      const counter = button.querySelector("span");
      if (counter) {
        counter.textContent = String(payload.likes_count || 0);
      }
    });
  });
})();
