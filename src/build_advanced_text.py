"""Advanced text evidence: TF-IDF unigrams/bigrams and five NMF topics.

The published topic basis is DESCRIPTIVE: it is fitted on unique sampled near/pre
reviews across projects, then used unchanged for pre/post comparisons. Predictive
validation must fit its own vocabulary and NMF inside every project/city fold.
Full texts and raw identities remain in the ignored local corpus cache.
"""
import argparse
import gzip
import hashlib
import heapq
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
from sklearn.decomposition import NMF
from sklearn.feature_extraction.text import TfidfVectorizer
from threadpoolctl import threadpool_limits
from project_registry import ROOT
LOCAL=ROOT/'data/interim/project_evidence'
CORPUS=LOCAL/'advanced_corpus.json.gz'
OUT=ROOT/'data/derived/advanced_text.json'
EVIDENCE=ROOT/'data/derived/project_evidence.json'
VERSION='tfidf-bigram-nmf5-v1'
N_TOPICS=5
WORD=re.compile(r"\b[a-zA-Z]+(?:'[a-zA-Z]+)?\b")
NEGATIONS={'no','not','never','neither','nor','nothing','nowhere','without',"don't","doesn't","didn't","isn't","wasn't","weren't","can't","couldn't","won't","wouldn't","shouldn't"}


def sample_rank(review_id):
    return int.from_bytes(hashlib.sha256(review_id.encode()).digest()[:8],'big')


def build_corpus(max_per_project=1200):
    if max_per_project < 1:raise ValueError('Sample cap must be positive')
    manifest=json.loads((LOCAL/'cache_manifest.json').read_text())
    signature=hashlib.sha256(json.dumps([VERSION,max_per_project,manifest['signature']]).encode()).hexdigest()
    if CORPUS.exists():
        old=load_corpus()
        if old['metadata'].get('signature')==signature:return old
    heaps=defaultdict(list);population=Counter();scanned=0;eligible_unique=0
    with gzip.open(LOCAL/'reviews_scored.jsonl.gz','rt') as f:
        for line in f:
            r=json.loads(line);scanned+=1
            hits=[(pid,period) for pid,band,period in r['memberships'] if band=='near' and period in ('pre','post')]
            if not hits or not r['text'].strip():continue
            eligible_unique+=1
            slim={k:r[k] for k in ('review_id','business_id','date','stars','text')}
            slim['all_memberships']=r['memberships']
            rank=sample_rank(r['review_id'])
            for key in hits:
                population[key]+=1;heap=heaps[key]
                item=(-rank,r['review_id'],slim)
                if len(heap)<max_per_project:heapq.heappush(heap,item)
                elif rank < -heap[0][0]:heapq.heapreplace(heap,item)
    selected={}
    for (pid,period),heap in sorted(heaps.items()):
        for _,rid,r in heap:
            item=selected.setdefault(rid,{**r,'memberships':[]})
            item['memberships'].append([pid,'near',period])
    records=[selected[k] for k in sorted(selected,key=lambda rid:(sample_rank(rid),rid))]
    corpus={'metadata':{'version':VERSION,'signature':signature,'sample_method':'Lowest SHA256 review-ID ranks independently within each nearby project/period; shared selected reviews deduplicated','max_reviews_per_project_period':max_per_project,'source_reviews_scanned':scanned,'eligible_near_pre_post_unique_reviews':eligible_unique,'unique_selected_reviews':len(records),'project_period_counts':{'|'.join(k):{'available':population[k],'selected':len(heaps[k])} for k in sorted(heaps)}},'records':records}
    with gzip.open(CORPUS,'wt') as f:json.dump(corpus,f,separators=(',',':'))
    print(f'Advanced corpus: {len(records):,} unique selected / {eligible_unique:,} eligible near pre/post reviews',flush=True)
    return corpus


def load_corpus(path=CORPUS):
    with gzip.open(path,'rt') as f:return json.load(f)


def fit_topic_basis(texts):
    vectorizer=TfidfVectorizer(ngram_range=(1,2),max_features=8000,min_df=2,max_df=.95,stop_words='english',sublinear_tf=True,strip_accents='unicode')
    X=vectorizer.fit_transform(texts)
    model=NMF(n_components=N_TOPICS,init='nndsvda',random_state=42,max_iter=300,tol=1e-4)
    with threadpool_limits(limits=1):model.fit(X)
    return vectorizer,model


def lexical_features(text):
    words=[w.lower() for w in WORD.findall(text)];n=len(words)
    return {'word_count':n,'lexical_diversity':len(set(words))/n if n else 0.,'negation_count':sum(w in NEGATIONS for w in words)}


def normalized_weights(weights):
    totals=weights.sum(axis=1,keepdims=True)
    return np.divide(weights,totals,out=np.zeros_like(weights),where=totals>0)


