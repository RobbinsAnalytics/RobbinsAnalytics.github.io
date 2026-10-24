#!/usr/bin/env python3
"""Export Ribbon paths and outlined A wordmarks from pinned local masters.

Developer regeneration only: pip install fonttools uharfbuzz.
CI rasterizes the checked-in SVGs with build_icons.py; no font/CDN dependency.
"""
from pathlib import Path
import hashlib
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
BRAND = ROOT / 'assets' / 'brand'
SRC = BRAND / 'src'
NS = {'s': 'http://www.w3.org/2000/svg'}
LIGHT = {'body':'#103f39', 'teal':'#3f8b84', 'lime':'#d5ed5d', 'word':'#0f1f1e', 'accent':'#1f6b63'}
DARK = {'body':'#d0e9e4', 'teal':'#69b8ac', 'lime':'#d5ed5d', 'word':'#ffffff', 'accent':'#83c7bc'}

def geometry(palette):
    master = ET.parse(SRC/'ribbon-master.svg').getroot()
    return ''.join(f'<path fill="{palette[p.attrib["id"].removeprefix("ribbon-")]}" d="{p.attrib["d"]}"/>' for p in master.findall('s:path',NS))

def svg(viewbox, contents, label='Robbins Analytics'):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{viewbox}" role="img" aria-label="{label}"><title>{label}</title>{contents}</svg>\n'

def symbol(palette):
    return svg('0 0 820 700',f'<g transform="translate(-500 -30)">{geometry(palette)}</g>')

def icon():
    # Identical bird geometry; the dark tile supplies contrast in either browser
    # theme. Vector paths, no embedded raster and no color-scheme dependency.
    return svg('0 0 1024 1024', '<rect x="8" y="8" width="1008" height="1008" rx="156" fill="#0f1f1e" stroke="#83c7bc" stroke-width="16"/>'
               +f'<g transform="translate(68 133) scale(1.08)"><g transform="translate(-500 -30)">{geometry(DARK)}</g></g>')

def outline(text, file, axes, size, tracking=-.025):
    import uharfbuzz as hb
    from fontTools.ttLib import TTFont
    from fontTools.varLib.instancer import instantiateVariableFont
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.pens.transformPen import TransformPen
    raw=(SRC/'ribbon-fonts'/file).read_bytes()
    font=TTFont(SRC/'ribbon-fonts'/file)
    font=instantiateVariableFont(font,axes,inplace=False)
    gs=font.getGlyphSet()
    hf=hb.Font(hb.Face(raw));hf.set_variations(axes)
    buf=hb.Buffer();buf.add_str(text);buf.guess_segment_properties();hb.shape(hf,buf)
    scale=size/font['head'].unitsPerEm
    pen=SVGPathPen(gs);x=0
    for info,pos in zip(buf.glyph_infos,buf.glyph_positions):
        trans=TransformPen(pen,(scale,0,0,-scale,x+pos.x_offset*scale,-pos.y_offset*scale))
        gs[font.getGlyphName(info.codepoint)].draw(trans)
        x+=pos.x_advance*scale + size*tracking
    return pen.getCommands(),x

def wordmark(palette):
    runs=[('Robbins ', 'InterTight.ttf',{'wght':600},'word'),
          ('Analytics','Fraunces-Italic.ttf',{'wght':400,'opsz':20.8,'SOFT':0,'WONK':1},'accent'),
          ('.','InterTight.ttf',{'wght':600},'accent')]
    x=0;parts=[]
    for text,file,axes,color in runs:
        d,width=outline(text,file,axes,40)
        parts.append(f'<path fill="{palette[color]}" transform="translate({x:.3f} 0)" d="{d}"/>')
        x+=width
    return ''.join(parts),x

def main():
    for name,p in [('robbins-mark.svg',LIGHT),('robbins-mark-reversed.svg',DARK)]:
        (BRAND/name).write_text(symbol(p),encoding='utf-8',newline='\n')
    (BRAND/'favicon.svg').write_text(icon(),encoding='utf-8',newline='\n')
    for suffix,p in [('',LIGHT),('-reversed',DARK)]:
        words,ww=wordmark(p)
        bird=geometry(p)
        for stacked in (False,True):
            if stacked:
                width=max(ww+32,176);height=204
                contents=f'<g transform="translate({(width-140)/2:.3f} 10) scale({140/820:.6f}) translate(-500 -30)">{bird}</g><g transform="translate({(width-ww)/2:.3f} 182)">{words}</g>'
                name='robbins-lockup-stacked'+suffix+'.svg'
            else:
                width=120+24+ww+20;height=128
                contents=f'<g transform="translate(8 12) scale({120/820:.6f}) translate(-500 -30)">{bird}</g><g transform="translate(152 75)">{words}</g>'
                name='robbins-lockup'+(suffix or '-primary')+'.svg'
            (BRAND/name).write_text(svg(f'0 0 {width:.3f} {height}',contents),encoding='utf-8',newline='\n')
    tracked=[SRC/'ribbon-selected.png',SRC/'ribbon-master.svg',*sorted((SRC/'ribbon-fonts').iterdir()),*sorted(BRAND.glob('*.svg'))]
    receipt={'decision':'A, horizontal; period retained and matches Analytics',
             'light_wordmark':{'Robbins':LIGHT['word'],'Analytics_and_period':LIGHT['accent']},
             'reversed_wordmark':{'Robbins':DARK['word'],'Analytics_and_period':DARK['accent']},
             'geometry':'Same Ribbon paths in every cut; favicon adds a contrast tile only',
             'sha256':{str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in tracked}}
    (SRC/'ribbon-asset-manifest.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('Exported Ribbon symbols, favicon and four outlined lockups.')

if __name__=='__main__': main()
