// Keep meaningful labels at reading size. The locator retains the complete map.
for (const diagram of document.querySelectorAll('.map-view svg.map, .map-view svg.network')) {
  diagram.querySelectorAll('[data-route-color]').forEach(e=>e.style.setProperty('--edge-color',e.dataset.routeColor));
  diagram.querySelectorAll('[data-role-color]').forEach(e=>e.style.setProperty('--badge-color',e.dataset.roleColor));
  const original = diagram.viewBox.baseVal;
  const full = { x: original.x, y: original.y, width: original.width, height: original.height };
  const panel = diagram.closest('.view-panel');
  const reader = document.createElement('div');
  reader.className = 'map-reader';
  reader.dataset.variant = diagram.classList.contains('wide') ? 'wide' : diagram.classList.contains('compact') ? 'compact' : 'single';
  const id = panel.id + '-reader-' + reader.dataset.variant;
  reader.innerHTML = `<div class="map-reader-tools" aria-label="Map detail controls">
    <span class="map-reader-title">Readable map</span>
    <div class="map-pan"><button type="button" data-pan="left" aria-label="Move map view left">←</button><button type="button" data-pan="up" aria-label="Move map view up">↑</button><button type="button" data-pan="down" aria-label="Move map view down">↓</button><button type="button" data-pan="right" aria-label="Move map view right">→</button></div>
    <div class="map-zoom"><button type="button" data-zoom="out" aria-label="Zoom map out">−</button><button type="button" data-zoom="in" aria-label="Zoom map in">+</button><button type="button" data-reset>Reset view</button></div>
    <label class="map-jump" for="${id}-jump">Find connector<select id="${id}-jump"><option value="">Choose a number…</option></select></label>
  </div><div class="map-reader-stage"><div class="map-detail" role="region" aria-label="Readable diagram. Drag to move the view, or use the direction buttons." tabindex="0"></div><div class="map-locator-wrap"><span>Whole map · select an area</span><button type="button" class="map-locator" aria-label="Whole-map locator. Click an area to show it in detail. Direction buttons provide a keyboard alternative." tabindex="-1"></button></div></div><p class="map-reader-status" aria-live="polite"></p>`;
  diagram.before(reader);
  const detail = reader.querySelector('.map-detail');
  detail.append(diagram);
  const locator = reader.querySelector('.map-locator');
  const mini = diagram.cloneNode(true);
  mini.removeAttribute('class');
  mini.removeAttribute('id');
  mini.removeAttribute('aria-labelledby');
  mini.setAttribute('aria-hidden', 'true');
  mini.setAttribute('focusable', 'false');
  mini.querySelectorAll('text,title,desc').forEach(e => e.remove());
  mini.querySelectorAll('[id]').forEach(e => e.removeAttribute('id'));
  mini.querySelectorAll('[data-connector]').forEach(e => { e.removeAttribute('data-connector'); e.removeAttribute('data-role-color'); });
  // Referenced marker IDs remain on the original diagram and are unique per view.
  const windowBox = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
  windowBox.setAttribute('class', 'map-window');
  mini.append(windowBox);
  locator.append(mini);
  const overview=document.createElement('div');
  overview.className='map-reader-overview';
  const overviewCopy=document.createElement('div');
  overviewCopy.innerHTML='<strong>Whole map + readable detail</strong>';
  overviewCopy.append(reader.querySelector('.map-reader-status'));
  overview.append(overviewCopy,reader.querySelector('.map-locator-wrap'));
  reader.prepend(overview);
  const jump = reader.querySelector('select');
  const badges = [...diagram.querySelectorAll('[data-connector]')].sort((a,b) => a.dataset.connector.localeCompare(b.dataset.connector, undefined, {numeric:true}));
  badges.forEach(badge => {
    const option = document.createElement('option');
    option.value = badge.dataset.connector;
    const entry = panel.querySelector(`[data-connector-key="${option.value}"]`);
    option.textContent = `${option.value} · ${entry.querySelector('strong').textContent}`;
    jump.append(option);
  });
  let x=full.x, y=full.y, scale=1, floor=1, width=0, height=0, ready=false;
  const clamp = (n, lo, hi) => Math.max(lo, Math.min(n, Math.max(lo, hi)));
  function render() {
    if (!width) return;
    const w=Math.min(full.width,width/scale), h=Math.min(full.height,height/scale);
    x=clamp(x,full.x,full.x+full.width-w);
    y=clamp(y,full.y,full.y+full.height-h);
    // Use an exact aspect ratio so SVG's meet scaling cannot reduce label size.
    diagram.setAttribute('viewBox',`${x} ${y} ${width/scale} ${height/scale}`);
    for(const [key,value] of Object.entries({x,y,width:w,height:h})) windowBox.setAttribute(key,value);
    for(const button of reader.querySelectorAll('[data-pan]')) {
      const side=button.dataset.pan;
      button.disabled = side==='left' ? x<=full.x+.1 : side==='up' ? y<=full.y+.1 : side==='right' ? x+w>=full.x+full.width-.1 : y+h>=full.y+full.height-.1;
    }
    reader.querySelector('[data-zoom=out]').disabled=scale<=floor+.001;
    reader.querySelector('[data-zoom=in]').disabled=scale>=floor*3-.001;
    const cropped=w<full.width-.1 || h<full.height-.1;
    reader.querySelector('.map-reader-status').textContent=cropped ? 'Detail view · labels stay at reading size. Use the locator, direction buttons or Find connector to explore the whole map.' : 'The whole map is visible at reading size.';
    reader.dispatchEvent(new CustomEvent('mapviewchange',{bubbles:true}));
  }
  function layout() {
    width=detail.clientWidth;
    if (!width) return;
    const fonts=[...diagram.querySelectorAll('text')].map(e=>parseFloat(getComputedStyle(e).fontSize)).filter(n=>n>0);
    floor=12.2/Math.min(...fonts);
    if(!ready) {scale=floor;ready=true;}
    scale=Math.max(scale,floor);
    height=Math.min(full.height*scale, Math.max(360,Math.min(620,window.innerHeight*.7)));
    detail.style.height=height+'px';
    render();
  }
  diagram.revealConnector=badge => {
    if(!width) layout();
    const circle=badge.querySelector('circle:not(.connector-hit)');
    const cx=Number(circle.getAttribute('cx')), cy=Number(circle.getAttribute('cy'));
    const w=width/scale,h=height/scale;
    if(cx<x+24 || cx>x+w-24 || cy<y+24 || cy>y+h-24) {
      x=cx-w/2;y=cy-h/2;render();
    }
  };
  reader.querySelectorAll('[data-pan]').forEach(button=>button.addEventListener('click',()=>{
    const side=button.dataset.pan;
    x+=({left:-1,right:1}[side]||0)*width/scale*.65;
    y+=({up:-1,down:1}[side]||0)*height/scale*.65;
    render();
  }));
  reader.querySelectorAll('[data-zoom]').forEach(button=>button.addEventListener('click',()=>{
    const cx=x+width/scale/2,cy=y+height/scale/2;
    scale=clamp(scale*(button.dataset.zoom==='in'?1.3:1/1.3),floor,floor*3);
    x=cx-width/scale/2;y=cy-height/scale/2;render();
  }));
  reader.querySelector('[data-reset]').addEventListener('click',()=>{x=full.x;y=full.y;scale=floor;jump.value='';layout();});
  jump.addEventListener('change',()=>{
    const badge=badges.find(b=>b.dataset.connector===jump.value);
    if(badge){
      diagram.revealConnector(badge);
      const bounds=badge.getBoundingClientRect();
      const tabs=badge.closest('[data-level]').querySelector('.view-tabs').getBoundingClientRect();
      const top=Math.max(0,tabs.bottom)+8;
      if(bounds.top<top)window.scrollBy({top:bounds.top-top,behavior:'instant'});
      else if(bounds.bottom>innerHeight-8)window.scrollBy({top:bounds.bottom-innerHeight+8,behavior:'instant'});
      badge.focus({preventScroll:true});
    }
  });
  locator.addEventListener('click',event=>{
    const box=locator.getBoundingClientRect();
    x=full.x+(event.clientX-box.left)/box.width*full.width-width/scale/2;
    y=full.y+(event.clientY-box.top)/box.height*full.height-height/scale/2;
    render();
  });
  let drag;
  detail.addEventListener('pointerdown',event=>{
    if(event.target.closest('[data-connector]') || event.button!==0)return;
    drag={clientX:event.clientX,clientY:event.clientY,x,y};
    detail.setPointerCapture(event.pointerId);
  });
  detail.addEventListener('pointermove',event=>{
    if(!drag)return;
    x=drag.x-(event.clientX-drag.clientX)/scale;y=drag.y-(event.clientY-drag.clientY)/scale;render();
  });
  for(const name of ['pointerup','pointercancel'])detail.addEventListener(name,()=>{drag=null;});
  detail.addEventListener('keydown',event=>{
    if(event.target!==detail)return;
    const side={ArrowLeft:'left',ArrowRight:'right',ArrowUp:'up',ArrowDown:'down'}[event.key];
    if(side){event.preventDefault();reader.querySelector(`[data-pan=${side}]`).click();}
  });
  new ResizeObserver(layout).observe(detail);
  diagram.closest('details')?.addEventListener('toggle',layout);
  window.addEventListener('beforeprint',()=>diagram.setAttribute('viewBox',`${full.x} ${full.y} ${full.width} ${full.height}`));
  window.addEventListener('afterprint',layout);
  layout();
}
