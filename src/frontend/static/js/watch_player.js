(function () {
  const config = window.AEMWatchPage;
  if (!config) {
    return;
  }

  const playerShell = document.getElementById("watch-player-shell");
  const playerOverlay = document.getElementById("watch-player-overlay");
  const video = document.getElementById("watch-video");
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
  const addSourceForm = document.getElementById("add-source-form");
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

  const getSourcesByTranslation = (translationId) =>
    allSources
      .filter((item) => String(item.translation_id) === String(translationId))
      .sort(
        (left, right) =>
          getQualityRank(right.quality_label) -
          getQualityRank(left.quality_label),
      );

  const setPlayerVisualState = () => {
    if (!playerShell || !video) {
      return;
    }
    playerShell.classList.toggle("is-playing", !video.paused);
    playerShell.classList.toggle("is-paused", video.paused);
    if (playToggle) {
      playToggle.textContent = video.paused ? "▶" : "II";
      playToggle.setAttribute("aria-label", video.paused ? "Play" : "Pause");
    }
    if (muteToggle) {
      muteToggle.textContent = video.muted || video.volume === 0 ? "🔇" : "🔊";
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
    if (video && !video.paused) {
      hideControlsTimer = window.setTimeout(() => {
        playerShell.classList.add("is-controls-hidden");
      }, 2600);
    }
  };

  const seekTo = (value) => {
    if (!video) {
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
    if (!video) {
      return;
    }
    const duration = Number(video.duration || 0);
    if (timelineRange) {
      timelineRange.max = duration > 0 ? String(duration) : "100";
      if (!isScrubbing) {
        timelineRange.value = String(video.currentTime || 0);
      }
    }
    if (currentTimeLabel) {
      currentTimeLabel.textContent = formatClock(video.currentTime || 0);
    }
    if (durationTimeLabel) {
      durationTimeLabel.textContent = formatClock(duration);
    }
  };

  const saveSession = async () => {
    if (!config.isAuthenticated || !video || !config.selectedSourceId) {
      return;
    }
    await fetch(`/watch/${config.animeId}/session`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        episode: config.episode,
        watch_source_id: config.selectedSourceId,
        position_seconds: video.currentTime || 0,
        volume: video.muted ? 0 : video.volume,
        quality_label: qualitySelect
          ? qualitySelect.selectedOptions[0]?.textContent || "Auto"
          : "Auto",
        is_paused: video.paused,
      }),
    });
  };

  const togglePlayback = async () => {
    if (!video) {
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

  const setVideoSource = (sourceId) => {
    if (!video) {
      return;
    }
    const source = allSources.find(
      (item) => Number(item.source_id) === Number(sourceId),
    );
    if (!source) {
      if (hlsInstance) {
        hlsInstance.destroy();
        hlsInstance = null;
      }
      video.removeAttribute("src");
      video.load();
      return;
    }

    const currentTime = video.currentTime || config.lastPositionSeconds || 0;
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

    const streamUrl = source.stream_url;
    const isHlsStream = /\.m3u8($|\?)/i.test(streamUrl);
    if (isHlsStream && window.Hls && window.Hls.isSupported()) {
      hlsInstance = new window.Hls();
      hlsInstance.loadSource(streamUrl);
      hlsInstance.attachMedia(video);
      video.addEventListener("loadedmetadata", onLoadedMetadata, {
        once: true,
      });
    } else {
      video.src = streamUrl;
      video.load();
      video.addEventListener("loadedmetadata", onLoadedMetadata, {
        once: true,
      });
    }

    setPlayerVisualState();
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
                ${item.quality_label} • ${item.provider_name}
            </option>
        `,
      )
      .join("");

    if (!items.length) {
      qualitySelect.innerHTML = "<option value=''>Нет источников</option>";
      return;
    }

    const preferred =
      items.find((item) => item.quality_label === config.savedQualityLabel) ||
      items[0];
    qualitySelect.value = String(preferred.source_id);
    config.selectedSourceId = preferred.source_id;
    setVideoSource(preferred.source_id);
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
    if (!video) {
      return;
    }
    if (video.muted || video.volume === 0) {
      video.muted = false;
      video.volume = Number(volumeRange?.value || config.savedVolume || 1) || 1;
    } else {
      video.muted = true;
    }
    setPlayerVisualState();
    saveSession();
    showControls();
  });

  volumeRange?.addEventListener("input", () => {
    if (!video) {
      return;
    }
    const nextVolume = Number(volumeRange.value);
    video.muted = nextVolume === 0;
    video.volume = nextVolume;
    setPlayerVisualState();
    saveSession();
  });

  translationSelect?.addEventListener("change", () => {
    config.selectedTranslationId = Number(translationSelect.value);
    syncQualityOptions();
    showControls();
  });

  qualitySelect?.addEventListener("change", () => {
    config.selectedSourceId = Number(qualitySelect.value);
    setVideoSource(config.selectedSourceId);
    saveSession();
    showControls();
  });

  timelineRange?.addEventListener("input", () => {
    isScrubbing = true;
    if (currentTimeLabel) {
      currentTimeLabel.textContent = formatClock(timelineRange.value);
    }
    showControls();
  });

  timelineRange?.addEventListener("change", () => {
    isScrubbing = false;
    seekTo(timelineRange.value);
    saveSession();
  });

  highlightStartButton?.addEventListener("click", () => {
    if (!video || !highlightForm) {
      return;
    }
    highlightStart = video.currentTime || 0;
    highlightForm.elements.start_timestamp.value = formatClock(highlightStart);
    showControls();
  });

  highlightEndButton?.addEventListener("click", () => {
    if (!video || !highlightForm) {
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

  addSourceForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(addSourceForm);
    const response = await fetch(`/watch/${config.animeId}/sources`, {
      method: "POST",
      body: formData,
    });
    if (!response.ok) {
      window.alert("Не удалось сохранить источник.");
      return;
    }
    window.location.reload();
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
    if (!video || video.paused) {
      return;
    }
    playerShell.classList.add("is-controls-hidden");
  });
  playerShell?.addEventListener("dblclick", (event) => {
    if (
      event.target instanceof HTMLElement &&
      event.target.closest("button, input, select, textarea, form")
    ) {
      return;
    }
    toggleFullscreen();
  });

  video?.addEventListener("play", () => {
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

  document.addEventListener("keydown", (event) => {
    const target = event.target;
    if (
      target instanceof HTMLElement &&
      target.closest("input, textarea, select")
    ) {
      return;
    }
    if (!video) {
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

  if (video && config.lastPositionSeconds > 0) {
    video.addEventListener(
      "loadedmetadata",
      () => {
        video.currentTime = config.lastPositionSeconds;
        updateTimeline();
      },
      { once: true },
    );
  }

  if (playerShell && playerOverlay) {
    playerShell.classList.add("is-paused");
    playerShell.classList.remove("is-controls-hidden");
  }
})();
