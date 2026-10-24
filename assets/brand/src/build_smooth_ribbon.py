"""Build smooth Ribbon geometry from source-coordinate design landmarks.

Developer regeneration: pip install numpy scipy pillow opencv-python-headless.
Normal CI consumes the checked-in master. Each run below is a C2-continuous
parametric cubic spline. Separate runs meet only at intentional pointed tips.
The raster and initial polygon conversion remain preserved for comparison.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
from scipy.interpolate import CubicSpline

HERE = Path(__file__).resolve().parent

# Ordered outlines, in the original 1536x1024 raster's coordinate system.
# The named joins are deliberate points, not pixel-trace stair steps.
SHAPES = {
    'tail': [
        [(738,512),(700,534),(665,562),(620,607),(573,654),(543,678),(522,692)],
        [(522,692),(551,691),(578,685),(612,665),(643,632),(676,580),(706,542),(738,512)],
    ],
    'body': [
        [(1293,297),(1188,301),(1109,308),(1056,314),(1000,293),(961,286),(922,298),(894,323),(871,358),(847,393)],
        [(847,393),(871,387),(894,388),(913,394),(927,403)],
        [(927,403),(897,395),(873,396),(845,404),(810,420),(769,439),(728,447),(691,447),(657,442),(621,431),(593,420),(567,403)],
        [(567,403),(590,437),(618,461),(650,483),(687,498),(729,505),(768,502)],
        [(768,502),(739,522),(713,548),(693,572),(672,610),(648,654),(622,689),(593,719)],
        [(593,719),(622,714),(650,695),(677,664),(707,626),(735,602),(770,591),(809,587),(858,572),(903,543),(940,498),(975,417),(1006,369),(1056,335),(1150,314),(1293,297)],
    ],
    'upper': [
        [(724,41),(700,50),(675,68),(654,91),(640,120),(636,147),(639,176),(651,205),(669,233),(693,263),(720,293),(746,322),(768,352),(782,378),(788,400),(788,419)],
        [(788,419),(815,406),(841,395),(843,393)],
        [(843,393),(844,380),(840,357),(830,333),(811,302),(792,274),(773,244),(756,216),(741,184),(729,151),(721,117),(719,88),(720,66),(724,41)],
    ],
    'teal': [
        [(607,148),(580,160),(558,185),(548,209),(549,236),(559,263),(578,290),(608,317),(643,341),(680,365),(708,389),(727,413),(737,433),(755,430),(771,425),(773,417),(768,392),(756,368),(737,342),(700,302),(662,263),(636,229),(617,192),(609,170),(607,148)],
    ],
    'lime': [
        [(532,266),(525,279),(521,296),(521,316),(525,336),(536,358),(553,378),(575,395),(600,410),(627,422),(656,430),(685,435),(706,436),(722,435)],
        [(722,435),(712,416),(697,398),(675,380),(654,365),(628,350),(600,332),(581,318),(557,296),(542,280),(532,266)],
    ],
}

def number(x):
    return f'{x:.4f}'.rstrip('0').rstrip('.')

def point(p):
    return ','.join(number(x) for x in p)

def fit_run(points):
    pts = np.array(points, dtype=float)
    t = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts,axis=0),axis=1))]
    spline = CubicSpline(t, pts, axis=0, bc_type='natural')
    commands=[]
    for i,dt in enumerate(np.diff(t)):
        a,b=pts[i:i+2]
        c1=a+spline(t[i],1)*dt/3
        c2=b-spline(t[i+1],1)*dt/3
        commands.append(f'C{point(c1)} {point(c2)} {point(b)}')
    # Dense samples support source-mask overlap and boundary-deviation checks.
    samples=spline(np.linspace(t[0],t[-1],max(2,int(t[-1]*4))))
    # A cubic spline is C2 at each interior knot; compare polynomial limits
    # directly instead of merely relying on the constructor's contract.
    errors=[]
    for i in range(1,len(t)-1):
        dt=t[i]-t[i-1]
        left1=3*spline.c[0,i-1]*dt**2+2*spline.c[1,i-1]*dt+spline.c[2,i-1]
        left2=6*spline.c[0,i-1]*dt+2*spline.c[1,i-1]
        errors.extend([np.max(np.abs(left1-spline.c[2,i])),np.max(np.abs(left2-2*spline.c[1,i]))])
    return ''.join(commands),samples,max(errors,default=0)

def main():
    from PIL import Image
    import cv2
    from scipy.spatial import cKDTree
    colors={'tail':'#103f39','body':'#103f39','upper':'#103f39','teal':'#3f8b84','lime':'#d5ed5d'}
    paths=[];samples={};continuity={};segments={}
    for name,runs in SHAPES.items():
        d='M'+point(runs[0][0]);samples[name]=[];errors=[]
        for run in runs:
            commands,sampled,error=fit_run(run)
            d+=commands;samples[name].extend(sampled);errors.append(error)
        paths.append(f'<path id="ribbon-{name}" fill="{colors[name]}" d="{d}Z"/>')
        continuity[name]=float(max(errors));segments[name]=sum(len(r)-1 for r in runs)
    master='<svg xmlns="http://www.w3.org/2000/svg" viewBox="500 30 820 700">\n'+'\n'.join(paths)+'\n</svg>\n'
    (HERE/'ribbon-master.svg').write_text(master,encoding='utf-8',newline='\n')
    im=np.array(Image.open(HERE/'ribbon-selected.png').convert('RGBA'))[:725]
    opaque=im[:,:,3]>=128;rgb=im[:,:,:3].astype(int)
    reference={'silhouette':opaque,
       'teal':opaque&(rgb[:,:,0]>30)&(rgb[:,:,0]<120)&(rgb[:,:,1]>90)&(rgb[:,:,2]>70),
       'lime':opaque&(rgb[:,:,0]>=120)&(rgb[:,:,1]>150)}
    masks={name:np.zeros(opaque.shape,dtype='uint8') for name in reference}
    for name,sampled in samples.items():
        contour=np.rint(sampled).astype('int32')
        cv2.fillPoly(masks['silhouette'],[contour],1)
        if name in ('teal','lime'):cv2.fillPoly(masks[name],[contour],1)
    comparison={}
    for name,mask in masks.items():
        ref=reference[name]
        union=np.logical_or(ref,mask)
        a,_=cv2.findContours(ref.astype('uint8'),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
        b,_=cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
        aa=np.concatenate([p[:,0,:] for p in a if cv2.contourArea(p)>80])
        bb=np.concatenate([p[:,0,:] for p in b if cv2.contourArea(p)>80])
        deviations=np.r_[cKDTree(aa).query(bb)[0],cKDTree(bb).query(aa)[0]]
        comparison[name]={'intersection_over_union':round(float(np.logical_and(ref,mask).sum()/union.sum()),5),
            'boundary_distance_95_percent_px':round(float(np.percentile(deviations,95)),3),
            'boundary_distance_max_px':round(float(deviations.max()),3)}
    receipt={'source_sha256':hashlib.sha256((HERE/'ribbon-selected.png').read_bytes()).hexdigest(),
      'conversion':'C2-continuous parametric cubic splines through source-coordinate design landmarks. Intentional pointed beak, feather and tail tips retained. No straight-line contour trace.',
      'color_treatment':'Separate solid-color feather shapes; no duplicate dark underlay below lime or teal. Reversed cuts change color only.',
      'continuity_max_derivative_error':continuity,'cubic_segment_count':segments,
      'geometry_comparison':comparison}
    (HERE/'ribbon-trace-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(receipt,indent=2))

if __name__=='__main__':main()
