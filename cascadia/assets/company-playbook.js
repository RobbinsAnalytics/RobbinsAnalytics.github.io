/* One illustrative request preserves its selected state and visible next action. */
(() => {
  'use strict';
  const sectionHeadings = [...document.querySelectorAll('.company-page .cwds-section > .section-heading-bar')];
  if (sectionHeadings.length && window.ResizeObserver) {
    let aligned = false;
    const headingSizes = new ResizeObserver(entries => {
      entries.forEach(({target}) => target.closest('[data-cwds-section]')?.style.setProperty('--section-heading-height', `${Math.ceil(target.getBoundingClientRect().height)}px`));
      if (aligned) return;
      aligned = true;
      const target = document.getElementById(decodeURIComponent(location.hash.slice(1)));
      if (target?.matches('[data-cwds-subsection]')) requestAnimationFrame(() => target.scrollIntoView({block: 'start'}));
    });
    sectionHeadings.forEach(heading => headingSizes.observe(heading));
  }
  const request = document.querySelector('#request-walkthrough');
  if (!request) return;
  const controls = request.querySelector('.company-request-controls');
  const buttons = [...controls.querySelectorAll('.company-request-choice')];
  const panel = request.querySelector('.company-request-panel');
  const status = panel.querySelector('.company-request-status');
  const heading = panel.querySelector('h3');
  const body = panel.querySelector('p:not(.company-request-status):not(.company-request-next)');
  const next = panel.querySelector('.company-request-next');
  if (buttons.length !== 4 || !status || !heading || !body || !next) return;

  const steps = [
    {
      status: 'After inventory · Captured, waiting for intake',
      heading: 'The question is recorded, with no delivery promise.',
      bodyLead: 'Keep the requester’s original words and identify its owner.',
      bodyTail: 'Formal intake waits for the selected foundation to be ready.',
      next: 'Return to the owner when intake opens.'
    },
    {
      status: 'After readiness · Formal intake',
      heading: 'Confirm the business question, then check what exists.',
      bodyLead: 'The requester confirms the audience, useful result, resources and restrictions.',
      bodyTail: 'An existing answer can close the request; an access gap follows the access route; a needed change gets a defined scope.',
      next: 'Schedule only when resources are confirmed and restrictions are cleared.'
    },
    {
      status: 'After accepted intake · Develop and verify',
      heading: 'Build only the part that is needed.',
      bodyLead: 'Use certified definitions and approved tools.',
      bodyTail: 'AI can help draft within the permitted work envelope; the delivery lead checks the result against the agreed rules and expected cases.',
      next: 'Present a version with evidence and stated limits for private review.'
    },
    {
      status: 'Before release · Human acceptance',
      heading: 'The requester decides whether the solution works.',
      bodyLead: 'The delivery lead confirms the applicable checks.',
      bodyTail: 'The requester accepts, requests correction or rejects the reviewed version and supplies firsthand retrospective feedback.',
      next: 'Release through the company’s approved route, then assign ongoing ownership.'
    }
  ];

  function select(index) {
    const step = steps[index];
    buttons.forEach((button, buttonIndex) => button.setAttribute('aria-pressed', String(buttonIndex === index)));
    panel.dataset.step = String(index);
    status.textContent = step.status;
    heading.textContent = step.heading;
    body.replaceChildren(Object.assign(document.createElement('strong'), {textContent: step.bodyLead}), document.createTextNode(' ' + step.bodyTail));
    next.replaceChildren(Object.assign(document.createElement('strong'), {textContent: 'Next: '}), document.createTextNode(step.next));
  }
  buttons.forEach((button, index) => {
    button.setAttribute('aria-controls', panel.id);
    button.addEventListener('click', () => select(index));
  });
  controls.hidden = false;
  select(0);

  const compact = matchMedia('(max-width: 767px)');
  const safeBottom = () => Math.min(innerHeight - 8, (document.querySelector('.cwds-index-toggle')?.getBoundingClientRect().top ?? innerHeight) - 8);
  const syncPin = () => {
    const sectionHeading = request.closest('[data-cwds-section]')?.querySelector('.section-heading-bar');
    const stack = (sectionHeading?.getBoundingClientRect().height ?? 0) + controls.getBoundingClientRect().height;
    controls.classList.toggle('mobile-pin-ready', compact.matches && stack <= innerHeight * 0.45 && safeBottom() - stack >= 160);
  };
  if (window.ResizeObserver) {
    const observer = new ResizeObserver(syncPin);
    observer.observe(controls);
    const sectionHeading = request.closest('[data-cwds-section]')?.querySelector('.section-heading-bar');
    if (sectionHeading) observer.observe(sectionHeading);
  }
  compact.addEventListener('change', syncPin);
  addEventListener('resize', syncPin);
  syncPin();

  const diagram = document.querySelector('.company-definition-map');
  if (!diagram || !window.CascadiaRelationshipArrow) return;
  const diagramDesktop = matchMedia('(min-width: 900px)');
  let arrows = [];
  function syncDiagram() {
    if (!diagramDesktop.matches && arrows.length) {
      arrows.forEach(arrow => arrow.disconnect());
      arrows = [];
    } else if (diagramDesktop.matches && !arrows.length) {
      const point = selector => diagram.querySelector(selector);
      const mount = options => CascadiaRelationshipArrow.mount({container: diagram, direction: 'forward', ...options});
      arrows = [
        mount({from: point('#definition-sales'), to: point('#definition-owner'), key: 'sales-to-owner', axis: 'diagonal', toPort: .28}),
        mount({from: point('#definition-finance'), to: point('#definition-owner'), key: 'finance-to-owner', axis: 'diagonal', toPort: .72}),
        mount({from: point('#definition-owner'), to: point('#definition-result'), key: 'owner-to-result', axis: 'horizontal'})
      ];
    }
  }
  diagramDesktop.addEventListener('change', syncDiagram);
  syncDiagram();
})();
