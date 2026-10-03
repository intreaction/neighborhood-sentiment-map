"""Checks for the new project evidence data contract and classification limits."""
import json
import gzip
from unittest.mock import patch
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from project_registry import load_registry, build_cohorts
from project_text import analyze_text
from build_project_evidence import accumulator, add, summarize, primary_outcome, period_for_year, aggregate


class ProjectEvidenceTests(unittest.TestCase):
    def test_registry_periods_and_source_corrections(self):
        projects=load_registry();self.assertEqual(len(projects),11)
        gateway=next(p for p in projects if p['project']=='Gateway Arch Park')
        self.assertEqual(gateway['opening'],'2018-07-03')
        self.assertEqual(gateway['post_years'],[2019,2020])
        for p in projects:
            self.assertEqual(period_for_year(p,2026),None)
            self.assertTrue(set(p['pre_years']).isdisjoint(p['post_years']))

    def test_spatial_membership_ignores_city_spelling(self):
        project={'id':'test','state':'PA','geometry':{'kind':'center_proxy','latitude':40,'longitude':-75}}
        businesses=[{'business_id':'near','state':'NJ','city':'Different Municipality','latitude':40,'longitude':-75},
          {'business_id':'far','state':'PA','city':'', 'latitude':40.02,'longitude':-75},
          {'business_id':'excluded','state':'PA','city':'Same City','latitude':41,'longitude':-75}]
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'business.json';path.write_text('\n'.join(json.dumps(b) for b in businesses))
            assignment,inventory,_=build_cohorts([project],path)
        self.assertEqual(assignment['near'],[('test','near')]);self.assertEqual(assignment['far'],[('test','far')]);self.assertNotIn('excluded',assignment)

    def test_business_target_is_not_public_cleanliness(self):
        result=analyze_text('The bathroom was dirty and filthy.')
        self.assertFalse(result['place']);self.assertFalse(result['public_realm_complaint'])
        self.assertEqual(result['evidence'][0]['target'],'business')

    def test_mixed_business_and_place_sentiment(self):
        result=analyze_text('The food was excellent, but walking here felt unsafe.')
        self.assertTrue(result['place']);self.assertTrue(result['access_friction']);self.assertTrue(result['public_realm_complaint'])
        food=next(e for e in result['evidence'] if e['topic']=='food_service_value')
        safety=next(e for e in result['evidence'] if e['topic']=='safety')
        self.assertEqual(food['polarity'],'positive');self.assertEqual(safety['polarity'],'negative')

    def test_negation_and_unclear_target(self):
        self.assertFalse(analyze_text('The street was not unsafe.')['public_realm_complaint'])
        self.assertFalse(analyze_text('Parking was difficult.')['access_friction'])
        self.assertTrue(analyze_text('Street parking was difficult.')['access_friction'])
        self.assertFalse(analyze_text('Their parking lot was dirty.')['public_realm_complaint'])

    def test_aggregation_uses_all_review_denominator_and_unique_businesses(self):
        cell=accumulator()
        for text in ['Street parking was difficult.','Excellent food.']:
            add(cell,{'business_id':'b1','stars':3,'date':'2011-01-01','text':text,'analysis':analyze_text(text)})
        result=summarize(cell)
        self.assertEqual(result['n_reviews'],2);self.assertEqual(result['n_businesses'],1)
        self.assertEqual(result['access_friction_share'],.5)
        self.assertEqual(result['topics']['parking']['negative_share'],.5)
        self.assertIsNone(summarize(accumulator())['access_friction_share'])

    def test_business_balance_and_missing_text_are_explicit(self):
        cell=accumulator()
        for bid,text in [('busy','Street parking was difficult.')]*3+[('quiet','Good food.'),('missing','')]:
            add(cell,{'business_id':bid,'stars':3,'date':'2011-01-01','text':text,'analysis':analyze_text(text)})
        summary=summarize(cell)
        self.assertEqual(summary['n_reviews'],5)
        self.assertEqual(summary['n_text_reviews'],4)
        self.assertEqual(summary['n_missing_text'],1)
        self.assertEqual(summary['access_friction_share'],.75)
        self.assertEqual(summary['business_balanced']['access_friction_share'],.5)
        self.assertEqual(summary['business_balanced']['n_businesses'],2)
        self.assertEqual(summary['business_balanced']['largest_business_review_share'],.75)

    def test_shared_review_join_and_baseline_text_excludes_post(self):
        projects=[{'id':pid,'project':pid,'city':'City','cost_millions':10,'post_years':[2016]} for pid in ['a','b']]
        records=[{'review_id':'r1','business_id':'business','date':'2011-01-01','stars':4,'text':'Good food.',
                  'memberships':[['a','near','pre'],['b','near','pre']],'analysis':analyze_text('Good food.')},
                 {'review_id':'r2','business_id':'business','date':'2016-01-01','stars':1,'text':'The sidewalk was dirty.',
                  'memberships':[['a','near','post']],'analysis':analyze_text('The sidewalk was dirty.')}]
        inventories={pid:{'near':['business'],'far':[]} for pid in ['a','b']}
        with tempfile.TemporaryDirectory() as d:
            local=Path(d);cache=local/'reviews.jsonl.gz'
            with gzip.open(cache,'wt') as f:
                for r in records:f.write(json.dumps(r)+'\n')
            (local/'cache_manifest.json').write_text('{}')
            with patch('build_project_evidence.LOCAL',local):result=aggregate(cache,projects,inventories)
        self.assertEqual(result['coverage']['unique_reviews_scored'],2)
        self.assertEqual(result['coverage']['review_project_period_memberships'],3)
        self.assertEqual(result['coverage']['reviews_shared_across_projects'],1)
        a=result['projects'][0]
        self.assertEqual(a['features']['place_discussion_share'],0)
        self.assertEqual(a['periods']['near']['post']['place_discussion_share'],1)
        self.assertEqual(a['coverage']['near_listing_overlap'],{'b':1})

    def test_outcome_support_and_growth_adjustment(self):
        near={'pre':{'n_reviews':100,'n_businesses':20},'post':{'n_reviews':300}}
        far={'pre':{'n_reviews':1000},'post':{'n_reviews':2000}}
        r=primary_outcome(near,far,10)
        self.assertTrue(r['eligible']);self.assertEqual(r['ce_reviews_per_million'],10)
        near['pre']['n_businesses']=19
        r=primary_outcome(near,far,10)
        self.assertFalse(r['eligible']);self.assertIsNone(r['ce_reviews_per_million'])

if __name__=='__main__':unittest.main()
