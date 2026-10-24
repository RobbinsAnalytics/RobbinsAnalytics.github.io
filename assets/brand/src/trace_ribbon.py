"""Trace the selected raster's opaque artwork, excluding transparent glow/noise.

One-time source conversion: pip install pillow numpy opencv-python-headless.
The committed SVG is the production geometry master; normal builds do not trace.
No scaling, rotation or alternate silhouette is introduced. The 128-alpha mask
is checked against the final paths by build_ribbon_assets.py's source receipt.
"""
from pathlib import Path
import hashlib, json
import cv2
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
im = np.array(Image.open(HERE / 'ribbon-selected.png').convert('RGBA'))
# The source's wordmark starts below this boundary; only the bird is traced.
im = im[:725]
opaque = im[:, :, 3] >= 128
rgb = im[:, :, :3].astype(int)
masks = {
    'body': opaque,
    'teal': opaque & (rgb[:,:,0] > 30) & (rgb[:,:,0] < 120)
            & (rgb[:,:,1] > 90) & (rgb[:,:,2] > 70),
    'lime': opaque & (rgb[:,:,0] >= 120) & (rgb[:,:,1] > 150),
}
colors = {'body': '#103f39', 'teal': '#3f8b84', 'lime': '#d5ed5d'}
paths = []
metrics = {}
for name,mask in masks.items():
    contours, _ = cv2.findContours(mask.astype('uint8'), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = [c for c in contours if cv2.contourArea(c) > 80]
    ds = []
    traced = np.zeros(mask.shape, dtype='uint8')
    for c in contours:
        # Less than 0.1 CSS px deviation at the 60px header width.
        p = cv2.approxPolyDP(c, .85, True)
        cv2.fillPoly(traced, [p], 1)
        pts = p[:,0,:]
        ds.append('M' + ' '.join(f'{x},{y}' if i == 0 else f'L{x},{y}' for i,(x,y) in enumerate(pts)) + 'Z')
    paths.append(f'<path id="ribbon-{name}" fill="{colors[name]}" d="{" ".join(ds)}"/>')
    union=np.logical_or(mask,traced)
    metrics[name]={'intersection_over_union':round(np.logical_and(mask,traced).sum()/union.sum(),5), 'contours':len(contours)}
svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="500 30 820 700">\n'+'\n'.join(paths)+'\n</svg>\n'
(HERE/'ribbon-master.svg').write_text(svg, encoding='utf-8',newline='\n')
receipt={'source_sha256':hashlib.sha256((HERE/'ribbon-selected.png').read_bytes()).hexdigest(),
         'conversion':'Opaque contours, alpha >=128; polygons simplified by at most .85 source pixels; soft glow and raster color noise excluded.',
         'color_treatment':'Flat representative source colors; reversed colors are an application variant.',
         'geometry_comparison':metrics}
(HERE/'ribbon-trace-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(receipt,indent=2))
