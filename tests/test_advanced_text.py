"""Advanced text tests: deterministic sampling and baseline-only learned basis."""
import gzip
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import build_advanced_text as advanced


class AdvancedTextTests(unittest.TestCase):
    def test_hash_sampling_deduplicates_shared_reviews_and_ignores_order(self):
        rows=[{'review_id':str(i),'business_id':'b'+str(i),'date':'2011-01-01','stars':4,'text':'Street parking and good coffee.',
               'memberships':[['a','near','pre'],['b','near','pre'],['c','far','post']]} for i in range(5)]
        with tempfile.TemporaryDirectory() as d:
            local=Path(d);corpus=local/'advanced.json.gz'
            (local/'cache_manifest.json').write_text('{"signature":"test"}')
            def write(data):
                with gzip.open(local/'reviews_scored.jsonl.gz','wt') as f:
                    for r in data:f.write(json.dumps(r)+'\n')
            write(rows)
            with patch.object(advanced,'LOCAL',local),patch.object(advanced,'CORPUS',corpus):
                first=advanced.build_corpus(2);corpus.unlink();write(rows[::-1]);second=advanced.build_corpus(2)
        self.assertEqual(first,second)
        self.assertEqual(len(first['records']),2)
        for r in first['records']:
            self.assertEqual(len(r['memberships']),2)
            self.assertIn(['c','far','post'],r['all_memberships'])

    def test_document_mixture_and_entropy_account_for_unmapped_reviews(self):
        records=[{'business_id':'b1','text':'not safe safe','memberships':[['a','near','pre']]},
                 {'business_id':'b2','text':'safe walking','memberships':[['a','near','pre']]},
                 {'business_id':'b3','text':'unknown','memberships':[['a','near','post']]}]
        weights=np.array([[2.,0,0,0,0],[0,2,0,0,0],[0,0,0,0,0]])
        result=advanced.aggregate_features(records,weights,['a'],'pre')['a']
        self.assertEqual(result['topic_distribution'],[.5,.5,0,0,0])
        self.assertAlmostEqual(result['topic_entropy'],np.log(2)/np.log(5))
        post=advanced.aggregate_features(records,weights,['a'],'post')['a']
        self.assertEqual(post['n_topic_mapped_reviews'],0)
        self.assertIsNone(post['topic_distribution'])
        self.assertIsNone(post['topic_entropy'])

    def test_lexical_negation_is_not_sentiment(self):
        result=advanced.lexical_features("No, I don't dislike this safe street.")
        self.assertEqual(result['negation_count'],2)
        self.assertGreater(result['word_count'],0)
        self.assertTrue(0<=result['lexical_diversity']<=1)

    def test_learned_vocabulary_fits_only_baseline_text_and_retains_bigrams(self):
        themes=['coffee espresso roast beans','pizza crust tomato cheese','parking sidewalk street walking','service staff waiter friendly','park garden public fountain']
        records=[]
        for t,text in enumerate(themes):
            for i in range(4):
                records.append({'review_id':f'{t}-{i}','business_id':f'{t}-{i}','text':text+' excellent experience visit','memberships':[['a','near','pre']]})
        for i in range(4):records.append({'review_id':'post'+str(i),'business_id':'post'+str(i),'text':'quasarzeppelin quasarzeppelin pizza cheese','memberships':[['a','near','post']]})
        captured={}
        original=advanced.fit_topic_basis
        def capture(texts):
            vectorizer,model=original(texts);captured['vocabulary']=vectorizer.vocabulary_;captured['n']=len(texts);return vectorizer,model
        evidence={'projects':[{'id':'a','project':'A'}]}
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'evidence.json';path.write_text(json.dumps(evidence))
            with patch.object(advanced,'fit_topic_basis',capture),patch.object(advanced,'EVIDENCE',path):
                artifact=advanced.build_artifact({'records':records,'metadata':{}},evidence)
        self.assertEqual(captured['n'],20)
        self.assertNotIn('quasarzeppelin',captured['vocabulary'])
        self.assertIn('pizza crust',captured['vocabulary'])
        self.assertEqual(len(artifact['topics']),5)
        self.assertEqual(artifact['projects'][0]['post']['n_reviews'],4)
        self.assertAlmostEqual(sum(artifact['projects'][0]['pre']['topic_distribution']),1)

if __name__=='__main__':unittest.main()
