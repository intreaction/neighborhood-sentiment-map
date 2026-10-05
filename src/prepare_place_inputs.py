"""Freeze aggregate inputs for the notebook; never publish raw review text or IDs.

Run after rebuilding the upstream analysis. This refresh is deliberately separate
from notebook execution so reruns do not silently change their own source data.
"""
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / 'data/derived/place_inputs'


def prepare(root=ROOT, destination=DESTINATION):
    destination.mkdir(parents=True, exist_ok=True)
    sources = {}
    def read(relative):
        path = root / relative
        sources[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
        return path
    copies = {
        'baseline_profiles.json': 'web/place-data.json',
        'map_geometry.json': 'web/place-map.json',
        'metro_zips.json': 'data/interim/metro_zips.json',
        'sentiment_zip_quarter.csv': 'data/interim/sentiment_zip_quarter.csv',
        'yelp_zip_summary.csv': 'data/interim/yelp_zip_summary.csv',
        'income.csv': 'data/derived/place_area_income.csv',
    }
    for name, relative in copies.items():
        (destination / name).write_bytes(read(relative).read_bytes())
    topics = json.loads(read('data/interim/review_topics.json').read_text())
    # Keep just denominators and access counts used by the page, not excerpts.
    access = {'method': topics['method'], 'panel': {
        zip_code: {quarter: {'stars': values['stars'],
                            'topics': {'access': values['topics'].get('access', [0])}}
                   for quarter, values in quarters.items()}
        for zip_code, quarters in topics['panel'].items()}}
    (destination / 'access_quarters.json').write_text(json.dumps(access, separators=(',', ':'))+'\n')
    # Monthly ZIP totals for the map timeline: counts and score sums only, no review IDs or text.
    months = defaultdict(lambda: [0, 0.0, 0, 0])
    with read('data/interim/reviews_5metro.csv').open() as stream:
        for row in csv.DictReader(stream):
            cell, compound = months[(row['zip5'], row['date'][:7])], float(row['compound'])
            cell[0] += 1; cell[1] += compound; cell[2] += int(row['stars']); cell[3] += compound <= -0.05
    with (destination / 'review_zip_month.csv').open('w', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['zip5', 'month', 'n_reviews', 'compound_sum', 'stars_sum', 'n_negative'])
        for (zip_code, month), (n, compound, stars, negative) in sorted(months.items()):
            writer.writerow([zip_code, month, n, f'{compound:.4f}', stars, negative])
    snapshot_files = [*copies, 'access_quarters.json', 'review_zip_month.csv']
    manifest = {
        'version': 'place-notebook-inputs-v1',
        'description': 'Prepared historical aggregates, not original raw data. Frozen from the existing course analysis.',
        'upstream_sources_sha256': sources,
        'files_sha256': {name: hashlib.sha256((destination / name).read_bytes()).hexdigest() for name in snapshot_files},
        'lineage': {
            'baseline_profiles.json': 'build_place_data.py: full Yelp January 2022 archive, business coordinates and 2018–2019 review counts; copied from its existing published output.',
            'map_geometry.json': 'build_place_data.py: existing simplified Census ZCTA polygons; copied from its existing published output.',
            'sentiment_zip_quarter.csv': 'build_sentiment_panel.py: Yelp review text scored with VADER, aggregated by ZIP and quarter.',
            'review_zip_month.csv': 'build_sentiment_panel.py per-review scores (reviews_5metro.csv), summed by ZIP and calendar month: review count, VADER compound sum, star sum and count at or below the -0.05 negative cutoff.',
            'access_quarters.json': 'build_review_topics.py: existing keyword-rule counts. Includes positive and negative mentions; not a complaint classifier.',
            'income.csv': 'Earlier course ACS extracts: 2007–2011 Philadelphia/Tucson, 2008–2012 other metros. Historical estimates, not current incomes.',
            'metro_zips.json': 'Existing atlas study ZIP membership; retained to compute comparison against the rest of each study metro.',
            'yelp_zip_summary.csv': 'build_zip_universe.py: business inventory from the January 2022 Yelp archive.'
        }
    }
    (destination / 'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    return manifest


if __name__ == '__main__':
    result = prepare()
    print(f"Prepared {len(result['files_sha256'])} aggregate inputs in {DESTINATION}")
