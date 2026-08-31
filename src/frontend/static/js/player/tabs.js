/* Watch page tabs — "Источники / Серии / Моменты / Обсуждение" switching */
"use strict";

export function initWatchTabs() {
  var tabButtons = document.querySelectorAll(".tab-btn[data-tab]");
  var tabContents = document.querySelectorAll(".tab-content[data-tab-content]");

  function selectTab(name) {
    tabButtons.forEach(function (btn) {
      var active = btn.getAttribute("data-tab") === name;
      btn.classList.toggle("active", active);
      btn.setAttribute("aria-selected", active ? "true" : "false");
    });
    tabContents.forEach(function (content) {
      content.classList.toggle("active", content.getAttribute("data-tab-content") === name);
    });
  }

  tabButtons.forEach(function (btn) {
    btn.addEventListener("click", function () {
      var name = btn.getAttribute("data-tab");
      if (name) selectTab(name);
    });
    var isActive = btn.classList.contains("active");
    btn.setAttribute("aria-selected", isActive ? "true" : "false");
  });
}
