from pathlib import Path
import json,hashlib,math
import pandas as pd
from shapely.geometry import shape,mapping
from shapely.ops import transform,unary_union
from pyproj import Transformer
import argparse
parser=argparse.ArgumentParser(description='Prepare the EDA map and reviewed-business counts from existing extracts.')
parser.add_argument('--work-dir',type=Path,required=True)
parser.add_argument('--states-file',type=Path,required=True)
args=parser.parse_args()
R=Path(__file__).resolve().parent
W=args.work_dir
D=R/'study_data';reg=json.loads((D/'project_registry.json').read_text())
summary=[];annual=[];sources=[]
for row in reg:
 name=row['project'];folder=W/row['folder']
 if name=='Sun Link':folder=W/'Sun Link Full Corridor'
 bf=folder/('business_inventory_8km.csv' if name=='Sun Link' else 'business_features.csv')
 rf=folder/'scored_reviews.csv.gz'
 b=pd.read_csv(bf,usecols=['business_id','distance_m']).set_index('business_id')
 counts=pd.read_csv(rf,usecols=['business_id','year']).groupby(['business_id','year']).size().unstack(fill_value=0)
 counts=counts.reindex(b.index,fill_value=0)
 pre=counts.reindex(columns=row['pre'],fill_value=0).sum(axis=1);post=counts.reindex(columns=row['post'],fill_value=0).sum(axis=1)
 for area,mask in [('Near',b.distance_m.le(500)),('Farther',b.distance_m.gt(1500)&b.distance_m.le(8000))]:
  a=pre[mask];z=post[mask]
  summary.append(dict(project=name,area=area,listings=int(mask.sum()),baseline_active=int((a>0).sum()),post_active=int((z>0).sum()),active_both=int(((a>0)&(z>0)).sum()),post_only=int(((a==0)&(z>0)).sum()),baseline_only=int(((a>0)&(z==0)).sum()),neither=int(((a==0)&(z==0)).sum()),baseline_years='/'.join(map(str,row['pre'])),post_years='/'.join(map(str,row['post']))))
  for year in counts.columns:annual.append(dict(project=name,area=area,year=int(year),reviewed_businesses=int((counts.loc[mask,year]>0).sum())))
 sources.extend([str(bf),str(rf)])
s=pd.DataFrame(summary);s['growth_pct']=100*(s.post_active/s.baseline_active-1)
for name in s.project.unique():
 rows=s[s.project.eq(name)].set_index('area');r=100*((rows.loc['Near','post_active']/rows.loc['Near','baseline_active'])/(rows.loc['Farther','post_active']/rows.loc['Farther','baseline_active'])-1)
 s.loc[s.project.eq(name),'relative_growth_pct']=r
assert (s.active_both+s.post_only==s.post_active).all()
assert (s.active_both+s.baseline_only==s.baseline_active).all()
assert (s.active_both+s.baseline_only+s.post_only+s.neither==s.listings).all()
s.to_csv(D/'business_growth.csv',index=False);pd.DataFrame(annual).to_csv(D/'business_growth_annual.csv',index=False)
print(s.to_string(index=False))
# Prepare cartographic coordinates so the submitted notebook needs no GIS libraries.
t=Transformer.from_crs(4326,5070,always_xy=True).transform
states=[]
for f in json.loads(args.states_file.read_text())['features']:
 if f['properties']['name'] in ['Alaska','Hawaii']:continue
 geom=transform(t,shape(f['geometry']))
 states.append({'name':f['properties']['name'],'geometry':mapping(geom)})
files=['Lafitte.geojson','Sun_Link.geojson','Dilworth_Park.geojson','Water_Works_Park.geojson','Riverfront_Ascend.geojson'];projects=[]
for row,filename in zip(reg,files):
 j=json.loads((D/filename).read_text());features=j.get('features',[j]);g=unary_union([shape(f['geometry']) for f in features])
 center=g.centroid;utm=row.get('epsg',32612 if row['project']=='Sun Link' else 32615)
 project=transform(Transformer.from_crs(4326,utm,always_xy=True).transform,g)
 cx,cy=project.centroid.coords[0]
 local=lambda x,y,z=None:((x-cx)/1000,(y-cy)/1000)
 projects.append({'project':row['project'],'city':row['city'],'national_xy':list(t(center.x,center.y)),'footprint':mapping(transform(local,project)),'near_buffer':mapping(transform(local,project.buffer(500))),'epsg':utm})
mp={'states':states,'projects':projects,'national_crs':'EPSG:5070','local_units':'km','buffer_m':500,'basemap_source':'https://www.naturalearthdata.com/downloads/110m-cultural-vectors/110m-admin-1-states-provinces/','basemap_download':'https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_1_states_provinces.geojson'}
(D/'project_map.json').write_text(json.dumps(mp,separators=(',',':'))+'\n')
manifest=json.loads((D/'provenance.json').read_text())
for f in ['business_growth.csv','business_growth_annual.csv','project_map.json']:manifest['files'][f]=hashlib.sha256((D/f).read_bytes()).hexdigest()
manifest['map_and_business_growth']={'prepared':'2026-09-12','script':'prepare_map_and_business_growth.py','business_sources':sources,'meaning':'Active means at least one Yelp review in the specified two-year period, not verified operation. Sun Link uses inclusive full-corridor inventory.','map_source':mp['basemap_download'],'map_projection':'National EPSG:5070; project-specific UTM for 500 m buffers.'}
(D/'provenance.json').write_text(json.dumps(manifest,indent=2)+'\n')
