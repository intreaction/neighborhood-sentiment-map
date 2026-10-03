"""Retrospective point profiles: period, distance, coverage and public schema."""
import io
import json
import math
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import build_place_data as build
from place_data import EARTH_RADIUS_M,haversine_m,profile_records,profile_at,padded_bounds,inside_bounds


class PlaceDataTests(unittest.TestCase):
    def test_haversine_and_baseline_inventory_are_separate(self):
        lat499=math.degrees(499/EARTH_RADIUS_M);lat501=math.degrees(501/EARTH_RADIUS_M)
        result=profile_records([[0,0,0],[0,lat499,10],[0,lat501,99]],0,0)
        self.assertEqual(result['inventory_businesses'],2)
        self.assertEqual(result['baseline_reviewed_businesses'],1)
        self.assertEqual(result['baseline_reviews'],10)
        self.assertEqual(result['reviews_per_business'],10)
        self.assertAlmostEqual(haversine_m(0,0,0,lat499),499,places=6)

    def test_no_coverage_is_not_zero(self):
        payload={'cities':[{'id':'test','bounds':[0,0,1,1],'businesses':[[.5,.5,0]]}]}
        outside=profile_at(payload,2,2)
        self.assertEqual(outside['status'],'outside_coverage')
        self.assertIsNone(outside['baseline_reviews'])
        self.assertEqual(profile_at(payload,.1,.1)['status'],'no_inventory_coverage')
        self.assertEqual(profile_at(payload,.5,.5)['status'],'no_baseline_reviews')
        self.assertIsNone(profile_at(payload,.5,.5)['reviews_per_business'])
        with self.assertRaises(ValueError):profile_at(payload,float('nan'),0)
        with self.assertRaises(ValueError):profile_at(payload,.5,.5,1000)

    def test_full_archive_counting_uses_fixed_two_year_window(self):
        rows=[{'business_id':'b1','date':'2017-12-31'},{'business_id':'b1','date':'2018-01-01'},
              {'business_id':'b1','date':'2019-12-31'},{'business_id':'b1','date':'2020-01-01'},
              {'business_id':'outside-project-cache','date':'2018-03-04'}]
        data='\n'.join(json.dumps(r) for r in rows).encode()
        with tempfile.TemporaryDirectory() as d:
            archive=Path(d)/'reviews.tar';cache=Path(d)/'counts.json.gz'
            with tarfile.open(archive,'w') as tf:
                info=tarfile.TarInfo('nested/yelp_academic_dataset_review.json');info.size=len(data);tf.addfile(info,io.BytesIO(data))
            with patch.object(build,'ARCHIVE',archive),patch.object(build,'CACHE',cache):
                result=build.count_reviews()
                reused=build.count_reviews()
        self.assertEqual(result['source_reviews_scanned'],5)
        self.assertEqual(result['review_counts'],{'b1':2,'outside-project-cache':1})
        self.assertEqual(result['baseline_reviews_by_year'],{'2018':2,'2019':1})
        self.assertEqual(result,reused)

    def test_buffer_keeps_businesses_beyond_city_edge_without_publishing_ids(self):
        bounds=[0,0,1,1]
        record=(1.003,.5)
        self.assertTrue(inside_bounds(*record,padded_bounds(bounds)))
        payload,_=build.build_payload({'private-business-id':record},{},
            {'review_counts':{'private-business-id':8},'source_reviews_scanned':8,'baseline_reviews_all_source_geographies':8,'baseline_reviews_by_year':{'2018':4,'2019':4}},
            {'Philadelphia':bounds},[])
        result=profile_at(payload,1,.5)
        self.assertEqual(result['baseline_reviews'],8)
        self.assertEqual(result['baseline_reviewed_businesses'],1)
        self.assertNotIn('private-business-id',json.dumps(payload))
        self.assertEqual(payload['cities'][0]['businesses'],[[1.003,.5,8]])
        self.assertFalse(payload['coverage']['raw_review_text_published'])

    def test_invalid_business_locations_are_audited(self):
        records=[{'business_id':'good','longitude':-75,'latitude':40},
                 {'business_id':'missing','longitude':None,'latitude':40},
                 {'business_id':'bad','longitude':200,'latitude':40}]
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'business.json';path.write_text('\n'.join(json.dumps(r) for r in records))
            locations,audit=build.read_businesses(path)
        self.assertEqual(locations,{'good':(-75,40)})
        self.assertEqual(audit['missing_or_invalid_coordinates'],2)

if __name__=='__main__':unittest.main()
