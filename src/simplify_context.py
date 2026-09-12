"""Shrink the water/road/county context so the page loads fast.

Roads and shorelines arrive at survey resolution; at metro zoom a ~200 m
tolerance is invisible. Lines are simplified open, polygons closed.
"""
import json, sys
from pathlib import Path
sys.setrecursionlimit(200_000)
ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data/interim/map_context.geojson"
OUT = ROOT / "data/interim/map_context.min.geojson"
TOL = {"water": 0.0020, "road": 0.0030, "county": 0.0060}
PREC = 4

def _perp(p,a,b):
    (px,py),(ax,ay),(bx,by)=p,a,b
    dx,dy=bx-ax,by-ay
    if dx==0 and dy==0: return ((px-ax)**2+(py-ay)**2)**.5
    t=max(0.,min(1.,((px-ax)*dx+(py-ay)*dy)/(dx*dx+dy*dy)))
    return ((px-(ax+t*dx))**2+(py-(ay+t*dy))**2)**.5

def rdp(pts,tol):
    if len(pts)<3: return pts
    dmax,idx=0.,0
    for i in range(1,len(pts)-1):
        d=_perp(pts[i],pts[0],pts[-1])
        if d>dmax: dmax,idx=d,i
    if dmax<=tol: return [pts[0],pts[-1]]
    return rdp(pts[:idx+1],tol)[:-1]+rdp(pts[idx:],tol)

def simp(c,depth,tol,closed):
    if depth==1:
        o=rdp(c,tol)
        if closed:
            if len(o)<4: o=c[::max(1,len(c)//8)]
            if o[0]!=o[-1]: o.append(o[0])
        elif len(o)<2:
            return None
        return [[round(x,PREC),round(y,PREC)] for x,y in o]
    out=[simp(x,depth-1,tol,closed) for x in c]
    out=[x for x in out if x]
    return out or None

DEPTH={"Polygon":2,"MultiPolygon":3,"LineString":1,"MultiLineString":2}
def main():
    gj=json.loads(SRC.read_text()); keep=[]
    for f in gj["features"]:
        g=f.get("geometry") or {}; d=DEPTH.get(g.get("type"))
        if not d: continue
        kind=f["properties"]["kind"]
        closed=g["type"] in ("Polygon","MultiPolygon")
        c=simp(g["coordinates"],d,TOL.get(kind,0.003),closed)
        if not c: continue
        g["coordinates"]=c
        keep.append({"type":"Feature","geometry":g,
                     "properties":{"k":kind[0],"m":f["properties"]["metro"]}})
    OUT.write_text(json.dumps({"type":"FeatureCollection","features":keep},separators=(",",":")))
    print(f"{len(gj['features'])} -> {len(keep)} features")
    print(f"{SRC.stat().st_size/1e6:.2f} MB -> {OUT.stat().st_size/1e6:.2f} MB")
main()
