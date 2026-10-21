/* In-page navigation and typography only; no operating-model state is calculated. */
'use strict';
(() => {
  const header = document.getElementById('quarto-header');
  const nav = document.querySelector('.charter-index');
  const select = document.getElementById('charter-location');
  const content = document.querySelector('.charter-content');
  if (!header || !nav || !select || !content) return;
  const topLinks = [...nav.querySelectorAll('.charter-index-links > a')];
  const entries = topLinks.map(link => ({link, node: document.getElementById(link.hash.slice(1)), children: []})).filter(entry => entry.node);
  let scheduled = false;
  let previousTarget = '';
  const context = document.createElement('p');
  context.className = 'charter-current-section';
  context.setAttribute('aria-live', 'off');
  nav.querySelector('.charter-index-inner').appendChild(context);
  select.replaceChildren();
  entries.forEach(entry => {
    const group = document.createElement('optgroup');
    group.label = entry.link.textContent.trim();
    const option = new Option(entry.link.textContent.trim(), entry.link.hash);
    group.appendChild(option);
    const list = document.createElement('div');
    list.className = 'charter-index-children';
    list.hidden = true;
    entry.node.querySelectorAll('h3').forEach((heading, index) => {
      let target = heading;
      if (!target.id && heading.parentElement.id) target = heading.parentElement;
      if (!target.id) heading.id = entry.node.id + '-subsection-' + (index + 1);
      const child = document.createElement('a');
      child.href = '#' + target.id;
      child.textContent = heading.textContent.replace(/§\d+/g, '').trim();
      if (!child.textContent) return;
      list.appendChild(child);
      entry.children.push({link: child, node: target});
      const prefix = /^s(\d+)$/.exec(entry.node.id);
      group.appendChild(new Option((prefix ? prefix[1] + ' · ' : '') + child.textContent, '#' + target.id));
    });
    entry.link.after(list);
    entry.list = list;
    select.appendChild(group);
  });
  function compact() { return matchMedia('(max-width:900px)').matches; }
  function visible(node) { return node.getClientRects().length && !node.closest('details:not([open])'); }
  function track() {
    scheduled = false;
    const line = header.getBoundingClientRect().height + (compact() ? nav.getBoundingClientRect().height : 0) + 38;
    let active = entries[0];
    entries.forEach(entry => { if (entry.node.getBoundingClientRect().top <= line && visible(entry.node)) active = entry; });
    if (scrollY + innerHeight >= document.documentElement.scrollHeight - 3) active = entries.at(-1);
    let sub = null;
    active.children.forEach(child => { if (visible(child.node) && child.node.getBoundingClientRect().top <= line) sub = child; });
    entries.forEach(entry => {
      entry.list.hidden = entry !== active;
      entry.link.classList.toggle('is-active-parent', entry === active && !!sub);
      entry.link.removeAttribute('aria-current');
      entry.children.forEach(child => child.link.removeAttribute('aria-current'));
    });
    const current = sub || active;
    current.link.setAttribute('aria-current', 'location');
    if (select.value !== '#' + current.node.id) select.value = '#' + current.node.id;
    context.textContent = '';
    select.title = active.link.textContent.trim() + (sub ? ' - ' + sub.link.textContent : '');
    if (!compact() && previousTarget !== current.node.id) {
      const rail = nav.querySelector('.charter-index-inner');
      const bounds = rail.getBoundingClientRect(), item = current.link.getBoundingClientRect();
      if (item.bottom > bounds.bottom - 12) rail.scrollTop += item.bottom - bounds.bottom + 18;
      else if (item.top < bounds.top + 12) rail.scrollTop += item.top - bounds.top - 18;
    }
    previousTarget = current.node.id;
  }
  function queue() { if (!scheduled) { scheduled = true; requestAnimationFrame(track); } }
  function measure() {
    document.body.style.setProperty('--charter-header', header.getBoundingClientRect().height + 'px');
    document.body.style.setProperty('--charter-index', (compact() ? nav.getBoundingClientRect().height : 0) + 'px');
    queue();
  }
  function reveal(hash, focus) {
    let id;
    try { id = decodeURIComponent(hash.slice(1)); } catch { return; }
    const target = document.getElementById(id);
    if (!target) return;
    for (let parent = target.parentElement; parent; parent = parent.parentElement) if (parent.tagName === 'DETAILS') parent.open = true;
    const destination = entries.find(entry => entry.node === target || entry.node.contains(target));
    const subsection = destination && destination.children.find(child => child.node === target || child.node.contains(target));
    context.textContent = '';
    measure();
    target.scrollIntoView({block:'start', behavior:'instant'});
    if (focus) {
      const heading = target.matches('h1,h2,h3') ? target : target.querySelector('h1,h2,h3');
      if (heading) { heading.tabIndex = -1; heading.focus({preventScroll:true}); }
    }
    track();
    measure();
  }
  select.addEventListener('change', () => { history.pushState(null, '', select.value); reveal(select.value, false); });
  document.addEventListener('click', event => {
    if (event.button || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    const link = event.target.closest('a[href]');
    if (!link || link.origin !== location.origin || link.pathname !== location.pathname || !link.hash) return;
    let target;
    try { target = document.getElementById(decodeURIComponent(link.hash.slice(1))); } catch { return; }
    if (!target) return;
    event.preventDefault();
    history.pushState(null, '', link.hash);
    reveal(link.hash, true);
  });
  window.addEventListener('scroll', queue, {passive:true});
  window.addEventListener('hashchange', () => reveal(location.hash, false));
  window.addEventListener('popstate', () => reveal(location.hash, false));
  document.addEventListener('toggle', queue, true);
  new ResizeObserver(measure).observe(header);
  new ResizeObserver(measure).observe(nav);

  // Keep the final two words together only when a desktop final line contains one word.
  // Original text is restored before measuring a new width; mobile wrapping remains natural.
  const originals = new Map();
  function repairRunts() {
    originals.forEach((value, node) => { if (node.isConnected) node.nodeValue = value; });
    originals.clear();
    if (innerWidth < 1000) { measure(); return; }
    content.querySelectorAll('p,li,h2,h3,dd,td').forEach(block => {
      if (!visible(block) || block.querySelector('p,li,ul,ol,svg,table,details')) return;
      const walker = document.createTreeWalker(block, NodeFilter.SHOW_TEXT);
      const words = []; let node;
      while ((node = walker.nextNode())) {
        let match; const regex = /\S+/g;
        while ((match = regex.exec(node.nodeValue))) {
          const range = document.createRange();
          range.setStart(node, match.index); range.setEnd(node, match.index + match[0].length);
          const rect = range.getBoundingClientRect();
          if (rect.width && rect.height) words.push({node, start:match.index, end:match.index+match[0].length, rect});
        }
      }
      if (words.length < 4) return;
      const last = words.at(-1), before = words.at(-2);
      if (last.node !== before.node || last.rect.top - before.rect.top < 8 || last.rect.width + before.rect.width > block.clientWidth * .8) return;
      const gap = last.node.nodeValue.slice(before.end, last.start);
      if (!/^\s+$/.test(gap)) return;
      originals.set(last.node, last.node.nodeValue);
      last.node.nodeValue = last.node.nodeValue.slice(0, before.end) + '\u00a0' + last.node.nodeValue.slice(last.start);
    });
    measure();
  }
  let typographyFrame = null;
  window.addEventListener('resize', () => {
    measure();
    if (typographyFrame) cancelAnimationFrame(typographyFrame);
    typographyFrame = requestAnimationFrame(repairRunts);
  });
  measure();
  document.fonts.ready.then(() => { repairRunts(); if (location.hash) reveal(location.hash, false); });
})();
