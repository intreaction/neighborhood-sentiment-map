"""Retrieve the completed Rail Park footprint, excluding the mapped future phase.

The Center City District account publishes both the existing park (OBJECTID 11)
and a separate Phase 2 polygon (13). Preserve the query and source metadata with
the geometry. This is a current mapped footprint, not a certified 2018 survey.
"""
import hashlib
import json
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
SERVICE = 'https://services1.arcgis.com/TNz8x5gA9YhXLeFQ/arcgis/rest/services/Rail_Park/FeatureServer/0'
ITEM = 'https://www.arcgis.com/sharing/rest/content/items/ca95766207934d409c481634b26fcd79'


def main():
    params = {'f': 'geojson', 'where': 'OBJECTID = 11', 'outFields': '*', 'outSR': 4326}
    response = requests.get(SERVICE + '/query', params=params, timeout=30)
    response.raise_for_status()
    payload = response.json()
    assert len(payload['features']) == 1, 'Expected only the existing Rail Park feature'
    feature = payload['features'][0]
    assert feature['properties']['Name'] == 'Rail Park'
    assert feature['geometry']['type'] == 'Polygon'
    points = feature['geometry']['coordinates'][0]
    assert all(-75.163 < x < -75.155 and 39.958 < y < 39.962 for x, y in points)
    metadata_response = requests.get(ITEM, params={'f': 'json'}, timeout=30)
    metadata_response.raise_for_status()
    metadata = metadata_response.json()
    out = ROOT / 'data/geometry'
    out.mkdir(parents=True, exist_ok=True)
    geometry = out / 'rail-park-phase-one.geojson'
    geometry.write_text(json.dumps(payload, separators=(',', ':')) + '\n')
    audit = {
        'project': 'The Rail Park', 'source_url': SERVICE,
        'item_url': ITEM, 'item_owner': metadata['owner'],
        'retrieved_date': '2026-09-25', 'query': params,
        'selected_object_ids': [11], 'excluded_future_phase_object_ids': [13],
        'sha256': hashlib.sha256(geometry.read_bytes()).hexdigest(),
        'quality': 'Current operator-account mapped polygon; historical fidelity not independently surveyed',
        'source_description': 'Rail Park layer published by jbrain_ccdphila; future Phase 2 is a separate feature.',
    }
    (out / 'rail-park-phase-one.provenance.json').write_text(json.dumps(audit, indent=2) + '\n')
    print(f'Wrote {geometry} ({len(points)} vertices; future phase excluded)')


if __name__ == '__main__':
    main()
