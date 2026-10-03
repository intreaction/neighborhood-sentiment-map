import json
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from build_place_areas import summarize,compare,geometry_area_km2

class AreaAnalysisTests(unittest.TestCase):
    def test_review_weighting_and_period_selection(self):
        rows=[{'quarter':'2012Q1','n_reviews':'100','mean_compound':'0.2'},
              {'quarter':'2013Q1','n_reviews':'300','mean_compound':'0.8'},
              {'quarter':'2019Q1','n_reviews':'900','mean_compound':'-0.5'}]
        result=summarize(rows,(2012,2013,2014))
        self.assertEqual(result['reviews'],400)
        self.assertAlmostEqual(result['sentiment'],.65)

    def test_relative_sentiment_excludes_the_selected_zip(self):
        a={'reviews':100,'sentiment_sum':50,'sentiment':.5}
        b={'reviews':200,'sentiment_sum':80,'sentiment':.4}
        m0={'reviews':300,'sentiment_sum':190}
        m1={'reviews':600,'sentiment_sum':280}
        result=compare(a,b,m0,m1)
        self.assertEqual(result['growth_pct'],100)
        self.assertAlmostEqual(result['sentiment_change'],-.1)
        self.assertAlmostEqual(result['relative_sentiment_change'],.1)
        self.assertIsNone(compare({**a,'reviews':99},b,m0,m1)['growth_pct'])

    def test_polygon_holes_reduce_density_denominator(self):
        outer=[[0,0],[1,0],[1,1],[0,1],[0,0]]
        hole=[[.2,.2],[.8,.2],[.8,.8],[.2,.8],[.2,.2]]
        whole=geometry_area_km2({'type':'Polygon','coordinates':[outer]})
        cut=geometry_area_km2({'type':'Polygon','coordinates':[outer,hole]})
        self.assertTrue(12300<whole<12400)
        self.assertAlmostEqual(cut/whole,.64,places=4)

    def test_published_artifact_preserves_nulls_denominators_and_vintages(self):
        data=json.loads((ROOT/'web/place-areas.json').read_text())
        self.assertEqual(sum(len(c['areas']) for c in data['cities']),196)
        limited=0
        for city in data['cities']:
            for area in city['areas']:
                self.assertLessEqual(area['access_mentions'],area['late']['reviews'])
                if area['acs_year'] is not None:
                    self.assertEqual(area['acs_year'],2011 if city['id'] in ['Philadelphia','Tucson'] else 2012)
                if area['late']['reviews']>=100:
                    self.assertAlmostEqual(area['access_share_pct'],100*area['access_mentions']/area['late']['reviews'])
                else:
                    limited+=1
                    self.assertIsNone(area['access_share_pct'])
                    self.assertIsNone(area['annual_review_density'])
                if min(area['early']['reviews'],area['late']['reviews'])<100:
                    self.assertIsNone(area['growth_pct'])
                    self.assertIsNone(area['relative_sentiment_change'])
        self.assertGreater(limited,0)

if __name__=='__main__':unittest.main()
