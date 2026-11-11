(() => {
  const pop = document.querySelector("#connector-tooltip");
  const triggerSelector = "[data-connector]";
  let active = null;
  let pinned = false;
  let blocked = null;
  let pending;

  function clear() {
    clearTimeout(pending);
    if (active) active.removeAttribute("aria-describedby");
    active = null;
    pinned = false;
    pop.hidden = true;
  }

  function position() {
    if (!active || !active.getClientRects().length) return clear();
    const bounds = active.getBoundingClientRect();
    const canvas = active.closest(".inline-canvas")?.getBoundingClientRect();
    const margin = 8;
    const width = document.documentElement.clientWidth;
    const height = window.innerHeight;
    if (bounds.bottom < 0 || bounds.top > height ||
        (canvas && (bounds.right < canvas.left || bounds.left > canvas.right))) return clear();
    const left = Math.max(margin, Math.min(bounds.left, width - pop.offsetWidth - margin));
    const below = bounds.bottom + 5;
    const top = below + pop.offsetHeight <= height - margin ?
      below : Math.max(margin, bounds.top - pop.offsetHeight - 5);
    pop.style.left = left + "px";
    pop.style.top = top + "px";
  }

  function open(trigger) {
    if (trigger === blocked || (pinned && active !== trigger)) return;
    clearTimeout(pending);
    if (active === trigger) return;
    clear();
    const entry = trigger.closest(".view-panel").querySelector(
      '[data-connector-key="' + trigger.dataset.connector + '"]');
    const detail = entry.querySelector("div");
    const text = detail.querySelector("p");
    const primary = detail.querySelector("strong");
    pop.querySelector(".connector-title").textContent =
      trigger.dataset.connector + " · " + (text ? primary : detail.querySelector(".route")).textContent;
    pop.querySelector(".connector-text").textContent = (text ?? primary).textContent;
    pop.style.setProperty("--connector-color", trigger.dataset.roleColor);
    active = trigger;
    active.setAttribute("aria-describedby", pop.id);
    pop.hidden = false;
    position();
  }

  function scheduleClose() {
    clearTimeout(pending);
    if (!active || pinned || document.activeElement === active) return;
    pending = setTimeout(clear, 240);
  }

  function dismiss() {
    blocked = active;
    clear();
  }

  for (const diagram of document.querySelectorAll(".map-view svg.network, .map-view svg.map")) {
    const triggers = [...diagram.querySelectorAll(triggerSelector)].sort((a, b) =>
      a.dataset.connector.localeCompare(b.dataset.connector, undefined, { numeric: true }));
    if (!triggers.length) continue;
    diagram.setAttribute("role", "group");
    diagram.closest(".map-view").querySelector(".connector-help").hidden = false;
    const moveFocus = trigger => {
      for (const item of triggers) item.tabIndex = item === trigger ? 0 : -1;
      diagram.revealConnector?.(trigger);
      const canvas = trigger.closest(".inline-canvas");
      if (canvas && canvas.scrollWidth > canvas.clientWidth) {
        const box = trigger.getBoundingClientRect();
        const frame = canvas.getBoundingClientRect();
        if (box.left < frame.left + 12) canvas.scrollLeft += box.left - frame.left - 12;
        if (box.right > frame.right - 12) canvas.scrollLeft += box.right - frame.right + 12;
      }
      const bounds = trigger.getBoundingClientRect();
      const tabs = trigger.closest("[data-level]").querySelector(".view-tabs").getBoundingClientRect();
      const top = Math.max(0, tabs.bottom) + 8;
      if (bounds.top < top) window.scrollBy({ top: bounds.top - top, behavior: "instant" });
      else if (bounds.bottom > innerHeight - 8) window.scrollBy({ top: bounds.bottom - innerHeight + 8, behavior: "instant" });
      trigger.focus({ preventScroll: true });
    };
    for (const [index, trigger] of triggers.entries()) {
      trigger.setAttribute("role", "button");
      trigger.setAttribute("aria-label", "Connector " + trigger.dataset.connector);
      trigger.tabIndex = index === 0 ? 0 : -1;
      trigger.addEventListener("pointerenter", event => {
        if (event.pointerType !== "touch") open(trigger);
      });
      trigger.addEventListener("pointerleave", () => {
        if (blocked === trigger) blocked = null;
        if (active === trigger) scheduleClose();
      });
      trigger.addEventListener("focus", () => {
        blocked = null;
        diagram.revealConnector?.(trigger);
        for (const item of triggers) item.tabIndex = item === trigger ? 0 : -1;
        open(trigger);
      });
      trigger.addEventListener("blur", () => {
        if (blocked === trigger) blocked = null;
        if (active === trigger && !pop.matches(":hover") && !trigger.matches(":hover")) scheduleClose();
      });
      trigger.addEventListener("mousedown", event => event.preventDefault());
      const activate = () => {
        if (active === trigger && pinned) return dismiss();
        if (active !== trigger) clear();
        blocked = null;
        open(trigger);
        pinned = active === trigger;
      };
      trigger.addEventListener("click", activate);
      trigger.addEventListener("keydown", event => {
        const next = {
          ArrowRight: (index + 1) % triggers.length,
          ArrowDown: (index + 1) % triggers.length,
          ArrowLeft: (index + triggers.length - 1) % triggers.length,
          ArrowUp: (index + triggers.length - 1) % triggers.length,
          Home: 0,
          End: triggers.length - 1
        }[event.key];
        if (next !== undefined) {
          event.preventDefault();
          clear();
          blocked = null;
          moveFocus(triggers[next]);
        } else if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          activate();
        }
      });
    }
  }

  pop.addEventListener("pointerenter", () => clearTimeout(pending));
  pop.addEventListener("pointerleave", scheduleClose);
  document.addEventListener("pointerdown", event => {
    if (!event.target.closest(triggerSelector) && !pop.contains(event.target)) clear();
  });
  document.addEventListener("keydown", event => {
    if (event.key === "Escape" && active) {
      event.preventDefault();
      dismiss();
    }
  });
  document.addEventListener("click", event => {
    if (event.target.closest(".view-tabs button")) clear();
  });
  document.addEventListener("toggle", event => {
    if (event.target.matches(".diagram-disclosure") && !event.target.open) clear();
  }, true);
  document.addEventListener("mapviewchange", clear);
  window.addEventListener("popstate", clear);
  window.addEventListener("hashchange", clear);
  window.addEventListener("scroll", () => { if (active) position(); }, { capture: true, passive: true });
  window.addEventListener("resize", () => { if (active) position(); });
})();
