"""Package existing area analysis for Place Lab; no new review classification.

The checked-in income table is a subset of the course's ACS 2011/2012 extracts.
Review panels are the existing atlas outputs. Run after those analyses are built.
"""
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INTERIM = ROOT / 'data/interim'
EARLY = (2012, 2013, 2014)
LATE = (2019, 2020, 2021)
MIN_REVIEWS = 100


def read_csv(path):
    with path.open() as f:
        return list(csv.DictReader(f))


def geometry_area_km2(geometry):
    """Spherical polygon area, subtracting holes; includes water inside ZCTAs."""
    def ring_area(ring):
        return abs(sum(math.radians(b[0]-a[0]) * (2+math.sin(math.radians(a[1]))+math.sin(math.radians(b[1])))
                       for a, b in zip(ring, ring[1:]))) * 6371.0088**2 / 2
    polygons = [geometry['coordinates']] if geometry['type'] == 'Polygon' else geometry['coordinates']
    return sum(max(0, ring_area(poly[0])-sum(ring_area(hole) for hole in poly[1:])) for poly in polygons)


def summarize(rows, years):
    eligible = [r for r in rows if int(r['quarter'][:4]) in years]
    n = sum(int(r['n_reviews']) for r in eligible)
    score_sum = sum(int(r['n_reviews'])*float(r['mean_compound']) for r in eligible)
    return {'reviews': n, 'sentiment_sum': score_sum, 'sentiment': score_sum/n if n else None}


def compare(early, late, metro_early, metro_late, minimum=MIN_REVIEWS):
    if min(early['reviews'], late['reviews']) < minimum:
        return {'growth_pct': None, 'sentiment_change': None, 'relative_sentiment_change': None}
    result = {'growth_pct': 100*(late['reviews']/early['reviews']-1),
              'sentiment_change': late['sentiment']-early['sentiment'], 'relative_sentiment_change': None}
    n0, n1 = metro_early['reviews']-early['reviews'], metro_late['reviews']-late['reviews']
    if min(n0, n1) >= minimum:
        other_change = ((metro_late['sentiment_sum']-late['sentiment_sum'])/n1
                        -(metro_early['sentiment_sum']-early['sentiment_sum'])/n0)
        result['relative_sentiment_change'] = result['sentiment_change']-other_change
    return result


def compute_areas(map_data, metro_zips, sentiment_rows, topic_data, inventory_rows, income_rows, sources):
    """Derive area evidence from explicit inputs; no file reads or writes."""
    panel = defaultdict(list)
    for row in sentiment_rows:
        panel[row['zip5']].append(row)
    inventory = {r['zip']: int(r['businesses']) for r in inventory_rows}
    income = {r['zip5']: r for r in income_rows}
    cities = []
    for city in map_data['cities']:
        all_rows = [r for z in metro_zips[city['id']] for r in panel[z]]
        m0, m1 = summarize(all_rows, EARLY), summarize(all_rows, LATE)
        areas = []
        for feature in city['features']:
            z = feature['properties']['zip']
            early, late = summarize(panel[z], EARLY), summarize(panel[z], LATE)
            quarters = [v for q,v in topic_data['panel'].get(z, {}).items() if int(q[:4]) in LATE]
            topic_n = sum(sum(q['stars']) for q in quarters)
            access_n = sum(q['topics'].get('access', [0])[0] for q in quarters)
            # The two existing pipelines must describe the same reviews.
            if topic_n != late['reviews']:
                raise ValueError(f'{z}: topic denominator {topic_n} differs from review panel {late["reviews"]}')
            area = geometry_area_km2(feature['geometry'])
            eco = income.get(z, {})
            def numeric(key):
                raw = eco.get(key, '')
                return float(raw) if raw and math.isfinite(float(raw)) and float(raw) >= 0 else None
            areas.append({'zip': z, 'area_km2': area, 'business_inventory': inventory.get(z),
                          'early': early, 'late': late, **compare(early, late, m0, m1),
                          'annual_review_density': late['reviews']/3/area if late['reviews'] >= MIN_REVIEWS and area > 0 else None,
                          'access_mentions': access_n, 'access_share_pct': 100*access_n/topic_n if topic_n >= MIN_REVIEWS else None,
                          'median_income': numeric('median_household_income'), 'income_moe': numeric('median_household_income_moe'),
                          'poverty_pct': numeric('poverty_rate')*100 if numeric('poverty_rate') is not None else None,
                          'acs_year': int(eco['acs_end_year']) if eco else None})
        cities.append({'id': city['id'], 'areas': areas})
    output = {'version': 'place-area-analysis-v1', 'early_years': list(EARLY), 'late_years': list(LATE),
              'minimum_reviews_per_period': MIN_REVIEWS, 'cities': cities,
              'method': {'geography': 'Existing ZIP analysis joined to Census ZCTA display polygons. No block-level interpolation.',
                         'income': 'Existing baseline ACS five-year estimates: 2007–2011 for Philadelphia/Tucson, 2008–2012 for other metros. Nominal historical household income, not reviewer income.',
                         'growth': '100 × (2019–2021 reviews / 2012–2014 reviews − 1), equal three-year windows.',
                         'sentiment': 'Review-weighted VADER change minus the change in the rest of the same study metro (excluding the selected ZIP). Whole-review business sentiment.',
                         'activity': 'Mean annual 2019–2021 reviews divided by displayed ZCTA square kilometres, including water. Inventory is the separate January 2022 Yelp listing snapshot.',
                         'access': topic_data['method']+' Access/parking share includes praise and complaints; it is not an aspect-specific complaint rate.',
                         'coverage': 'Fewer than 100 reviews in a required period: limited data, not zero. 2019–2021 includes the pandemic. Review activity does not establish visits, business openings or project effects.'},
              'sources': sources}
    return output


def build():
    """CLI equivalent of the notebook's area transformation and export."""
    from place_pipeline import load_inputs, derive_areas, write_json
    inputs = load_inputs(ROOT)
    output = derive_areas(inputs)
    destination = ROOT / 'web/place-areas.json'
    write_json(destination, output)
    print('Wrote', destination)
    return output


if __name__ == '__main__':
    build()
