/* Player select — custom dropdown used for quality and dubbing pickers.

Native <select> elements render an OS-level popup that ignores the player
theme, cannot be styled consistently and is clipped by the player shell.
This module replaces them with a button + listbox pair that follows the
player theme and stays inside the shell bounds.

The returned facade mimics the small part of the <select> API the player
relies on, so existing call sites keep reading naturally.
*/

"use strict";

import core from "./core.js";

var OPTION_ROLE = "option";

function PlayerSelect(host, settings) {
  this.host = host;
  this.id = settings.id;
  this.label = settings.label || "";
  this.placeholder = settings.placeholder || "Не выбрано";
  this.emptyText = settings.emptyText || "";
  this.onChange = settings.onChange || null;
  this.items = [];
  this.selected = null;
  this.disabled = false;
  this.open = false;
  this._build();
}

PlayerSelect.prototype._build = function () {
  this.host.className = "pc-select";
  this.host.innerHTML = "";

  var trigger = document.createElement("button");
  trigger.type = "button";
  trigger.className = "pc-select-trigger";
  trigger.setAttribute("aria-haspopup", "listbox");
  trigger.setAttribute("aria-expanded", "false");
  trigger.setAttribute("aria-label", this.label);

  var value = document.createElement("span");
  value.className = "pc-select-value";

  var caret = document.createElement("span");
  caret.className = "pc-select-caret";
  caret.setAttribute("aria-hidden", "true");
  caret.textContent = "▾";

  trigger.appendChild(value);
  trigger.appendChild(caret);
  this.host.appendChild(trigger);

  var menu = document.createElement("div");
  menu.className = "pc-select-menu";
  menu.setAttribute("role", "listbox");
  menu.setAttribute("aria-label", this.label);
  this.host.appendChild(menu);

  this.trigger = trigger;
  this.valueEl = value;
  this.menu = menu;

  core.on(trigger, "click", function (ev) {
    ev.preventDefault();
    ev.stopPropagation();
    this.toggle();
  }.bind(this));

  core.on(menu, "click", function (ev) {
    ev.stopPropagation();
    var row = ev.target.closest(".pc-select-option");
    if (!row || !this.host.contains(row)) return;
    this.select(row.getAttribute("data-value"));
  }.bind(this));

  core.on(trigger, "keydown", function (ev) { this._onKeyDown(ev); }.bind(this));

  core.on(document, "click", function () { this.close(); }.bind(this));
  core.on(document, "keydown", function (ev) {
    if (ev.key === "Escape" && this.open) this.close();
  }.bind(this));
};

PlayerSelect.prototype._onKeyDown = function (ev) {
  if (ev.key === "Escape") {
    if (this.open) { ev.preventDefault(); this.close(); }
    return;
  }
  if (ev.key === "ArrowDown" || ev.key === "Enter" || ev.key === " ") {
    ev.preventDefault();
    if (!this.open) { this.open_(); return; }
  }
  if (ev.key === "ArrowDown") this._move(1);
  if (ev.key === "ArrowUp") this._move(-1);
};

PlayerSelect.prototype._move = function (step) {
  if (!this.items.length) return;
  var index = this.items.findIndex(function (item) { return item.value === this.selected; }.bind(this));
  var next = (index + step + this.items.length) % this.items.length;
  this.select(this.items[next].value);
};

PlayerSelect.prototype.open_ = function () {
  if (this.disabled || this.open) return;
  this.open = true;
  this.host.classList.add("open");
  this.trigger.setAttribute("aria-expanded", "true");
  var active = this.menu.querySelector('[data-value="' + cssEscape(this.selected) + '"]');
  if (active) active.focus();
};

PlayerSelect.prototype.close = function () {
  if (!this.open) return;
  this.open = false;
  this.host.classList.remove("open");
  this.trigger.setAttribute("aria-expanded", "false");
};

PlayerSelect.prototype.toggle = function () {
  if (this.open) this.close();
  else this.open_();
};

PlayerSelect.prototype.setOptions = function (items, selected) {
  this.items = items.slice();
  this.menu.innerHTML = "";

  if (!this.items.length) {
    var empty = document.createElement("div");
    empty.className = "pc-select-empty";
    empty.textContent = this.emptyText;
    this.menu.appendChild(empty);
  }

  this.items.forEach(function (item) {
    var row = document.createElement("button");
    row.type = "button";
    row.className = "pc-select-option";
    row.setAttribute("role", OPTION_ROLE);
    row.setAttribute("data-value", item.value);
    if (item.disabled) row.setAttribute("disabled", "disabled");

    var label = document.createElement("span");
    label.className = "pc-select-option-label";
    label.textContent = item.label;
    row.appendChild(label);

    if (item.hint) {
      var hint = document.createElement("span");
      hint.className = "pc-select-option-hint";
      hint.textContent = item.hint;
      row.appendChild(hint);
    }

    this.menu.appendChild(row);
  }.bind(this));

  var next = selected != null ? String(selected) : null;
  if (next == null || !this._has(next)) next = this.items.length ? this.items[0].value : null;
  this._applyValue(next);
};

PlayerSelect.prototype._has = function (value) {
  return this.items.some(function (item) { return String(item.value) === String(value); });
};

PlayerSelect.prototype._applyValue = function (value) {
  this.selected = value;
  var item = this._find(value);
  this.valueEl.textContent = item ? item.label : this.placeholder;
  this.valueEl.classList.toggle("is-placeholder", !item);
  Array.prototype.forEach.call(this.menu.querySelectorAll(".pc-select-option"), function (row) {
    var active = row.getAttribute("data-value") === String(value);
    row.classList.toggle("is-active", active);
    row.setAttribute("aria-selected", active ? "true" : "false");
  });
};

PlayerSelect.prototype._find = function (value) {
  var found = null;
  this.items.forEach(function (item) {
    if (String(item.value) === String(value)) found = item;
  });
  return found;
};

PlayerSelect.prototype.select = function (value) {
  if (!this._has(value)) return;
  this.close();
  if (String(value) === String(this.selected)) return;
  this._applyValue(value);
  if (typeof this.onChange === "function") this.onChange(this.selected);
};

PlayerSelect.prototype.setDisabled = function (disabled) {
  this.disabled = Boolean(disabled);
  this.host.classList.toggle("is-disabled", this.disabled);
  this.trigger.disabled = this.disabled;
  if (this.disabled) this.close();
};

PlayerSelect.prototype.getValue = function () {
  return this.selected;
};

PlayerSelect.prototype.setValue = function (value) {
  this._applyValue(value == null ? null : String(value));
};

function cssEscape(value) {
  if (value == null) return "";
  if (window.CSS && typeof window.CSS.escape === "function") return window.CSS.escape(value);
  return String(value).replace(/["\\]/g, "\\$&");
}

export function createPlayerSelect(host, settings) {
  return new PlayerSelect(host, settings);
}