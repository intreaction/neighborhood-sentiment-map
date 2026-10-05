"""Contract checks for the portable evidence and proposal experience."""
import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class EvidenceSiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = json.loads((ROOT / 'data/derived/project_evidence.json').read_text())
        cls.model = json.loads((ROOT / 'data/derived/project_model.json').read_text())

    def test_all_project_records_reach_portable_pages(self):
        self.assertEqual(len(self.evidence['projects']), 11)
        ids = [p['id'] for p in self.evidence['projects']]
        self.assertEqual(len(set(ids)), 11)
        for name in ('projects', 'model'):
            html = (ROOT / 'web' / f'{name}.html').read_text()
            self.assertNotIn('__DATA__', html)
            self.assertNotIn('__MATH__', html)
            self.assertNotRegex(html, r'<(?:script|link)[^>]+(?:src|href)=["\']https?://')
            self.assertIn('href="atlas.html"', html)
            self.assertLess(len(html.encode()), 2_000_000)
            script = re.search(r'<script>(.*?)</script>', html, re.S).group(1)
            with tempfile.TemporaryDirectory() as temp:
                path = Path(temp) / 'site.js'
                path.write_text(script)
                checked = subprocess.run(['node', '--check', str(path)], capture_output=True, text=True)
                self.assertEqual(checked.returncode, 0, checked.stderr)
        self.assertIn('url=place.html', (ROOT / 'web/index.html').read_text())

    def test_advanced_text_evidence_is_embedded_for_every_project(self):
        advanced = json.loads((ROOT / 'data/derived/advanced_text.json').read_text())
        self.assertEqual(len(advanced['topics']), 5)
        self.assertEqual({p['id'] for p in advanced['projects']}, {p['id'] for p in self.evidence['projects']})
        for project in advanced['projects']:
            for period in ('pre', 'post'):
                values = project[period]['topic_distribution']
                self.assertEqual(len(values), 5)
                self.assertTrue(all(0 <= value <= 1 for value in values))
                self.assertAlmostEqual(sum(values), 1, places=6)
        html = (ROOT / 'web/projects.html').read_text()
        self.assertIn('const ADVANCED=', html)
        self.assertIn('Learned patterns in review language.', html)
        self.assertIn('TF-IDF + NMF', html)

    def test_profile_import_validation_and_fraction_units(self):
        source = (ROOT / 'src/evidence.js').read_text()
        start = source.index('function validateProfile(value)')
        end = source.index('function initializeModel()', start)
        validation = source[start:end]
        script = """const assert=require('node:assert/strict');
const textFields=[['place_share'],['access_negative_share'],['publicrealm_negative_share']];
const inputFields=['cost_millions','baseline_reviewed','pre_reviews_per_business',...textFields.map(x=>x[0]),'early_relative_trend'];
""" + validation + """
const valid={schema_version:'pim-baseline-profile-v1',name:'Example',location:'Measured 500 m footprint',source:'Documented extraction',extracted_at:'2026-09-26',baseline_years:[2018,2019],inputs:{cost_millions:55,baseline_reviewed:500,pre_reviews_per_business:10,place_share:0.12,access_negative_share:0.03,publicrealm_negative_share:null}};
assert.equal(validateProfile(valid),valid);
assert.throws(()=>validateProfile({...valid,inputs:{...valid.inputs,place_share:12}}),/fraction/);
assert.throws(()=>validateProfile({...valid,inputs:{...valid.inputs,baseline_reviewed:2.5}}),/whole/);
assert.throws(()=>validateProfile({...valid,inputs:{...valid.inputs,cost_millions:0}}),/positive/);
assert.throws(()=>validateProfile({...valid,inputs:{...valid.inputs,unexpected:5}}),/Unknown/);
assert.throws(()=>validateProfile({...valid,baseline_years:[2018,2020]}),/consecutive/);
assert.throws(()=>validateProfile({...valid,extracted_at:'2026-02-30'}),/valid/);
assert.throws(()=>validateProfile({...valid,source:''}),/source/);
assert.throws(()=>validateProfile([]),/object/);
"""
        check = subprocess.run(['node', '-e', script], capture_output=True, text=True)
        self.assertEqual(check.returncode, 0, check.stderr)

    def test_preset_percentage_roundtrips_and_low_support(self):
        source = (ROOT / 'src/evidence.js').read_text()
        preset_fn = source[source.index('function profileForProject('):source.index('function loadProfile(')]
        validation_fn = source[source.index('function validateProfile('):source.index('function initializeModel(')]
        script = "const assert=require('node:assert/strict');const fs=require('node:fs');" + (
            "const {projectEstimate}=require('./src/project_model_math.js');"
            "const MODEL=JSON.parse(fs.readFileSync('data/derived/project_model.json'));"
            "const EVIDENCE=JSON.parse(fs.readFileSync('data/derived/project_evidence.json'));"
        ) + "const geometry=p=>p.geometry_quality;const inputFields=Object.keys(MODEL.feature_schema);const textFields=[[\"place_share\"],[\"access_negative_share\"],[\"publicrealm_negative_share\"]];" + preset_fn + validation_fn + """
for(const project of EVIDENCE.projects){
  const profile=profileForProject(project);
  profile.extracted_at='2026-09-26';
  assert.equal(validateProfile(profile),profile);
  if(profile.inputs.topic_1!=null)assert.throws(()=>validateProfile({...profile,inputs:{...profile.inputs,topic_basis_version:'wrong-basis'}}),/matching/);
  for(const key of ['place_share','access_negative_share','publicrealm_negative_share']){
    if(profile.inputs[key]!=null)profile.inputs[key]=Number(String(profile.inputs[key]*100))/100;
  }
  const result=projectEstimate(MODEL,profile.inputs);
  assert.equal(Boolean(result.estimate),project.primary.eligible,project.project);
  if(project.primary.eligible){
    for(const candidate of Object.keys(MODEL.candidates)){
      const alternate=projectEstimate({...MODEL,selected_model:candidate},profile.inputs);
      assert.ok(alternate.estimate,project.project+' '+candidate+' '+JSON.stringify(alternate.errors));
    }
  }
}
"""
        result = subprocess.run(['node', '-e', script], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_project_preset_maps_to_supported_model_contract(self):
        by_name = {p['project']: p for p in self.evidence['projects']}
        fields = self.model['candidates'][self.model['selected_model']]['feature_names']
        for row in self.model['training_rows']:
            self.assertIn(row['project'], by_name)
            for field in fields:
                self.assertIsInstance(row['inputs'][field], (int, float))
            self.assertAlmostEqual(row['observed_ce'], by_name[row['project']]['primary']['ce_reviews_per_million'], places=6)


if __name__ == '__main__':
    unittest.main()
