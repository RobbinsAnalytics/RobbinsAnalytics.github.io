'use strict';
(() => {
  const header = document.getElementById('quarto-header');
  const nav = document.querySelector('.charter-index');
  if (!header || !nav) return;
  const links = [...nav.querySelectorAll('a')];
  const select = document.getElementById('charter-location');
  const sections = links.map(a => document.getElementById(a.hash.slice(1)));
  let scheduled = false;
  function track() {
    const compact = matchMedia('(max-width:900px)').matches;
    const offset = header.getBoundingClientRect().height + (compact ? nav.getBoundingClientRect().height : 0);
    let active = 0;
    sections.forEach((section, i) => {if (section.getBoundingClientRect().top <= offset + 65) active = i;});
    if (scrollY + innerHeight >= document.documentElement.scrollHeight - 3) active = links.length - 1;
    links.forEach((link, i) => {if(i === active)link.setAttribute('aria-current','location');else link.removeAttribute('aria-current');});
    select.value = links[active].hash; scheduled = false;
  }
  function measure() {
    document.body.style.setProperty('--charter-header', header.getBoundingClientRect().height + 'px');
    document.body.style.setProperty('--charter-index', (matchMedia('(max-width:900px)').matches ? nav.getBoundingClientRect().height : 0) + 'px');
    track();
  }
  function reveal(hash, focus) {
    const target = document.getElementById(decodeURIComponent(hash.slice(1)));
    if (!target) return;
    for (let p = target.parentElement; p; p = p.parentElement) if (p.tagName === 'DETAILS') p.open = true;
    target.scrollIntoView({block:'start', behavior:'instant'});
    if (focus) {
      const heading = target.matches('h1,h2,h3') ? target : target.querySelector('h1,h2,h3');
      if (heading) {heading.tabIndex = -1; heading.focus({preventScroll:true});}
    }
    track();
  }
  select.addEventListener('change', () => {history.pushState(null,'',select.value); reveal(select.value, false);});
  document.addEventListener('click', event => {
    const link = event.target.closest('a[href]');
    if (!link || link.origin !== location.origin || link.pathname !== location.pathname || !link.hash || !document.getElementById(link.hash.slice(1))) return;
    event.preventDefault();history.pushState(null,'',link.hash);reveal(link.hash, true);
  });
  window.addEventListener('scroll', () => {if(!scheduled){scheduled=true;requestAnimationFrame(track);}}, {passive:true});
  window.addEventListener('resize', measure);
  window.addEventListener('hashchange', () => reveal(location.hash, false));
  new ResizeObserver(measure).observe(header);new ResizeObserver(measure).observe(nav);
  measure();if(location.hash)reveal(location.hash, false);
})();
