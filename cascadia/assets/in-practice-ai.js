/* The sequence is also stated in the numbered cards and their surrounding text. */
(() => {
  'use strict';
  const container = document.querySelector('#ai-relationship-diagram');
  if (container && window.CascadiaRelationshipArrow) {
    const steps = [...container.querySelectorAll(':scope > .ai-step')];
    if (steps.length === 4) {
      for (let index = 0; index < steps.length - 1; index += 1) {
        window.CascadiaRelationshipArrow.mount({
          container,
          from: steps[index],
          to: steps[index + 1],
          key: `ai-stage-${index + 1}-to-${index + 2}`,
          direction: 'forward',
          axis: 'vertical'
        });
      }
    }
  }

  const branch = document.querySelector('#revenue-paths .branch-model');
  if (branch && window.CascadiaRelationshipArrow) {
    const source = branch.querySelector(':scope > .role-readiness');
    const paths = [...branch.querySelectorAll('.parallel-paths > .model-node')];
    const result = branch.querySelector(':scope > .role-assurance');
    if (source && result && paths.length === 2) {
      paths.forEach((path, index) => {
        window.CascadiaRelationshipArrow.mount({
          container: branch, from: source, to: path,
          key: `written-rules-to-path-${index + 1}`, direction: 'forward', axis: 'diagonal',
          fromPort: index === 0 ? 0.35 : 0.65
        });
        window.CascadiaRelationshipArrow.mount({
          container: branch, from: path, to: result,
          key: `path-${index + 1}-to-reconciliation`, direction: 'forward', axis: 'diagonal',
          toPort: index === 0 ? 0.35 : 0.65
        });
      });
    }
  }

  const make = (tag, className, text) => {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text) element.textContent = text;
    return element;
  };
  const compactView = matchMedia('(max-width: 767px)');
  // Hash destinations clear the measured section heading at every width.
  let initialHashAligned = false;
  const headingSizes = new ResizeObserver(entries => {
    entries.forEach(({target}) => {
      target.closest('[data-cwds-section]')?.style.setProperty('--section-heading-height', `${Math.ceil(target.getBoundingClientRect().height)}px`);
    });
    if (!initialHashAligned) {
      initialHashAligned = true;
      const target = document.getElementById(decodeURIComponent(location.hash.slice(1)));
      if (target?.matches('[data-cwds-subsection]')) requestAnimationFrame(() => target.scrollIntoView({block: 'start'}));
    }
  });
  document.querySelectorAll('.cwds-section > .section-heading-bar').forEach(heading => headingSizes.observe(heading));

  // The five existing capability descriptions become the choice labels. The
  // map shows primary touchpoints in this illustration, not exclusive ownership.
  const capabilities = document.querySelector('#ai-work .ai-capabilities');
  if (capabilities) {
    const items = [...capabilities.querySelectorAll('li')];
    const touchpoints = [
      [1],       // Sovereign Ground
      [0, 1],    // Foundation Readiness
      [2],       // Solutions Foundry
      [2, 3],    // Experience Framework
      [3]        // Trust Assurance
    ];
    const roles = [
      'Ground. Permitted data and source traceability.',
      'Frame + Ground. Business meaning and expected answers.',
      'Propose. Candidate queries, code and tests for review.',
      'Propose + Verify. Findings a reader can inspect.',
      'Verify. Checks, review and retained limits.'
    ];
    if (items.length === touchpoints.length) {
      capabilities.classList.add('ai-capabilities--interactive');
      const capabilityTitle = capabilities.querySelector('h3');
      const capabilityPrompt = make('p', 'ai-capabilities-prompt', 'Select a capability to see its primary place in the four-stage workflow.');
      capabilityTitle.after(capabilityPrompt);
      const capabilityPin = make('div', 'ai-capability-pin');
      capabilityPrompt.after(capabilityPin);
      capabilityPin.append(capabilities.querySelector('ul'));
      const map = make('figure', 'ai-capability-map');
      map.append(make('figcaption', '', 'Where each capability primarily helps'));
      const track = make('ol', 'ai-capability-track');
      const stageNames = ['Frame', 'Ground', 'Propose', 'Verify'];
      const nodes = stageNames.map((name, index) => {
        const node = make('li', 'ai-capability-node');
        node.append(make('span', 'ai-capability-node-number', `0${index + 1}`), make('strong', '', name));
        track.append(node);
        return node;
      });
      map.append(track);
      const response = make('p', 'ai-capability-response');
      response.id = 'ai-capability-response';
      response.setAttribute('aria-live', 'polite');
      map.append(response);
      const placeResponse = () => compactView.matches ? capabilityPin.after(response) : track.after(response);
      compactView.addEventListener('change', placeResponse);
      placeResponse();
      capabilities.append(map);
      let active = null;
      const buttons = items.map((item, index) => {
        const button = make('button', 'ai-capability-choice');
        button.type = 'button';
        button.setAttribute('aria-pressed', 'false');
        button.setAttribute('aria-controls', response.id);
        button.append(...item.childNodes);
        item.append(button);
        button.addEventListener('click', () => {
          select(active === index ? null : index);
          if (!compactView.matches) return;
          requestAnimationFrame(() => {
            const pinBottom = capabilityPin.getBoundingClientRect().bottom;
            const result = response.getBoundingClientRect();
            const navTop = document.querySelector('.cwds-index-toggle')?.getBoundingClientRect().top ?? innerHeight;
            const safeBottom = Math.min(innerHeight - 8, navTop - 8);
            if (result.bottom > safeBottom) scrollBy(0, result.bottom - safeBottom);
            else if (result.top < pinBottom + 8) scrollBy(0, result.top - pinBottom - 8);
          });
        });
        return button;
      });
      function select(index) {
        active = index;
        buttons.forEach((button, choice) => button.setAttribute('aria-pressed', String(choice === index)));
        nodes.forEach((node, stage) => node.classList.toggle('is-active', index !== null && touchpoints[index].includes(stage)));
        if (index === null) {
          response.textContent = 'Select a capability to highlight where it primarily supports the workflow.';
        } else {
          const name = buttons[index].querySelector('strong').textContent;
          response.replaceChildren(make('strong', '', name), make('span', '', roles[index]));
        }
      }
      select(1);
    }
  }

  // Compare the AI draft with the effective-date rule without implying that
  // the published, rule-based Revenue Assurance module is an AI agent.
  const illustration = document.querySelector('#ai-work .ai-illustration');
  if (illustration) {
    const explorer = make('figure', 'ai-billing-explorer');
    explorer.append(make('figcaption', '', 'Trace the effective-date error'));
    const controls = make('div', 'ai-billing-controls');
    controls.setAttribute('role', 'group');
    controls.setAttribute('aria-label', 'Inspect the billing example');
    const labels = ['AI candidate', 'Rule check', 'Reviewed decision'];
    const buttons = labels.map((label, index) => {
      const button = make('button', 'ai-billing-choice', `${index + 1}. ${label}`);
      button.type = 'button';
      button.setAttribute('aria-pressed', 'false');
      controls.append(button);
      return button;
    });
    explorer.append(controls);
    const timeline = make('div', 'ai-billing-timeline');
    const corner = make('span', 'ai-billing-corner', 'Billable quantity');
    timeline.append(corner, make('strong', 'ai-billing-date', 'Today'), make('strong', 'ai-billing-date', 'At next term'));
    const rows = [
      ['AI draft', 'Reduced too early', 'Reduced quantity'],
      ['Agreed rule', 'Current quantity', 'Reduced quantity']
    ].map(([label, today, next], index) => {
      const rowLabel = make('strong', 'ai-billing-row-label', label);
      const first = make('span', `ai-billing-cell${index === 0 ? ' is-error' : ' is-correct'}`, today);
      const second = make('span', 'ai-billing-cell', next);
      timeline.append(rowLabel, first, second);
      return [rowLabel, first, second];
    });
    explorer.append(timeline);
    const response = make('p', 'ai-billing-response');
    response.id = 'ai-billing-response';
    response.setAttribute('aria-live', 'polite');
    explorer.append(response);
    const placeResponse = () => compactView.matches ? controls.after(response) : timeline.after(response);
    compactView.addEventListener('change', placeResponse);
    placeResponse();
    const messages = [
      'The AI draft reduces today’s billable quantity before the agreed effective date.',
      'The rule and known case expose the early reduction. Both paths agree next term.',
      'A person rejects the draft, corrects the calculation and retains the failed case as a test.'
    ];
    function select(index) {
      buttons.forEach((button, choice) => button.setAttribute('aria-pressed', String(choice === index)));
      rows.forEach((row, rowIndex) => row.forEach(cell => cell.classList.toggle('is-emphasized', index === 2 || rowIndex === index)));
      response.textContent = messages[index];
    }
    buttons.forEach((button, index) => button.addEventListener('click', () => select(index)));
    illustration.querySelector('.ai-illustration-grid').after(explorer);
    select(0);
  }

  // A synthetic, deliberately small case exposes the difference between an
  // order-register count and the billable quantity after the timing rule.
  const revenue = document.querySelector('#revenue .case-body');
  if (revenue) {
    const explorer = make('figure', 'revenue-rule-explorer');
    explorer.append(make('figcaption', '', 'What changes when the timing rule becomes executable?'));
    explorer.append(make('p', 'revenue-rule-context', 'Illustrative case: a customer has 10 licenses and requests a reduction to 7 halfway through the current term. The agreed rule takes effect at the next term boundary.'));
    const controls = make('div', 'revenue-rule-controls');
    controls.setAttribute('role', 'group');
    controls.setAttribute('aria-label', 'Compare calculations with and without the implemented timing rule');
    const labels = ['Order count alone', 'Rule-aware solution'];
    const buttons = labels.map((label) => {
      const button = make('button', 'revenue-rule-choice', label);
      button.type = 'button';
      button.setAttribute('aria-pressed', 'false');
      controls.append(button);
      return button;
    });
    explorer.append(controls);
    const outputs = make('div', 'revenue-rule-outputs');
    const cells = [
      ['Order register now', '7', 'Requested quantity'],
      ['Billable this term', '7', 'Calculated quantity'],
      ['Billable next term', '7', 'Calculated quantity']
    ].map(([label, value, note]) => {
      const cell = make('div', 'revenue-rule-output');
      cell.append(make('span', 'revenue-rule-label', label), make('strong', 'revenue-rule-value', value), make('span', 'revenue-rule-note', note));
      outputs.append(cell);
      return cell;
    });
    explorer.append(outputs);
    const explanation = make('p', 'revenue-rule-explanation');
    explanation.setAttribute('aria-live', 'polite');
    explorer.append(explanation);
    const placeExplanation = () => compactView.matches ? controls.after(explanation) : outputs.after(explanation);
    compactView.addEventListener('change', placeExplanation);
    placeExplanation();
    const states = [
      { current: '7', note: 'A plausible 7 comes straight from the latest order. It answers “what was requested?” but bills the reduction too early.' },
      { current: '10', note: 'The solution implements the known effective-date rule: bill 10 through this term, then 7 next term. Python and SQL reconcile that result.' }
    ];
    function select(index) {
      buttons.forEach((button, choice) => button.setAttribute('aria-pressed', String(choice === index)));
      cells[1].querySelector('.revenue-rule-value').textContent = states[index].current;
      cells[1].classList.toggle('is-error', index === 0);
      cells[1].classList.toggle('is-correct', index === 1);
      explanation.textContent = states[index].note;
    }
    buttons.forEach((button, index) => button.addEventListener('click', () => select(index)));
    revenue.querySelector('.rule-strip').after(explorer);
    select(0);
  }

  // This documented first-run failure is presented without treating a
  // corrected operating rule as a claim of current scheduler uptime.
  const ledger = document.querySelector('#run-check');
  if (ledger) {
    const controls = make('div', 'case-interaction-controls');
    controls.setAttribute('role', 'group');
    controls.setAttribute('aria-label', 'Compare the original refresh with its corrected operating rule');
    const states = [
      { label: 'Original run', values: ['36', '0', 'Could skip unsaved work'], message: 'The progress marker moved past 36 dockets before any rows were saved. A rate limit stopped the run, leaving a gap that the marker concealed.' },
      { label: 'Corrected route', values: ['One docket at a time', 'Before the marker moves', 'Resume unfinished dockets'], message: 'The documented correction saves each docket’s rows before advancing the marker. Partial dockets retain a resume point; the run record makes a stop or failure visible.' }
    ];
    const buttons = states.map(state => {
      const button = make('button', 'case-interaction-choice', state.label);
      button.type = 'button';
      button.setAttribute('aria-pressed', 'false');
      controls.append(button);
      return button;
    });
    const labels = ['Dockets reached', 'Rows safely saved', 'Next run'];
    const outputs = make('div', 'case-interaction-outputs');
    const values = labels.map(label => {
      const cell = make('div', 'case-interaction-output');
      cell.append(make('span', 'case-interaction-label', label), make('strong', 'case-interaction-value', ''));
      outputs.append(cell);
      return cell.querySelector('.case-interaction-value');
    });
    const response = make('p', 'case-interaction-response');
    response.setAttribute('aria-live', 'polite');
    ledger.append(controls, outputs, response);
    const placeResponse = () => compactView.matches ? controls.after(response) : outputs.after(response);
    compactView.addEventListener('change', placeResponse);
    placeResponse();
    function select(index) {
      buttons.forEach((button, choice) => button.setAttribute('aria-pressed', String(choice === index)));
      values.forEach((value, position) => value.textContent = states[index].values[position]);
      outputs.classList.toggle('shows-correction', index === 1);
      response.textContent = states[index].message;
    }
    buttons.forEach((button, index) => button.addEventListener('click', () => select(index)));
    select(0);
    ledger.querySelector('.interaction-fallback').hidden = true;
  }

  const claimPath = document.querySelector('#claim-path .model-steps');
  if (claimPath) {
    const items = [...claimPath.querySelectorAll(':scope > li')];
    const details = [
      'Retain the ride, member and billing facts with their sources. A ride record alone does not prove that a claim is complete.',
      'Construct a version from supported facts. A missing billing-party reference stays missing rather than being inferred.',
      'Check the version against the intended recipient’s requirements. Ready to send is not the same as accepted.',
      'Keep the sent version and the recipient response. A rejection without a reason remains open for follow-up.'
    ];
    if (items.length === details.length) {
      const response = make('p', 'claim-stage-response');
      response.id = 'claim-stage-response';
      response.setAttribute('aria-live', 'polite');
      claimPath.after(response);
      const buttons = items.map(item => {
        const button = make('button', 'claim-stage-choice');
        button.type = 'button';
        button.setAttribute('aria-pressed', 'false');
        button.setAttribute('aria-controls', response.id);
        button.append(...item.childNodes);
        item.append(button);
        return button;
      });
      let selected = 0;
      const placeResponse = () => compactView.matches ? items[selected].append(response) : claimPath.after(response);
      compactView.addEventListener('change', placeResponse);
      function select(index) {
        selected = index;
        buttons.forEach((button, choice) => button.setAttribute('aria-pressed', String(choice === index)));
        items.forEach((item, choice) => item.classList.toggle('is-active', choice === index));
        response.replaceChildren(make('strong', '', buttons[index].querySelector('strong').textContent + '. '), document.createTextNode(details[index]));
        placeResponse();
      }
      buttons.forEach((button, index) => button.addEventListener('click', () => select(index)));
      select(0);
    }
  }

  // The three decisions come from the existing recorded synthetic case study.
  const claimExample = document.querySelector('#claim-example');
  if (claimExample) {
    const states = [
      { label: 'July 14 · version 1', compact: 'Jul 14 · v1', status: 'Blocked', evidence: 'Ride and member records exist; the required billing-party ID is unknown.', action: 'Get the billing reference before sending.' },
      { label: 'July 16 · version 2', compact: 'Jul 16 · v2', status: 'Ready to send', evidence: 'The reference arrives. Version 2 links its source and passes readiness checks.', action: 'Send version 2; retain version 1.' },
      { label: 'Recipient response', compact: 'Recipient response', status: 'Rejected', evidence: 'The response has no reason code.', action: 'Request the reason before correcting.' }
    ];
    const controls = make('div', 'case-interaction-controls');
    controls.setAttribute('role', 'group');
    controls.setAttribute('aria-label', 'Inspect the recorded synthetic claim path');
    const buttons = states.map(state => {
      const button = make('button', 'case-interaction-choice');
      button.type = 'button';
      button.setAttribute('aria-pressed', 'false');
      button.setAttribute('aria-label', state.label);
      button.append(make('span', 'claim-choice-full', state.label), make('span', 'claim-choice-compact', state.compact));
      controls.append(button);
      return button;
    });
    const panel = make('div', 'claim-example-panel');
    panel.setAttribute('aria-live', 'polite');
    claimExample.append(controls, panel);
    function select(index) {
      buttons.forEach((button, choice) => button.setAttribute('aria-pressed', String(choice === index)));
      panel.replaceChildren(make('strong', 'claim-example-status', states[index].status), make('p', '', states[index].evidence), make('p', 'claim-example-action', 'Next action: ' + states[index].action));
      panel.dataset.state = String(index);
    }
    buttons.forEach((button, index) => button.addEventListener('click', () => select(index)));
    select(0);
    claimExample.querySelector('.interaction-fallback').hidden = true;
  }

  // Local controls only pin while their measured stack leaves a useful phone viewport.
  const localPins = [...document.querySelectorAll('.ai-billing-controls, .revenue-rule-controls, .ai-capability-pin, #run-check .case-interaction-controls, #claim-example .case-interaction-controls')];
  const syncLocalPins = () => localPins.forEach(control => {
    const heading = control.closest('[data-cwds-section]')?.querySelector('.section-heading-bar');
    const stack = (heading?.getBoundingClientRect().height ?? 0) + control.getBoundingClientRect().height;
    const limit = control.matches('.ai-capability-pin, #claim-example .case-interaction-controls') ? 0.55 : 0.45;
    control.classList.toggle('mobile-pin-ready', compactView.matches && stack <= innerHeight * limit && innerHeight - stack >= 170);
  });
  const pinSizes = new ResizeObserver(syncLocalPins);
  localPins.forEach(control => pinSizes.observe(control));
  document.querySelectorAll('.cwds-section > .section-heading-bar').forEach(heading => pinSizes.observe(heading));
  addEventListener('resize', syncLocalPins);
  compactView.addEventListener('change', syncLocalPins);
  syncLocalPins();

  // A choice keeps its changing explanation clear of the floating reading index.
  [
    ['#ai-example .ai-billing-controls', '#ai-example .ai-billing-response'],
    ['#revenue .revenue-rule-controls', '#revenue .revenue-rule-explanation'],
    ['#run-check .case-interaction-controls', '#run-check .case-interaction-response'],
    ['#claim-example .case-interaction-controls', '#claim-example .claim-example-panel']
  ].forEach(([controlSelector, responseSelector]) => {
    const controls = document.querySelector(controlSelector);
    const response = document.querySelector(responseSelector);
    if (!controls || !response) return;
    controls.addEventListener('click', event => {
      if (!compactView.matches || !event.target.closest('button')) return;
      requestAnimationFrame(() => {
        const navTop = document.querySelector('.cwds-index-toggle')?.getBoundingClientRect().top ?? innerHeight;
        const safeBottom = Math.min(innerHeight - 8, navTop - 8);
        const result = response.getBoundingClientRect();
        if (result.bottom > safeBottom) scrollBy(0, result.bottom - safeBottom);
        else if (result.top < controls.getBoundingClientRect().bottom + 8) scrollBy(0, result.top - controls.getBoundingClientRect().bottom - 8);
      });
    });
  });
})();
