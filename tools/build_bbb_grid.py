#!/usr/bin/env python3
"""Draw the actual extended matrix, with outcomes separate from artifacts."""
import html, json, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
def read(p): return json.loads((ROOT/p).read_text(encoding='utf-8'))
def main():
    rows=read('data/build-by-build.json'); prov=read('data/build-by-build.provenance.json')
    cells=read(prov['cell_evidence']['path']); catalog=read(prov['catalog']['path'])
    for entry in [prov,prov['baseline'],prov['extension'],prov['cell_evidence'],prov['catalog']]:
        path=entry.get('path','data/build-by-build.json')
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==entry['sha256'],path
    groups=['Data','Numbers','Presentation','Operation']
    ordered=[s for g in groups for s in catalog if s['group']==g]
    assert len(rows)==11 and len(ordered)==16
    parts=[]
    for row in sorted(rows,key=lambda r:r['first_commit']):
        assert set(row['surfaces'])=={s['id'] for s in ordered}
        for s in ordered:
            c=cells[row['key']][s['id']];state=c['state'];latest=' is-latest' if row['key']=='cascadia-claim-integrity' else ''
            title=html.escape(row['name']+' / '+s['label']+': '+state.replace('_',' ')+'; '+c['result'],quote=True)
            parts.append(f'<span class="fx-matrix__cell is-{state}{latest}{" is-on" if state=="recorded" else ""}" title="{title}" data-build="{row["key"]}" data-surface="{s["id"]}"></span>')
    names={'Data':'Data','Numbers':'Numbers','Presentation':'Display','Operation':'Ops'}
    bands=''.join(f'<span class="fx-matrix__band" style="--span:{sum(s["group"]==g for s in ordered)}">{names[g]}</span>' for g in groups)
    desc='Eleven builds in first-commit order by sixteen test surfaces. Solid lime: artifact recorded. Split amber: limited evidence. Dim: not carried in the original inventory. Dashed: not assessed. Last row, outlined: Claim Integrity. An artifact is not a pass rating. Original ten-build baseline October 7, 2026; additive Claim Integrity extension October 19, 2026. Open the full matrix for labels, evidence, recorded outcomes and definitions.'
    out=f'''<!-- Generated from the pinned additive inventory; do not edit. -->
<div class="fx-matrix" data-rows="11" data-cols="16">
<div class="fx-matrix__bands" aria-hidden="true">{bands}</div>
<div class="fx-matrix__grid" role="img" aria-label="{html.escape(desc,quote=True)}" style="--cols:16">{''.join(parts)}</div>
<p class="fx-matrix__caption">11 builds × 16 test surfaces</p>
<p class="fx-matrix__legend">Solid: recorded · Split: limited<br>Dim: not carried · Dashed: not assessed</p>
<p class="fx-matrix__new">Last row: Claim Integrity. Artifacts are not pass ratings.</p>
</div>\n'''
    p=ROOT/'_generated/bbb-grid.html';p.parent.mkdir(exist_ok=True);p.write_text(out,encoding='utf-8',newline='\n')
    print('Wrote homepage matrix: 11 × 16, four evidence states.')
if __name__=='__main__': main()
