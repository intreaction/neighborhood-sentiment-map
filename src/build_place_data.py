"""Build compact real-data 2018–2019 profiles and existing metro ground geometry.

Reads the COMPLETE local Yelp archive, not the restricted project text cache.
Public output has coordinates and review counts only: no text, names or IDs.
Run ../.venv/bin/python src/build_place_data.py
"""
import argparse
import gzip
import hashlib
import json
import math
import tarfile
import time
from collections import Counter
from pathlib import Path
from project_registry import ROOT,load_registry
from place_data import BASELINE_YEARS,BUFFER_M,inside_bounds,padded_bounds,profile_at,profile_records
RAW=ROOT/'data/raw/yelp_academic_dataset_business.json'
ARCHIVE=ROOT/'Yelp JSON/yelp_dataset.tar'
INTERIM=ROOT/'data/interim'
CACHE=INTERIM/'place-baseline-2018-2019.json.gz'
OUT=ROOT/'web/place-data.json'
MAP_OUT=ROOT/'web/place-map.json'
LABELS={'Philadelphia':'Philadelphia','TampaBay':'Tampa Bay','Nashville':'Nashville','NewOrleans':'New Orleans','Tucson':'Tucson'}
CITY_IDS={'Philadelphia':'Philadelphia','Tampa':'TampaBay','Nashville':'Nashville','New Orleans':'NewOrleans','Tucson':'Tucson'}
VERSION='place-profile-2018-2019-v1'


def read_businesses(path=RAW):
    records={};missing=0;total=0
    with Path(path).open() as f:
        for line in f:
            b=json.loads(line);total+=1
            lon,lat=b.get('longitude'),b.get('latitude')
            if not all(isinstance(x,(int,float)) and math.isfinite(x) for x in (lon,lat)) or not -180<=lon<=180 or not -90<=lat<=90:
                missing+=1;continue
            records[b['business_id']]=(lon,lat)
    return records,{'source_business_records':total,'businesses_with_valid_coordinates':len(records),'missing_or_invalid_coordinates':missing}


def count_reviews(rebuild=False):
    st=ARCHIVE.stat();signature=hashlib.sha256(json.dumps([VERSION,BASELINE_YEARS,st.st_size,st.st_mtime_ns]).encode()).hexdigest()
    if CACHE.exists() and not rebuild:
        with gzip.open(CACHE,'rt') as f:cached=json.load(f)
        if cached.get('signature')==signature:
            print('Reusing complete-archive baseline counts',flush=True);return cached
    counts=Counter();year_counts=Counter();scanned=0;start=time.monotonic()
    with tarfile.open(ARCHIVE,'r|*') as archive:
        for member in archive:
            if member.name.endswith('yelp_academic_dataset_review.json'):
                for line in archive.extractfile(member):
                    r=json.loads(line);scanned+=1
                    year=int(r['date'][:4])
                    if year in BASELINE_YEARS:counts[r['business_id']]+=1;year_counts[str(year)]+=1
                    if scanned%1000000==0:print(f'Scanned {scanned:,}; baseline reviews {sum(year_counts.values()):,}; {time.monotonic()-start:.1f}s',flush=True)
                break
    if not scanned:raise ValueError('Missing or empty review archive member')
    result={'signature':signature,'baseline_years':list(BASELINE_YEARS),'source_reviews_scanned':scanned,'baseline_reviews_all_source_geographies':sum(year_counts.values()),'baseline_reviews_by_year':dict(year_counts),'seconds':round(time.monotonic()-start,2),'review_counts':dict(counts)}
    with gzip.open(CACHE,'wt') as f:json.dump(result,f,separators=(',',':'))
    return result


def project_center(project):
    g=project['geometry']
    if g['kind']=='center_proxy':return [g['longitude'],g['latitude']]
    source=json.loads((ROOT/g['path']).read_text());geom=source.get('geometry') or source['features'][0]['geometry'];coords=[]
    def visit(value):
        if value and isinstance(value[0],(int,float)):coords.append(value)
        else:
            for c in value:visit(c)
    visit(geom['coordinates'])
    return [(min(c[0] for c in coords)+max(c[0] for c in coords))/2,(min(c[1] for c in coords)+max(c[1] for c in coords))/2]


