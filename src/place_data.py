"""Geographic profile helpers for retrospective 500 m location scenarios.

The inventory comes from the January 2022 Yelp archive. A zero means no matching
archive observation, never proof that no businesses or visits existed.
"""
import math
EARTH_RADIUS_M=6371008.8
BASELINE_YEARS=(2018,2019)
RADIUS_M=500
BUFFER_M=1000


def haversine_m(lon1,lat1,lon2,lat2):
    lon1,lat1,lon2,lat2=map(math.radians,(lon1,lat1,lon2,lat2))
    a=math.sin((lat2-lat1)/2)**2+math.cos(lat1)*math.cos(lat2)*math.sin((lon2-lon1)/2)**2
    return 2*EARTH_RADIUS_M*math.asin(min(1.,math.sqrt(max(0.,a))))


def inside_bounds(lon,lat,bounds):
    west,south,east,north=bounds
    return west<=lon<=east and south<=lat<=north


def padded_bounds(bounds,buffer_m=BUFFER_M):
    west,south,east,north=bounds
    lat_delta=math.degrees(buffer_m/EARTH_RADIUS_M)
    max_abs_lat=max(abs(south),abs(north))+lat_delta
    lon_delta=math.degrees(buffer_m/(EARTH_RADIUS_M*math.cos(math.radians(max_abs_lat))))
    return [west-lon_delta,south-lat_delta,east+lon_delta,north+lat_delta]


def profile_records(records,lon,lat,radius_m=RADIUS_M):
    """Count archive listings and baseline-reviewed listings separately."""
    inventory=reviewed=reviews=0
    for blon,blat,n in records:
        if haversine_m(lon,lat,blon,blat)<=radius_m:
            inventory+=1
            if n>0:reviewed+=1;reviews+=n
    return {'inventory_businesses':inventory,'baseline_reviewed_businesses':reviewed,'baseline_reviews':reviews,
            'reviews_per_business':reviews/reviewed if reviewed else None,'radius_m':radius_m,
            'status':'no_inventory_coverage' if not inventory else 'no_baseline_reviews' if not reviewed else 'observed_historical_profile'}


def profile_at(payload,lon,lat,radius_m=RADIUS_M):
    """Outside supported analysis bounds is unavailable, not zero activity."""
    if not all(math.isfinite(x) for x in (lon,lat)) or not -180<=lon<=180 or not -90<=lat<=90:
        raise ValueError('Valid longitude and latitude required')
    if radius_m!=RADIUS_M:raise ValueError('Published location profiles use a fixed 500 m radius')
    city=next((c for c in payload['cities'] if inside_bounds(lon,lat,c['bounds'])),None)
    if city is None:
        return {'status':'outside_coverage','city_id':None,'inventory_businesses':None,'baseline_reviewed_businesses':None,'baseline_reviews':None,'reviews_per_business':None,'radius_m':radius_m}
    return dict(profile_records(city['businesses'],lon,lat,radius_m),city_id=city['id'],baseline_years=list(BASELINE_YEARS))
