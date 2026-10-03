"""Freeze aggregate inputs for the notebook; never publish raw review text or IDs.

Run after rebuilding the upstream analysis. This refresh is deliberately separate
from notebook execution so reruns do not silently change their own source data.
"""
import hashlib
import json
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
    snapshot_files = [*copies, 'access_quarters.json']
    manifest = {
        'version': 'place-notebook-inputs-v1',
        'description': 'Prepared historical aggregates, not original raw data. Frozen from the existing course analysis.',
        'upstream_sources_sha256': sources,
        'files_sha256': {name: hashlib.sha256((destination / name).read_bytes()).hexdigest() for name in snapshot_files},
        'lineage': {
            'baseline_profiles.json': 'build_place_data.py: full Yelp January 2022 archive, business coordinates and 2018–2019 review counts; copied from its existing published output.',
            'map_geometry.json': 'build_place_data.py: existing simplified Census ZCTA polygons; copied from its existing published output.',
            'sentiment_zip_quarter.csv': 'build_sentiment_panel.py: Yelp review text scored with VADER, aggregated by ZIP and quarter.',
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
