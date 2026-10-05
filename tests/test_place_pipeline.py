"""Regression checks for the notebook's portable, explicit data contract."""
import copy
import json
import shutil
import sys
import tempfile
import unittest
from numeric_assertions import assert_numeric_tree
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from place_pipeline import load_inputs, derive_areas, build_payloads, validate_payloads, export_payloads


class NotebookPipelineTests(unittest.TestCase):
    def test_build_without_raw_data_intermediates_or_existing_web_outputs(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            paths = ['data/derived/place_inputs', 'data/derived/project_evidence.json',
                     'data/derived/project_model.json', 'data/derived/advanced_text.json',
                     'src/place_pipeline.py', 'src/build_place_areas.py',
                     'output/jupyter-notebook/Project_Research_Walkthrough.ipynb']
            for relative in paths:
                source, target = ROOT / relative, root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                if source.is_dir():
                    shutil.copytree(source, target)
                else:
                    shutil.copyfile(source, target)
            self.assertFalse((root / 'web').exists())
            self.assertFalse((root / 'data/interim').exists())
            inputs = load_inputs(root)
            payloads = build_payloads(inputs, derive_areas(inputs))
            manifest = export_payloads(payloads, inputs, root / 'web')
            self.assertEqual(manifest['summary']['ZIPs'], 196)
            self.assertEqual(manifest['summary']['historical_projects'], 11)
            self.assertEqual(len(manifest['outputs_sha256']), 6)
            # No substantive values change when replaying prepared inputs.
            for name, generated in payloads.items():
                assert_numeric_tree(self, generated, json.loads((ROOT / 'web' / name).read_text()), name)
            self.assertEqual(manifest, export_payloads(payloads, inputs, root / 'web'))

    def test_snapshot_tampering_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            destination = root / 'data/derived/place_inputs'
            shutil.copytree(ROOT / 'data/derived/place_inputs', destination)
            (destination / 'income.csv').write_text('changed')
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                load_inputs(root)

    def test_invalid_payloads_do_not_publish_partial_data(self):
        inputs = load_inputs(ROOT)
        payloads = build_payloads(inputs, derive_areas(inputs))
        damaged = copy.deepcopy(payloads)
        damaged['place-data.json']['cities'][0]['baseline_reviews'] += 1
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'web'
            with self.assertRaisesRegex(ValueError, 'reconcile'):
                export_payloads(damaged, inputs, target)
            self.assertFalse(target.exists())


if __name__ == '__main__':
    unittest.main()
