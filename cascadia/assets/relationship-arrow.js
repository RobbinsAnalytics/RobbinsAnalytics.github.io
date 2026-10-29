/* Case-local relationship arrow primitive for future Cascadia diagram edits. */
(() => {
  'use strict';

  const ns = 'http://www.w3.org/2000/svg';
  const owners = new WeakMap();
  const directions = new Set(['forward', 'reverse', 'both']);
  const axes = new Set(['auto', 'horizontal', 'vertical', 'diagonal']);

  function element(value, name) {
    if (!(value instanceof Element)) throw new TypeError(`${name} must be an Element`);
    return value;
  }

  function mount({ container, from, to, key, direction = 'forward', axis = 'auto', clearance = 8, minLength = 16, fromPort = 0.5, toPort = 0.5 }) {
    element(container, 'container');
    element(from, 'from');
    element(to, 'to');
    if (!key || typeof key !== 'string') throw new TypeError('key must identify this relationship');
    if (!directions.has(direction)) throw new TypeError('direction must be forward, reverse, or both');
    if (!axes.has(axis)) throw new TypeError('axis must be auto, horizontal, vertical, or diagonal');
    if (!Number.isFinite(clearance) || clearance < 0) throw new TypeError('clearance must be nonnegative');
    if (!Number.isFinite(minLength) || minLength < 14) throw new TypeError('minLength must be at least 14');
    if (![fromPort, toPort].every(value => Number.isFinite(value) && value >= 0 && value <= 1)) throw new TypeError('ports must be fractions from 0 to 1');
    if (!container.contains(from) || !container.contains(to)) throw new Error('Both endpoints must belong to the container');
    if (getComputedStyle(container).position === 'static') throw new Error('The container needs a positioned layout');

    let byKey = owners.get(container);
    if (!byKey) { byKey = new Map(); owners.set(container, byKey); }
    if (byKey.has(key)) throw new Error(`Relationship ${key} already has a renderer`);

    const svg = document.createElementNS(ns, 'svg');
    svg.classList.add('cascadia-relationship-arrow');
    svg.dataset.relationshipKey = key;
    svg.setAttribute('aria-hidden', 'true');
    Object.assign(svg.style, {
      position: 'absolute', display: 'none', overflow: 'visible', pointerEvents: 'none',
      width: '0', height: '0', zIndex: '2'
    });
    container.append(svg);
    byKey.set(key, svg);

    let frame = 0;
    let disposed = false;
    const observer = window.ResizeObserver ? new ResizeObserver(schedule) : null;

    function hide(reason) {
      svg.dataset.state = reason;
      svg.style.display = 'none';
      svg.replaceChildren();
    }

    function draw(vertical, length) {
      const line = document.createElementNS(ns, 'line');
      const start = direction === 'reverse' || direction === 'both' ? 6 : 1;
      const end = direction === 'forward' || direction === 'both' ? length - 6 : length - 1;
      line.setAttribute('x1', String(vertical ? 8 : start));
      line.setAttribute('y1', String(vertical ? start : 8));
      line.setAttribute('x2', String(vertical ? 8 : end));
      line.setAttribute('y2', String(vertical ? end : 8));
      const parts = [line];
      for (const atStart of [true, false]) {
        if (atStart && direction === 'forward') continue;
        if (!atStart && direction === 'reverse') continue;
        const head = document.createElementNS(ns, 'polyline');
        const tip = atStart ? 1 : length - 1;
        const base = atStart ? 6 : length - 6;
        head.setAttribute('points', vertical
          ? `4 ${base} 8 ${tip} 12 ${base}`
          : `${base} 4 ${tip} 8 ${base} 12`);
        parts.push(head);
      }
      for (const part of parts) {
        part.setAttribute('fill', 'none');
        part.setAttribute('stroke', 'currentColor');
        part.setAttribute('stroke-width', '1.25');
        part.setAttribute('stroke-linecap', 'round');
        part.setAttribute('stroke-linejoin', 'round');
      }
      svg.setAttribute('viewBox', vertical ? `0 0 16 ${length}` : `0 0 ${length} 16`);
      svg.replaceChildren(...parts);
    }

    function drawDiagonal(box, a, b) {
      const horizontal = b.left - a.right >= b.top - a.bottom;
      const start = horizontal
        ? {x: a.right + clearance - box.left, y: a.top + a.height * fromPort - box.top}
        : {x: a.left + a.width * fromPort - box.left, y: a.bottom + clearance - box.top};
      const end = horizontal
        ? {x: b.left - clearance - box.left, y: b.top + b.height * toPort - box.top}
        : {x: b.left + b.width * toPort - box.left, y: b.top - clearance - box.top};
      const dx = end.x - start.x, dy = end.y - start.y;
      const length = Math.hypot(dx, dy);
      if ((horizontal ? dx : dy) < minLength || length < minLength) { hide('insufficient-clearance'); return; }
      const left = Math.min(start.x, end.x) - 6, top = Math.min(start.y, end.y) - 6;
      const width = Math.abs(dx) + 12, height = Math.abs(dy) + 12;
      if (left < 0 || top < 0 || left + width > box.width || top + height > box.height) {
        hide('outside-container'); return;
      }
      const x1 = start.x - left, y1 = start.y - top, x2 = end.x - left, y2 = end.y - top;
      const ux = dx / length, uy = dy / length, px = -uy, py = ux;
      const atStart = direction === 'reverse' || direction === 'both';
      const atEnd = direction === 'forward' || direction === 'both';
      const line = document.createElementNS(ns, 'line');
      line.setAttribute('x1', String(x1 + (atStart ? 5 * ux : 0)));
      line.setAttribute('y1', String(y1 + (atStart ? 5 * uy : 0)));
      line.setAttribute('x2', String(x2 - (atEnd ? 5 * ux : 0)));
      line.setAttribute('y2', String(y2 - (atEnd ? 5 * uy : 0)));
      const parts = [line];
      for (const first of [true, false]) {
        if (first && !atStart || !first && !atEnd) continue;
        const tipX = first ? x1 : x2, tipY = first ? y1 : y2;
        const baseX = tipX + (first ? 5 : -5) * ux;
        const baseY = tipY + (first ? 5 : -5) * uy;
        const head = document.createElementNS(ns, 'polyline');
        head.setAttribute('points', `${baseX + 4 * px} ${baseY + 4 * py} ${tipX} ${tipY} ${baseX - 4 * px} ${baseY - 4 * py}`);
        parts.push(head);
      }
      for (const part of parts) {
        part.setAttribute('fill', 'none');
        part.setAttribute('stroke', 'currentColor');
        part.setAttribute('stroke-width', '1.25');
        part.setAttribute('stroke-linecap', 'round');
        part.setAttribute('stroke-linejoin', 'round');
      }
      svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
      svg.replaceChildren(...parts);
      svg.dataset.state = 'visible';
      svg.dataset.axis = 'diagonal';
      Object.assign(svg.style, {left: `${left}px`, top: `${top}px`, width: `${width}px`, height: `${height}px`, display: 'block'});
    }

    function update() {
      if (disposed) return;
      const box = container.getBoundingClientRect();
      const a = from.getBoundingClientRect();
      const b = to.getBoundingClientRect();
      if (!box.width || !box.height || !a.width || !b.width) { hide('unavailable'); return; }
      if (axis === 'diagonal') { drawDiagonal(box, a, b); return; }
      const horizontalGap = b.left - a.right;
      const verticalGap = b.top - a.bottom;
      const vertical = axis === 'vertical' || (axis === 'auto' && verticalGap > horizontalGap);
      const gap = vertical ? verticalGap : horizontalGap;
      const length = gap - 2 * clearance;
      if (length < minLength) { hide('insufficient-clearance'); return; }

      const cross = vertical
        ? ((a.left + a.right + b.left + b.right) / 4) - box.left
        : ((a.top + a.bottom + b.top + b.bottom) / 4) - box.top;
      const left = vertical ? cross - 8 : a.right - box.left + clearance;
      const top = vertical ? a.bottom - box.top + clearance : cross - 8;
      const width = vertical ? 16 : length;
      const height = vertical ? length : 16;
      if (left < 0 || top < 0 || left + width > box.width || top + height > box.height) {
        hide('outside-container'); return;
      }
      svg.dataset.state = 'visible';
      svg.dataset.axis = vertical ? 'vertical' : 'horizontal';
      Object.assign(svg.style, {
        left: `${left}px`, top: `${top}px`, width: `${width}px`, height: `${height}px`, display: 'block'
      });
      draw(vertical, length);
    }

    function schedule() {
      if (disposed) return;
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(update);
    }

    for (const target of [container, from, to]) observer?.observe(target);
    window.addEventListener('resize', schedule);
    document.fonts?.ready.then(schedule);
    update();

    return {
      svg,
      update,
      disconnect() {
        if (disposed) return;
        disposed = true;
        cancelAnimationFrame(frame);
        observer?.disconnect();
        window.removeEventListener('resize', schedule);
        svg.remove();
        byKey.delete(key);
      }
    };
  }

  window.CascadiaRelationshipArrow = Object.freeze({ mount });
})();
