const levels = [...document.querySelectorAll("[data-level]")];
const labels = ["model", "example"];
const selection = Object.fromEntries(levels.map(level => [level.id, "model"]));

function updateLevel(level, view) {
  selection[level.id] = view;
  for (const choice of labels) {
    const selected = choice === view;
    const tab = level.querySelector('[data-view="' + choice + '"]');
    const panel = document.getElementById(level.id + "-" + choice);
    tab.setAttribute("aria-selected", String(selected));
    tab.tabIndex = selected ? 0 : -1;
    panel.hidden = !selected;
  }
}

function restoreLocation() {
  const match = /^#(executive|director|manager)(?:-(model|example))?$/.exec(location.hash);
  const stored = history.state?.views;
  for (const level of levels) {
    const linked = match && match[1] === level.id ? match[2] : undefined;
    updateLevel(level, linked ?? stored?.[level.id] ?? selection[level.id]);
  }
}

for (const level of levels) {
  const group = level.querySelector(".view-tabs");
  const tabs = [...group.querySelectorAll("button")];
  group.setAttribute("role", "tablist");
  for (const tab of tabs) {
    const panel = document.getElementById(level.id + "-" + tab.dataset.view);
    tab.setAttribute("role", "tab");
    panel.setAttribute("role", "tabpanel");
    panel.setAttribute("aria-labelledby", tab.id);
    panel.tabIndex = 0;
    let pointerScroll = null;
    tab.addEventListener("pointerdown", () => { pointerScroll = window.scrollY; });
    tab.addEventListener("pointercancel", () => { pointerScroll = null; });
    tab.addEventListener("mousedown", event => event.preventDefault());
    tab.addEventListener("click", event => {
      const scroll = event.detail ? pointerScroll ?? window.scrollY : window.scrollY;
      pointerScroll = null;
      if (selection[level.id] === tab.dataset.view) {
        tab.focus({ preventScroll: true });
        return;
      }
      const bar = group.getBoundingClientRect();
      const levelTop = window.scrollY + level.getBoundingClientRect().top;
      const pinned = level.querySelector(".tab-anchor").getBoundingClientRect().top < bar.top - 1;
      updateLevel(level, tab.dataset.view);
      setDiagramMode(panel.querySelector(".map-view"));
      if (pinned) {
        const floor = Math.ceil(scroll - levelTop + bar.bottom + 12);
        if (level.offsetHeight < floor) level.style.minHeight = floor + "px";
      }
      tab.focus({ preventScroll: true });
      if (Math.abs(window.scrollY - scroll) > 1) window.scrollTo({ top: scroll, behavior: "instant" });
      history.pushState({ views: { ...selection } }, "", "#" + panel.id);
    });
  }
  group.addEventListener("keydown", event => {
    const index = tabs.indexOf(event.target);
    if (index < 0) return;
    const target = { ArrowLeft: 1 - index, ArrowRight: 1 - index, Home: 0, End: 1 }[event.key];
    if (target === undefined) return;
    event.preventDefault();
    tabs[target].focus({ preventScroll: true });
  });
}
restoreLocation();
history.replaceState({ views: { ...selection } }, "");
for (const level of levels) level.querySelector(".view-tabs").hidden = false;
if (/^#(executive|director|manager)-(model|example)$/.test(location.hash)) {
  window.addEventListener("load", () => document.getElementById(location.hash.slice(1))?.scrollIntoView(), { once: true });
}
window.addEventListener("popstate", restoreLocation);
window.addEventListener("hashchange", restoreLocation);

const index = document.querySelector(".reading-index");
const indexButton = index.querySelector("summary");
index.addEventListener("keydown", event => {
  if (event.key === "Escape" && index.open && !desktopIndex.matches) {
    index.open = false;
    indexButton.focus();
  }
});
index.querySelectorAll("a").forEach(link => link.addEventListener("click", event => {
  const destination = document.querySelector(link.hash);
  if (!destination) return;
  event.preventDefault();
  if (index.open && !desktopIndex.matches) index.open = false;
  const view = /-(model|example)$/.exec(link.hash)?.[1];
  const level = destination.closest("[data-level]");
  if (view && level) updateLevel(level, view);
  if (location.hash !== link.hash) history.pushState({ views: { ...selection } }, "", link.hash);
  destination.scrollIntoView();
  destination.focus({ preventScroll: true });
}));
const indexLinks = [...index.querySelectorAll("[data-section-link]")];
let scheduled = false;
function highlight() {
  const last = indexLinks.filter(link => document.querySelector(link.hash).getBoundingClientRect().top <= 120).at(-1);
  const active = last ?? indexLinks[0];
  for (const link of indexLinks) {
    if (link === active) link.setAttribute("aria-current", "location");
    else link.removeAttribute("aria-current");
  }
  scheduled = false;
}
window.addEventListener("scroll", () => {
  if (scheduled) return;
  scheduled = true;
  requestAnimationFrame(highlight);
}, { passive: true });
highlight();
const desktopIndex = window.matchMedia("(min-width: 1440px)");
function setIndexLayout() { index.open = desktopIndex.matches; }
desktopIndex.addEventListener("change", setIndexLayout);
setIndexLayout();

index.dataset.enhanced = '';

const disclosureModes = new WeakMap();
function setDiagramMode(target) {
  if (!target || !target.clientWidth) return;
  const disclosure = target.querySelector(".diagram-disclosure");
  const state = disclosureModes.get(disclosure);
  if (!state) return;
  const wide = target.clientWidth >= 70 * parseFloat(getComputedStyle(document.documentElement).fontSize);
  if (state.wide === wide) return;
  state.wide = wide;
  disclosure.open = wide || state.compactOpen;
}
const resizeMaps = new ResizeObserver(entries => {
  for (const { target } of entries) setDiagramMode(target);
});
for (const disclosure of document.querySelectorAll(".diagram-disclosure")) {
  const state = { wide: undefined, compactOpen: false };
  disclosureModes.set(disclosure, state);
  disclosure.querySelector("summary").addEventListener("click", event => {
    if (state.wide) return;
    event.preventDefault();
    state.compactOpen = !disclosure.open;
    disclosure.open = state.compactOpen;
  });
  resizeMaps.observe(disclosure.closest(".map-view"));
}
const measureTabs = new ResizeObserver(() => {
  const height = Math.max(...levels.map(level => level.querySelector(".view-tabs").offsetHeight));
  document.documentElement.style.setProperty("--sticky-clearance", (height + 24) + "px");
});
for (const level of levels) measureTabs.observe(level.querySelector(".view-tabs"));

// Preserve the active reading position while panels reflow.
document.documentElement.classList.add("view-enhanced");
window.addEventListener("scroll", () => {
  for (const level of levels) {
    if (level.style.minHeight && level.querySelector(".tab-anchor").getBoundingClientRect().top >= 8) {
      level.style.removeProperty("min-height");
    }
  }
}, { passive: true });

for (const link of document.querySelectorAll("[data-open-view]")) {
  link.addEventListener("click", event => {
    if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    const panel = document.querySelector(link.hash);
    const level = panel?.closest("[data-level]");
    const view = /-(model|example)$/.exec(link.hash)?.[1];
    if (!level || !view) return;
    event.preventDefault();
    updateLevel(level, view);
    setDiagramMode(panel.querySelector(".map-view"));
    history.pushState({ views: { ...selection } }, "", link.hash);
    panel.scrollIntoView({ block: "start" });
    panel.focus({ preventScroll: true });
  });
}
