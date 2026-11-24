"""Check the archived HUC8 assignments using the frozen WBD geometry."""

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from shapely.geometry import Point, shape
from shapely.ops import unary_union


def sha256(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wbd-root', required=True, type=Path)
    parser.add_argument('--inputs', type=Path, default=Path(__file__).resolve().parents[1] / 'inputs')
    parser.add_argument('--output', type=Path, default=Path(__file__).with_name('assignment_verification.json'))
    args = parser.parse_args()

    county_path = args.inputs / 'counties_2025_semigeneral.geojson'
    assignment_path = args.inputs / 'huc8_block_assignments.csv'
    with assignment_path.open(encoding='utf-8-sig', newline='') as stream:
        archived = defaultdict(list)
        for row in csv.DictReader(stream):
            archived[row['event_id']].append(row)
    county_features = json.loads(county_path.read_text(encoding='utf-8'))['features']
    county_centroids = {
        str(feat['properties']['FIPS']).zfill(5): shape(feat['geometry']).centroid
        for feat in county_features
    }

    report = []
    for event_id, rows in archived.items():
        event_source = args.wbd_root / event_id / 'event_huc12.geojson'
        polys = defaultdict(list)
        for feature in json.loads(event_source.read_text(encoding='utf-8'))['features']:
            huc12 = str(feature['properties'].get('huc12', ''))
            if len(huc12) >= 8:
                polys[huc12[:8]].append(shape(feature['geometry']))
        dissolved = {huc8: unary_union(polygons) for huc8, polygons in polys.items()}
        blocks = set()
        for expected in rows:
            centroid = county_centroids[expected['county_fips']]
            candidates = sorted(huc8 for huc8, poly in dissolved.items() if poly.covers(centroid))
            if candidates:
                huc8, assignment = candidates[0], 'centroid_within_huc8'
            else:
                huc8 = min(dissolved, key=lambda key: centroid.distance(dissolved[key]))
                assignment = 'nearest_huc8_fallback'
            assert (expected['huc8'], expected['assignment_method']) == (huc8, assignment), expected
            blocks.add(huc8)
        report.append({'event_id': event_id, 'county_assignments_reproduced': len(rows),
                       'distinct_huc8': len(blocks), 'event_geometry_sha256': sha256(event_source)})
    result = {'county_input_sha256': sha256(county_path), 'archived_assignments_sha256': sha256(assignment_path),
              'total_county_assignments_reproduced': sum(row['county_assignments_reproduced'] for row in report),
              'events': report}
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(f"Reproduced {result['total_county_assignments_reproduced']} HUC8 assignments.")


if __name__ == '__main__':
    main()