def aggregate_features(records,weights,project_ids,period='pre'):
    buckets={pid:[] for pid in project_ids}
    for i,r in enumerate(records):
        for pid,band,rperiod in r['memberships']:
            if pid in buckets and band=='near' and rperiod==period:buckets[pid].append(i)
    result={}
    normalized=normalized_weights(weights)
    for pid,indices in buckets.items():
        if not indices:
            result[pid]={'n_reviews':0,'n_businesses':0,'n_topic_mapped_reviews':0,'topic_distribution':None,'topic_entropy':None,'mean_word_count':None,'mean_lexical_diversity':None,'negation_per_100_words':None};continue
        values=normalized[indices];mapped=values.sum(axis=1)>0
        dist=values[mapped].mean(axis=0) if mapped.any() else np.zeros(weights.shape[1])
        positive=dist[dist>0];entropy=float(np.clip(-np.sum(positive*np.log(positive))/math.log(weights.shape[1]),0,1)) if len(positive) else None
        lex=[lexical_features(records[i]['text']) for i in indices]
        words=sum(x['word_count'] for x in lex)
        result[pid]={'n_reviews':len(indices),'n_businesses':len({records[i]['business_id'] for i in indices}),'n_topic_mapped_reviews':int(mapped.sum()),'topic_distribution':dist.tolist() if mapped.any() else None,'topic_entropy':entropy,'mean_word_count':float(np.mean([x['word_count'] for x in lex])),'mean_lexical_diversity':float(np.mean([x['lexical_diversity'] for x in lex])),'negation_per_100_words':100*sum(x['negation_count'] for x in lex)/words if words else None}
    return result


def topic_features(records,vectorizer,topic_model,project_ids,period='pre'):
    with threadpool_limits(limits=1):weights=topic_model.transform(vectorizer.transform([r['text'] for r in records]))
    return aggregate_features(records,weights,project_ids,period)


def build_artifact(corpus,evidence):
    records=corpus['records']
    baseline=[r for r in records if any(band=='near' and period=='pre' for _,band,period in r['memberships'])]
    vectorizer,model=fit_topic_basis([r['text'] for r in baseline])
    with threadpool_limits(limits=1):weights=model.transform(vectorizer.transform([r['text'] for r in records]))
    names=vectorizer.get_feature_names_out();ids=[p['id'] for p in evidence['projects']]
    pre=aggregate_features(records,weights,ids,'pre');post=aggregate_features(records,weights,ids,'post')
    normalized=normalized_weights(weights);baseline_indices=[i for i,r in enumerate(records) if any(period=='pre' for _,_,period in r['memberships'])]
    topics=[]
    for ti,components in enumerate(model.components_):
        ranked=np.argsort(components)[::-1][:12]
        examples=[];seen_businesses=set()
        # Weight favors substantively represented topics, not merely a pure but tiny projection.
        for i in sorted(baseline_indices,key=lambda i:float(weights[i,ti]),reverse=True):
            r=records[i]
            if r['business_id'] in seen_businesses:continue
            pid=next(pid for pid,_,period in r['memberships'] if period=='pre')
            clean=re.sub(r'\s+',' ',r['text']).strip()
            match=re.search(r'\b'+re.escape(str(names[ranked[0]]))+r'\b',clean,re.I)
            start=max(0,match.start()-70) if match else 0
            excerpt=('…' if start else '')+clean[start:start+240]+('…' if start+240<len(clean) else '')
            examples.append({'text':excerpt,'project_id':pid,'period':'pre','topic_weight':float(normalized[i,ti]),'review_key':hashlib.sha256(r['review_id'].encode()).hexdigest()[:16]})
            seen_businesses.add(r['business_id'])
            if len(examples)==3:break
        topics.append({'id':f'topic_{ti+1}','top_terms':names[ranked].tolist(),'term_weights':components[ranked].tolist(),'representative_excerpts':examples})
    return {'version':VERSION,'method':{'representation':'TF-IDF unigrams and bigrams; English stop words; sublinear term frequency','decomposition':'Nonnegative matrix factorization, five topics, random_state42','vocabulary_max_features':8000,'minimum_document_frequency':2,'maximum_document_frequency':.95,'fit_scope':'Unique sampled nearby baseline reviews only, across all projects; descriptive basis, not predictive validation','post_scope':'Post reviews transformed with the frozen baseline vocabulary and topic basis','topic_distribution':'Mean normalized review-topic weights; unmapped reviews excluded and counted','topic_entropy':'Shannon entropy of mean topic mixture divided by log(5); 0 concentrated to1 diffuse','lexical_diversity':'Mean per-review unique-word / word ratio; affected by review length','negation':'Lexical negation words per100 words; not sentiment','language_note':'English-centric stop words and lexical tokenization; language detection not performed.','selection_note':'Topics are unsupervised patterns, not validated civic-issue labels. Top terms are shown without invented names.','predictive_validation':'Any predictive challenger must refit TF-IDF and NMF inside each fold and exclude held-out/shared review IDs; never use these descriptive full-sample topic features as held-out evidence.'},'coverage':{**corpus['metadata'],'unique_baseline_fit_reviews':len(baseline),'learned_vocabulary_size':len(names),'nmf_iterations':int(model.n_iter_),'nmf_reconstruction_error':float(model.reconstruction_err_),'source_evidence_sha256':hashlib.sha256(EVIDENCE.read_bytes()).hexdigest()},'topics':topics,'projects':[{'id':p['id'],'project':p['project'],'pre':pre[p['id']],'post':post[p['id']],'topic_change':(np.asarray(post[p['id']]['topic_distribution'])-np.asarray(pre[p['id']]['topic_distribution'])).tolist() if pre[p['id']]['topic_distribution'] is not None and post[p['id']]['topic_distribution'] is not None else None} for p in evidence['projects']]}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--max-per-project',type=int,default=1200);args=parser.parse_args()
    corpus=build_corpus(args.max_per_project);artifact=build_artifact(corpus,json.loads(EVIDENCE.read_text()))
    OUT.write_text(json.dumps(artifact,indent=2,allow_nan=False)+'\n');print('Wrote',OUT,flush=True)
if __name__=='__main__':main()
