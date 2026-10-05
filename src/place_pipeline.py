"""Testable data transformations used by the Place Lab research notebook.

Reading, deriving, validating and exporting are separate operations. The browser
loads the exported files; it never runs Python or reads notebook internals.
"""
import csv
import hashlib
import json
from pathlib import Path

from build_place_areas import compute_areas, compute_timeline


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_inputs(root):
    """Read checked-in aggregates and reject snapshots whose hashes changed."""
    root = Path(root)
    folder = root / 'data/derived/place_inputs'
    manifest = json.loads((folder / 'manifest.json').read_text())
    inputs = {'root': root, 'manifest': manifest}
    for name, expected in manifest['files_sha256'].items():
        path = folder / name
        if digest(path) != expected:
            raise ValueError(f'Input hash mismatch: {name}. Refresh snapshots explicitly after an upstream rebuild.')
        if path.suffix == '.csv':
            with path.open() as stream:
                inputs[name] = list(csv.DictReader(stream))
        else:
            inputs[name] = json.loads(path.read_text())
    for name in ('project_evidence', 'project_model', 'advanced_text'):
        inputs[name] = json.loads((root / f'data/derived/{name}.json').read_text())
    evidence_hash = digest(root / 'data/derived/project_evidence.json')
    if inputs['project_model']['provenance']['evidence_sha256'] != evidence_hash:
        raise ValueError('Model and project evidence are from different builds.')
    if inputs['advanced_text']['coverage']['source_evidence_sha256'] != evidence_hash:
        raise ValueError('Advanced text and project evidence are from different builds.')
    return inputs


def derive_areas(inputs):
    """Recompute ZIP measures from quarterly counts, scores, ACS and geometry."""
    return compute_areas(inputs['map_geometry.json'], inputs['metro_zips.json'],
                         inputs['sentiment_zip_quarter.csv'], inputs['access_quarters.json'],
                         inputs['yelp_zip_summary.csv'], inputs['income.csv'],
                         {f'data/derived/place_inputs/{name}': value
                          for name, value in inputs['manifest']['files_sha256'].items()})


def derive_history(evidence):
    """Select historical chart fields from the current project evidence."""
    fields = ('n_reviews', 'by_year', 'topics', 'place_discussion_share',
              'access_friction_share', 'public_realm_complaint_share', 'mean_sentiment')
    return {'version': evidence['version'], 'projects': [
        {'id': p['id'], 'project': p['project'], 'opening': p['opening'],
         'periods': {band: {period: {key: values[key] for key in fields}
                           for period, values in p['periods'][band].items()}
                     for band in ('near', 'far')}} for p in evidence['projects']]}


def derive_timeline(inputs):
    """Monthly ZIP and metro sums behind the map's time controls."""
    return compute_timeline(inputs['map_geometry.json'], inputs['metro_zips.json'],
                            inputs['review_zip_month.csv'], inputs['access_quarters.json'])


def build_payloads(inputs, areas):
    """Assemble the six data files consumed by place_app.js."""
    return {'place-timeline.json': derive_timeline(inputs),
            'place-data.json': inputs['baseline_profiles.json'],
            'place-map.json': inputs['map_geometry.json'],
            'place-areas.json': areas,
            'place-model.json': inputs['project_model'],
            'place-history.json': derive_history(inputs['project_evidence'])}


def validate_payloads(payloads):
    """Check cross-file geography, record totals and missing-data semantics."""
    profiles = payloads['place-data.json']
    geometry = payloads['place-map.json']
    areas = payloads['place-areas.json']
    city_sets = [{c['id'] for c in p['cities']} for p in (profiles, geometry, areas)]
    if not city_sets[0] == city_sets[1] == city_sets[2]:
        raise ValueError('City coverage differs between app data files.')
    for city in profiles['cities']:
        records = city['businesses']
        if len(records) != city['inventory_businesses'] or sum(r[2] for r in records) != city['baseline_reviews']:
            raise ValueError(f"Profile counts do not reconcile: {city['id']}")
    mapped = {c['id']: {f['properties']['zip'] for f in c['features']} for c in geometry['cities']}
    for city in areas['cities']:
        if {a['zip'] for a in city['areas']} != mapped[city['id']]:
            raise ValueError(f"ZIP coverage differs: {city['id']}")
        for area in city['areas']:
            if area['access_mentions'] > area['late']['reviews']:
                raise ValueError('Access counts exceed review counts.')
            if area['late']['reviews'] < areas['minimum_reviews_per_period']:
                if area['access_share_pct'] is not None or area['annual_review_density'] is not None:
                    raise ValueError('Insufficient observations must remain null.')
    # The timeline must reproduce the published three-year windows exactly.
    timeline = payloads.get('place-timeline.json')
    if timeline:
        for city in timeline['cities']:
            published = {a['zip']: a for a in next(c for c in areas['cities'] if c['id'] == city['id'])['areas']}
            for zip_code, cell in city['areas'].items():
                late = sum(sum(cell['n'][(year-2012)*12:(year-2012)*12+12]) for year in areas['late_years'])
                if late != published[zip_code]['late']['reviews']:
                    raise ValueError(f'Timeline does not reconcile with area totals: {zip_code}')
    # JSON encoding rejects NaN and infinity, which browsers cannot parse as JSON.
    for data in payloads.values():
        json.dumps(data, allow_nan=False)
    return {'cities': len(city_sets[0]), 'ZIPs': sum(len(c['areas']) for c in areas['cities']),
            'profile_records': sum(len(c['businesses']) for c in profiles['cities']),
            'historical_projects': len(payloads['place-history.json']['projects'])}


def write_json(path, value):
    """Replace a JSON file only after successful finite-value serialization."""
    path = Path(path)
    encoded = json.dumps(value, separators=(',', ':'), allow_nan=False)+'\n'
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(encoded)
    temporary.replace(path)


def export_payloads(payloads, inputs, destination):
    """Validate all files before publishing; record inputs, code and output hashes."""
    summary = validate_payloads(payloads)
    destination = Path(destination)
    for name, value in payloads.items():
        write_json(destination / name, value)
    root = inputs['root']
    source_paths = ['data/derived/place_inputs/manifest.json', 'data/derived/project_evidence.json',
                    'data/derived/project_model.json', 'data/derived/advanced_text.json',
                    'src/place_pipeline.py', 'src/build_place_areas.py',
                    'output/jupyter-notebook/Project_Research_Walkthrough.ipynb']
    # Hash notebook source cells, not execution outputs, to avoid self-reference.
    notebook = json.loads((root / source_paths[-1]).read_text())
    notebook_source_hash = hashlib.sha256(json.dumps([(c['cell_type'], c['source']) for c in notebook['cells']], sort_keys=True).encode()).hexdigest()
    manifest = {'version': 'place-notebook-export-v1', 'summary': summary,
                'workflow': source_paths[-1], 'notebook_source_sha256': notebook_source_hash,
                'sources_sha256': {p: digest(root / p) for p in source_paths[:-1]},
                'outputs_sha256': {name: digest(destination / name) for name in payloads}}
    write_json(destination / 'place-build-manifest.json', manifest)
    return manifest