def build_payload(businesses,audit,counts,extents,projects):
    cities=[];source_records=[[round(lon,6),round(lat,6),counts['review_counts'].get(bid,0)] for bid,(lon,lat) in businesses.items()]
    for cid,bounds in extents.items():
        buffer=padded_bounds(bounds);records=sorted((r for r in source_records if inside_bounds(r[0],r[1],buffer)),key=lambda r:(r[0],r[1],r[2]))
        cities.append({'id':cid,'label':LABELS[cid],'center':[(bounds[0]+bounds[2])/2,(bounds[1]+bounds[3])/2],'bounds':bounds,'record_bounds':buffer,'buffer_m':BUFFER_M,'businesses':records,'inventory_businesses':len(records),'baseline_reviewed_businesses':sum(r[2]>0 for r in records),'baseline_reviews':sum(r[2] for r in records)})
    payload={'version':VERSION,'baseline_years':list(BASELINE_YEARS),'source_label':'Yelp Open Dataset January 2022 archive; retrospective 2018–2019 review baseline','record_fields':['longitude','latitude','reviews_2018_2019'],'radius_m':500,
     'cities':cities,'projects':[{'id':p['id'],'name':p['project'],'city_id':CITY_IDS.get(p['city']),'city_label':p['city'],'center':project_center(p),'project_type':p['project_type'],'cost_millions':p['cost_millions'],'geometry_quality':p['geometry_quality']} for p in projects],
     'coverage':{**audit,'source_reviews_scanned':counts['source_reviews_scanned'],'baseline_reviews_all_source_geographies':counts['baseline_reviews_all_source_geographies'],'baseline_reviews_by_year':counts['baseline_reviews_by_year'],'count_method':'Full raw review archive; all source businesses considered. City records selected by coordinates with 1000 m padding; no business city-name or ZIP filter.','bounds_method':'Existing five-atlas metro map extents define the supported analysis interface, not complete Yelp market coverage.','no_coverage':'Outside all city bounds: unavailable. No observed listings within 500 m: no inventory coverage, not measured zero activity. Listings but no 2018–2019 reviews: no baseline review support.','completeness':'Archive observations, not a census of businesses or all visits. Historical business coordinates are the archive snapshot, not verified 2018 addresses.','period_note':'Fixed pre-COVID 2018–2019 baseline for every chosen point; not current activity and not the project-specific windows used to train historical outcomes.','target_note':'The model predicts excess reviews over two post-opening years per $1M; this is not an annual rate.','center_note':'Project centers are navigation anchors. A 500 m circle around an anchor differs from a full project-footprint catchment.','published_business_records':sum(len(c['businesses']) for c in cities),'raw_review_text_published':False,'raw_business_or_review_ids_published':False}}
    # Audit every historical center with the SAME fixed period; do not tune a window.
    center_audit=[]
    for p in payload['projects']:
        profile=profile_records(source_records,*p['center'])
        center_audit.append({'id':p['id'],'name':p['name'],'center':p['center'],'in_supported_city_bounds':profile_at(payload,*p['center'])['status']!='outside_coverage',**profile})
    return payload,center_audit


def build_map(extents):
    zips=json.loads((INTERIM/'metro_zips.json').read_text());metro_of={z:m for m,zs in zips.items() for z in zs}
    source=json.loads((INTERIM/'zcta_boundaries.min.geojson').read_text());features={m:[] for m in extents}
    for f in source['features']:
        z=f['properties']['zip'];metro=metro_of.get(z)
        if metro in features:features[metro].append({'type':'Feature','properties':{'zip':z,'metro':metro},'geometry':f['geometry']})
    return {'version':'atlas-ground-geometry-v1','source':'Existing simplified Census ZCTA atlas polygons; geographic ground context, not actual building footprints or heights.','cities':[{'id':m,'label':LABELS[m],'center':[(b[0]+b[2])/2,(b[1]+b[3])/2],'bounds':b,'features':features[m]} for m,b in extents.items()]}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--rebuild-counts',action='store_true');args=parser.parse_args()
    businesses,audit=read_businesses();counts=count_reviews(args.rebuild_counts);extents=json.loads((INTERIM/'metro_extents.json').read_text())
    payload,center_audit=build_payload(businesses,audit,counts,extents,load_registry())
    OUT.write_text(json.dumps(payload,separators=(',',':'),allow_nan=False)+'\n');MAP_OUT.write_text(json.dumps(build_map(extents),separators=(',',':'),allow_nan=False)+'\n')
    (INTERIM/'place-center-profile-audit.json').write_text(json.dumps(center_audit,indent=2)+'\n')
    for p in center_audit:print(p['name'],p['inventory_businesses'],p['baseline_reviewed_businesses'],p['baseline_reviews'],p['reviews_per_business'],p['status'],flush=True)
    print('Wrote',OUT,OUT.stat().st_size,'bytes;',MAP_OUT,MAP_OUT.stat().st_size,'bytes',flush=True)
if __name__=='__main__':main()
