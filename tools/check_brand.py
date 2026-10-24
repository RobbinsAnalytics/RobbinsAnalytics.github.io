#!/usr/bin/env python3
"""Verify Ribbon delivery and preserve each page's existing preview image.

--rendered checks _site; --origin checks deployed bytes after build.txt is known
to serve the merge commit. Source manifests are checked in either mode.
"""
import argparse
import hashlib
from html.parser import HTMLParser
import json
import re
from pathlib import Path
import struct
from urllib.request import urlopen, Request
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET
import yaml

ROOT=Path(__file__).resolve().parent.parent
BRAND=ROOT/'assets/brand'

class Head(HTMLParser):
    def __init__(self):
        super().__init__();self.meta={};self.icons=[];self.images=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='meta':self.meta[a.get('property',a.get('name',''))]=a.get('content','')
        if tag=='link' and 'icon' in a.get('rel',''):self.icons.append(a.get('href',''))
        if tag=='img':self.images.append(a)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--rendered',action='store_true');ap.add_argument('--origin');ap.add_argument('--cache-bust',default='ribbon');args=ap.parse_args()
    checks=0
    def require(ok,message):
        nonlocal checks
        if not ok:raise AssertionError(message)
        checks+=1
    receipt=json.loads((BRAND/'src/ribbon-asset-manifest.json').read_text())
    for name,digest in receipt['sha256'].items():
        require(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,'Changed vector/font master: '+name)
    master=ET.parse(BRAND/'src/ribbon-master.svg').getroot()
    master_paths=master.findall('{http://www.w3.org/2000/svg}path')
    require(len(master_paths)==5,'Ribbon must have five separate shapes, without duplicate feather underlays')
    for path in master_paths:
        commands=set(re.findall(r'[A-Za-z]',path.attrib['d']))
        require(commands=={'M','C','Z'},'Ribbon outlines must use cubic curves rather than polygon contour segments')
    for color in ('#d5ed5d','#3f8b84'):
        require(sum(p.attrib.get('fill')==color for p in master_paths)==1,'Colored feathers must have one solid shape each')
    svg_names=['robbins-mark.svg','robbins-mark-reversed.svg','robbins-lockup-primary.svg','robbins-lockup-reversed.svg','robbins-lockup-stacked.svg','robbins-lockup-stacked-reversed.svg','favicon.svg']
    for name in svg_names:
        el=ET.parse(BRAND/name).getroot()
        require(bool(el.findall('.//{http://www.w3.org/2000/svg}path')),name+' lacks vector paths')
        require(not any(x.tag.rsplit('}',1)[-1] in ('image','text','script') for x in el.iter()),name+' contains raster, text or script')
    pngs={'favicon-16.png':(16,16),'favicon-32.png':(32,32),'apple-touch-icon.png':(180,180),'icon-512.png':(512,512),'avatar-512.png':(512,512),'avatar-512-dark.png':(512,512)}
    for name,dimensions in pngs.items():
        raw=(BRAND/name).read_bytes();require(struct.unpack('>II',raw[16:24])==dimensions,name+' has wrong dimensions')
    if args.origin or args.rendered:
        def get(path):
            if args.origin:
                url=urljoin(args.origin.rstrip('/')+'/',path)+'?brand='+args.cache_bust
                return urlopen(Request(url,headers={'User-Agent':'Robbins-brand-check/1'}),timeout=30).read()
            return (ROOT/'_site'/path.lstrip('/')).read_bytes()
        for name in svg_names+[p.name for p in sorted(BRAND.glob('*.png'))]:
            path='assets/brand/'+name
            require(get(path)==(ROOT/path).read_bytes(),'Rendered/live asset differs: '+path)
        pages=0;previews=0
        for source in [*ROOT.glob('*.qmd'),*ROOT.glob('projects/*.qmd')]:
            path=source.relative_to(ROOT).with_suffix('.html').as_posix()
            text=get(path).decode('utf-8');head=Head();head.feed(text)
            require(head.meta.get('og:site_name')=='Robbins Analytics','Wrong site name: '+path)
            for icon in ['favicon.svg','favicon-16.png','favicon-32.png','apple-touch-icon.png']:
                require(any(urlparse(x).path.endswith('/assets/brand/'+icon) for x in head.icons),'Missing '+icon+' in '+path)
            symbol=[i for i in head.images if i.get('class')=='ra-brand-symbol']
            require(len(symbol)==1 and symbol[0].get('alt')=='','Header must contain one decorative symbol: '+path)
            require('Robbins <em>Analytics</em>' in text,'Missing live wordmark: '+path)
            fm=yaml.safe_load(source.read_text(encoding='utf-8').split('---',2)[1])
            expected=fm.get('image')
            if expected:
                for key in ('og:image','twitter:image'):
                    require(head.meta.get(key)==expected,'Preview changed: '+path+' '+key)
                local=urlparse(expected).path.lstrip('/')
                if (ROOT/local).exists():require(bool(get(local)),'Missing preview image: '+local)
                previews+=1
            pages+=1
        print(f'Checked {pages} generated pages; preserved {previews} page-specific OG/Twitter images.')
    print(f'Ribbon brand checks passed ({checks} assertions).')

if __name__=='__main__':main()
