/* Preserve readable subsection targets beneath each mobile sticky heading. */
(() => {
  const headings = [...document.querySelectorAll('.section-heading-bar')];
  const measure = () => { document.body.style.setProperty('--index-top', `${Math.max(24, document.querySelector('.preview-header').getBoundingClientRect().bottom + 24)}px`); headings.forEach(heading => {
    heading.closest('[data-cwds-section]').style.setProperty('--section-title-height', `${Math.ceil(heading.getBoundingClientRect().height)}px`);
  }); };
  measure();
  if ('ResizeObserver' in window) {
    const observer = new ResizeObserver(measure);
    headings.forEach(heading => observer.observe(heading));
  }
  window.addEventListener('resize', measure, {passive:true});
  let frame = 0;
  window.addEventListener('scroll', () => {
    if (!frame) frame = requestAnimationFrame(() => { frame = 0; measure(); });
  }, {passive:true});
})();
