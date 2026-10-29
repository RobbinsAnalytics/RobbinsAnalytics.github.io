(() => {
  const route = document.querySelector('.learn-disposition');
  if (!route) return;
  const response = route.querySelector('.learn-response');
  const options = {
    correct: ['Correct the current solution', 'Record the defect and reason with the original version. Fix it, repeat affected checks and present the corrected version for its own review.', 'blue'],
    local: ['Retain the lesson with this project', 'Keep the observation, context and rationale beside the work. Later projects can inspect it without treating it as a shared rule.', 'blue'],
    propose: ['Propose a shared change', 'Record the proposed amendment and supporting evidence. An authorized owner reviews it before any maintained standard, method or tool changes.', 'amber'],
    defer: ['Defer with a reason', 'Keep the open question and evidence with the originating project. Revisit it when new evidence or a relevant request justifies the work.', 'neutral']
  };
  route.querySelectorAll('[data-route]').forEach(button => button.addEventListener('click', () => {
    const [title, detail, tone] = options[button.dataset.route];
    route.querySelectorAll('[data-route]').forEach(item => item.setAttribute('aria-pressed', String(item === button)));
    response.querySelector('h4').textContent = title;
    response.querySelector('p').textContent = detail;
    response.dataset.tone = tone;
  }));
})();
(() => {
  const route = document.querySelector('.learn-route');
  if (!route) return;
  const response = route.querySelector('.learn-transfer-response');
  const connections = {
    'ra-ml': ['A plausible number needs a written rule and an independent check.', 'Matter Ledger adds a frozen baseline, independently checked measures and published reconciliation to keep later runs inspectable.', 'Matter Ledger', 'examples.html#operations'],
    'ml-ci': ['A working first version is not enough; missing and failed work must become visible.', 'Claim Integrity makes expected claims and responses checkable even when nothing arrives. Its evidence and checks account for those absences instead of treating received records as the whole workload.', 'Claim Integrity', 'examples.html#claims'],
    'ci-about': ['Review needs an accountable path from evidence to a human decision.', 'About Cascadia keeps a private preview, versioned corrections and owner review separate from release. This page is being revised through that route.', 'About Cascadia', 'index.html']
  };
  route.querySelectorAll('[data-transfer]').forEach(button => button.addEventListener('click', () => {
    const [lesson, visible, name, href] = connections[button.dataset.transfer];
    route.querySelectorAll('[data-transfer]').forEach(item => item.setAttribute('aria-pressed', String(item === button)));
    response.querySelector('h4').textContent = lesson;
    response.querySelector('div:nth-child(2) p:not(.learn-eyebrow)').textContent = visible;
    const link = response.querySelector('a');
    link.href = href;
    link.textContent = `Explore ${name} →`;
  }));
})();
(() => {
  const nav = document.querySelector('.cwds-index nav');
  if (!nav) return;
  const groups = [
    ['evidence', ['evidence-route']],
    ['retrospectives', ['acceptance']],
    ['disposition', ['lesson-route', 'knowledge-homes']],
    ['next-request', []]
  ];
  const subsectionTitles = {
    'evidence-route': 'See how one build informed later work',
    acceptance: 'Acceptance',
    'lesson-route': 'Where should this lesson go',
    'knowledge-homes': 'Knowledge homes'
  };
  const activeGroup = () => {
    const header = document.querySelector('.cwds-header');
    const headerHeight = header && getComputedStyle(header).position === 'sticky' ? header.getBoundingClientRect().height : 0;
    const threshold = section => Math.max(100, headerHeight + (section?.querySelector('.section-heading-bar')?.getBoundingClientRect().height || 0) + 24);
    let current = groups[0][0];
    for (const [id] of groups) {
      const section = document.getElementById(id);
      if (section && section.getBoundingClientRect().top <= threshold(section)) current = id;
    }
    const currentSection = document.getElementById(current);
    const ids = groups.find(([id]) => id === current)?.[1] || [];
    let currentSubsection = null;
    ids.forEach(id => {
      const subsection = document.getElementById(id);
      if (subsection?.getBoundingClientRect().top <= threshold(currentSection)) currentSubsection = id;
    });
    nav.querySelectorAll('.learn-subnav').forEach(link => {
      link.hidden = link.dataset.parent !== current;
      if (!link.hidden && link.hash === `#${currentSubsection}`) link.setAttribute('aria-current', 'location');
      else link.removeAttribute('aria-current');
    });
    nav.querySelectorAll('a').forEach(link => {
      if (link.classList.contains('learn-subnav')) return;
      if (!currentSubsection && link.getAttribute('href') === `#${current}`) link.setAttribute('aria-current', 'location');
      else link.removeAttribute('aria-current');
    });
  };
  groups.forEach(([parent, ids]) => ids.slice().reverse().forEach(id => {
    const sectionLink = nav.querySelector(`a[href="#${parent}"]`);
    const target = document.getElementById(id);
    if (!sectionLink || !target) return;
    const link = document.createElement('a');
    link.href = `#${id}`;
    link.className = 'learn-subnav';
    link.dataset.parent = parent;
    link.textContent = subsectionTitles[id];
    link.hidden = true;
    sectionLink.after(link);
  }));
  let frame = 0;
  const schedule = () => {
    if (frame) return;
    frame = requestAnimationFrame(() => { frame = 0; activeGroup(); });
  };
  addEventListener('scroll', schedule, {passive: true});
  addEventListener('resize', schedule);
  activeGroup();
})();

/* Pin the active mobile choices only when their changing response fits below. */
(() => {
  const compact = matchMedia('(max-width: 767px)');
  const pairs = [
    ['.learn-transfer-choices', '.learn-transfer-response'],
    ['.learn-choices', '.learn-response']
  ].map(([choice, panel]) => {
    const controls = document.querySelector(choice);
    return controls && {controls, response: controls.parentElement.querySelector(panel)};
  }).filter(pair => pair?.response);
  if (!pairs.length) return;
  const safeBottom = () => Math.min(innerHeight - 8, (document.querySelector('.cwds-index-toggle')?.getBoundingClientRect().top ?? innerHeight) - 8);
  const sync = () => pairs.forEach(({controls, response}) => {
    const controlsHeight = controls.getBoundingClientRect().height;
    const responseHeight = response.getBoundingClientRect().height;
    controls.parentElement.style.setProperty('--learning-controls-height', `${Math.ceil(controlsHeight + 12)}px`);
    const transfer = controls.classList.contains('learn-transfer-choices');
    const fits = transfer
      ? controlsHeight <= safeBottom() * .42 && safeBottom() - controlsHeight >= 160
      : controlsHeight <= innerHeight * .36 && controlsHeight + responseHeight + 24 <= safeBottom();
    controls.classList.toggle('mobile-pin-ready', compact.matches && fits);
  });
  const sizes = new ResizeObserver(sync);
  pairs.forEach(({controls, response}) => {
    sizes.observe(controls);
    sizes.observe(response);
    controls.addEventListener('click', event => {
      if (!event.target.closest('button')) return;
      requestAnimationFrame(() => {
        sync();
        if (!compact.matches || controls.classList.contains('learn-transfer-choices')) return;
        const overflow = response.getBoundingClientRect().bottom - safeBottom();
        if (overflow > 0) scrollBy(0, overflow);
      });
    });
  });
  addEventListener('resize', sync);
  compact.addEventListener('change', sync);
  sync();
})();
