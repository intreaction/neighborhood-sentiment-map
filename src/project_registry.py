"""Canonical project registry and geography shared by evidence and prediction."""
import csv
import json
import math
from collections import defaultdict
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / 'data/project_registry.json'
BUSINESSES = ROOT / 'data/raw/yelp_academic_dataset_business.json'


def load_registry(path=REGISTRY):
    projects = json.loads(Path(path).read_text())['projects']
    assert len({p['id'] for p in projects}) == len(projects), 'Project IDs must be unique'
    for p in projects:
        assert not set(p['pre_years']) & set(p['post_years']), 'Periods must not overlap'
    return projects


def xy(coords, lon0, lat0):
    coords = np.asarray(coords)
    return np.column_stack(((coords[:, 0]-lon0)*111320*math.cos(math.radians(lat0)), (coords[:, 1]-lat0)*111320))


def project_distances(project, locations):
    g = project['geometry']
    if g['kind'] == 'center_proxy':
        return np.linalg.norm(xy(locations, g['longitude'], g['latitude']), axis=1)
    # Imported lazily to avoid matplotlib startup during text worker initialization.
    from matplotlib.path import Path as PlotPath
    raw = json.loads((ROOT / g['path']).read_text())
    geom = raw.get('geometry') or raw['features'][0]['geometry']
    polygon = geom['type'] == 'Polygon'
    if geom['type'] not in ('Polygon', 'MultiLineString'):
        raise ValueError('Unsupported geometry '+geom['type'])
    rings = geom['coordinates']
    coords = np.vstack(rings)
    lon0, lat0 = np.mean(coords, axis=0)
    paths = [xy(r,lon0,lat0) for r in rings]
    sampled=[]
    for path in paths:
        if polygon and not np.array_equal(path[0],path[-1]):path=np.vstack((path,path[0]))
        for a,b in zip(path[:-1],path[1:]):
            n=max(1,math.ceil(float(np.linalg.norm(b-a))/10))
            sampled.append(a+np.linspace(0,1,n,endpoint=False)[:,None]*(b-a))
    pts=xy(locations,lon0,lat0)
    dist=cKDTree(np.vstack(sampled)).query(pts,workers=-1)[0]
    if polygon:
        inside=PlotPath(paths[0]).contains_points(pts)
        for hole in paths[1:]:inside &= ~PlotPath(hole).contains_points(pts)
        dist[inside]=0
    return dist


def build_cohorts(projects, business_path=BUSINESSES):
    """Spatial selection by coordinates, without city or state-name cutoffs."""
    businesses={}; spatial_businesses=[]
    fixture_ids=set()
    for p in projects:
        if p.get('cohort_fixture'):
            with (ROOT/p['cohort_fixture']).open() as f:fixture_ids.update(r['business_id'] for r in csv.DictReader(f))
    with Path(business_path).open() as f:
        for line in f:
            b=json.loads(line)
            if b['business_id'] in fixture_ids:businesses[b['business_id']]=b
            if all(isinstance(b.get(k),(int,float)) and math.isfinite(b[k]) for k in ('latitude','longitude')) and -90 <= b['latitude'] <= 90 and -180 <= b['longitude'] <= 180:
                businesses[b['business_id']]=b;spatial_businesses.append(b)
    assignment=defaultdict(list); inventories={}
    for p in projects:
        inventories[p['id']]={'near':[],'far':[]}
        if p.get('cohort_fixture'):
            with (ROOT/p['cohort_fixture']).open() as f:
                for row in csv.DictReader(f):
                    bid,band=row['business_id'],row['band']
                    if bid not in businesses:raise ValueError('Unresolved fixture business '+bid)
                    assignment[bid].append((p['id'],band));inventories[p['id']][band].append(bid)
        else:
            pool=spatial_businesses
            distances=project_distances(p,[(b['longitude'],b['latitude']) for b in pool])
            for b,d in zip(pool,distances):
                band='near' if d <= 500 else 'far' if 1500 < d <= 8000 else None
                if band:
                    assignment[b['business_id']].append((p['id'],band));inventories[p['id']][band].append(b['business_id'])
    return dict(assignment),inventories,businesses
