"""Build auditable project evidence from local Yelp archive.

Run ../.venv/bin/python src/build_project_evidence.py --workers 4
Raw text, identifiers and label tasks stay under ignored data/interim/. Published
JSON contains aggregates and short excerpts only. --rebuild-cache forces a scan.
"""
import argparse
import csv
import gzip
import hashlib
import json
import multiprocessing as mp
import random
import tarfile
import time
from collections import Counter, defaultdict
from pathlib import Path
from project_registry import ROOT, load_registry, build_cohorts
from project_text import VERSION, TOPICS, analyze_text
ARCHIVE=ROOT/'Yelp JSON/yelp_dataset.tar'
LOCAL=ROOT/'data/interim/project_evidence'
OUT=ROOT/'data/derived/project_evidence.json'


def period_for_year(project,year):
    for period in ('early','pre','post'):
        if year in project[period+'_years']:return period
    return None


def score_record(record):
    record['analysis']=analyze_text(record['text'])
    return record


def eligible_reviews(assignments,projects):
    indexed={p['id']:p for p in projects};scanned=0;kept=0;seen_ids=set()
    with tarfile.open(ARCHIVE,'r|*') as archive:
        for member in archive:
            if member.name.endswith('yelp_academic_dataset_review.json'):
                for line in archive.extractfile(member):
                    scanned+=1
                    r=json.loads(line)
                    memberships=[]
                    for pid,band in assignments.get(r['business_id'],[]):
                        period=period_for_year(indexed[pid],int(r['date'][:4]))
                        if period:memberships.append([pid,band,period])
                    if memberships:
                        if r['review_id'] in seen_ids:raise ValueError('Duplicate source review ID '+r['review_id'])
                        seen_ids.add(r['review_id'])
                        kept+=1
                        yield {'review_id':r['review_id'],'business_id':r['business_id'],'date':r['date'][:10],'stars':r['stars'],'text':r.get('text',''),'memberships':memberships}
                    if scanned%1000000==0:print(f'Scanned {scanned:,}; eligible unique reviews {kept:,}',flush=True)
                break
    if not scanned:raise ValueError('Review archive member missing or empty')
    print(f'Completed scan: {scanned:,} source reviews; {kept:,} unique eligible reviews',flush=True)


def signature(projects):
    fingerprints={}
    for p in projects:
        for rel in [p['geometry'].get('path'),p.get('cohort_fixture')]:
            if rel:fingerprints[rel]=hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()
    return hashlib.sha256(json.dumps([projects,fingerprints,VERSION,ARCHIVE.stat().st_size],sort_keys=True).encode()).hexdigest()


def cache_reviews(assignments,projects,workers,rebuild=False):
    LOCAL.mkdir(parents=True,exist_ok=True)
    cache=LOCAL/'reviews_scored.jsonl.gz';manifest=LOCAL/'cache_manifest.json'
    sig=signature(projects)
    if not rebuild and cache.exists() and manifest.exists() and json.loads(manifest.read_text()).get('signature')==sig:
        print('Reusing matching scored review cache',flush=True);return cache
    temp=cache.with_suffix('.tmp');start=time.monotonic();count=0
    with gzip.open(temp,'wt',compresslevel=1) as out:
        with mp.Pool(workers) as pool:
            for r in pool.imap(score_record,eligible_reviews(assignments,projects),chunksize=128):
                out.write(json.dumps(r,separators=(',',':'))+'\n');count+=1
                if count%25000==0:print(f'Scored {count:,} unique reviews in {time.monotonic()-start:.1f}s',flush=True)
    temp.replace(cache)
    manifest.write_text(json.dumps({'signature':sig,'unique_reviews':count,'seconds':round(time.monotonic()-start,2),'extraction_version':VERSION},indent=2)+'\n')
    return cache


def accumulator():
    return {'n':0,'missing_text':0,'business_text':defaultdict(lambda:[0,0.,0,0,0,0]),'stars':0,'compound':0.,'negative':0,'place':0,'access':0,'realm':0,'businesses':set(),'topics':defaultdict(lambda:Counter()),'years':Counter()}


def add(cell,review):
    a=review['analysis'];cell['n']+=1;cell['stars']+=review['stars'];cell['compound']+=a['compound']
    cell['negative']+=a['compound']<=-.05;cell['place']+=a['place'];cell['access']+=a['access_friction'];cell['realm']+=a['public_realm_complaint']
    cell['businesses'].add(review['business_id']);cell['years'][review['date'][:4]]+=1
    has_text=bool((review.get('text') or '').strip())
    cell['missing_text']+=not has_text
    if has_text:
        b=cell['business_text'][review['business_id']]
        for i,value in enumerate((1,a['compound'],a['compound']<=-.05,a['place'],a['access_friction'],a['public_realm_complaint'])):b[i]+=value
    for topic,flags in a['topics'].items():
        cell['topics'][topic]['n']+=1;cell['topics'][topic]['negative']+=flags['negative'];cell['topics'][topic]['area']+=flags['area']


def summarize(cell):
    n=cell['n'];text_n=n-cell['missing_text'];divide=lambda x:x/text_n if text_n else None
    business=list(cell['business_text'].values())
    balanced={k:sum(b[i]/b[0] for b in business)/len(business) if business else None for k,i in [('mean_sentiment',1),('negative_share',2),('place_discussion_share',3),('access_friction_share',4),('public_realm_complaint_share',5)]}
    balanced['n_businesses']=len(business)
    balanced['largest_business_review_share']=max((b[0] for b in business),default=0)/text_n if text_n else None
    balanced['business_reporting_share']={k:sum(b[i]>0 for b in business)/len(business) if business else None for k,i in [('place_discussion',3),('access_friction',4),('public_realm_complaint',5)]}
    return {'n_reviews':n,'n_businesses':len(cell['businesses']),'n_text_reviews':text_n,'n_missing_text':cell['missing_text'],'text_completeness':text_n/n if n else None,'business_balanced':balanced,'mean_stars':cell['stars']/n if n else None,'mean_sentiment':divide(cell['compound']),
     'negative_share':divide(cell['negative']),'place_discussion_share':divide(cell['place']),'access_friction_share':divide(cell['access']),'public_realm_complaint_share':divide(cell['realm']),
     'text_counts':{'place_discussion':cell['place'],'access_friction':cell['access'],'public_realm_complaint':cell['realm']},
     'by_year':dict(sorted(cell['years'].items())),
     'topics':{topic:{'n_reviews':cell['topics'][topic]['n'],'share':divide(cell['topics'][topic]['n']),'negative_reviews':cell['topics'][topic]['negative'],'negative_share':divide(cell['topics'][topic]['negative']),'area_reviews':cell['topics'][topic]['area']} for topic in TOPICS},
     'text_support':'thin' if text_n<100 or len(business)<20 else 'available_provisional'}


def primary_outcome(near,far,cost):
    np=near['pre']['n_reviews'];npost=near['post']['n_reviews'];fp=far['pre']['n_reviews'];fpost=far['post']['n_reviews']
    factor=fpost/fp if fp else None;expected=np*factor if factor is not None else None;net=npost-expected if expected is not None else None
    eligible=near['pre']['n_businesses']>=20 and np>0 and fp>0 and cost>0
    return {'far_growth_factor':factor,'expected_near_post':expected,'net_review_difference':net,'ce_reviews_per_million':net/cost if eligible else None,'eligible':eligible,'reason':None if eligible else 'Insufficient baseline support: at least 20 nearby reviewed businesses and positive near/comparison baseline counts required','unit':'growth-adjusted excess Yelp reviews per $1M reported project cost'}


def aggregate(cache,projects,inventories):
    cells=defaultdict(accumulator);excerpts={};examples_seen=Counter();unique=0;multi=0;membership_count=0;missing_text=0
    # Independent seeded reservoir samples: random reviews and candidate clauses.
    rng=random.Random(509);random_sample=[];candidate_sample=[];candidate_seen=0
    strat_rng=random.Random(510);strata=defaultdict(list);strata_seen=Counter()
    for line in gzip.open(cache,'rt'):
        r=json.loads(line);unique+=1;missing_text+=not bool((r.get('text') or '').strip());membership_count+=len(r['memberships']);multi+=len({m[0] for m in r['memberships']})>1
        for pid,band,period in r['memberships']:
            add(cells[(pid,band,period)],r)
            if band=='near' and period in ('pre','post'):
                # Supplement the representative pooled samples with coverage of
                # every project/period/topic, including rare or ambiguous labels.
                for ev in r['analysis']['evidence']:
                    if ev['topic']=='food_service_value':continue
                    skey=(pid,period,ev['topic']);strata_seen[skey]+=1
                    item={'review_id':r['review_id'],'business_id':r['business_id'],'date':r['date'],'memberships':r['memberships'],'text':ev['text'],'review_text':r['text'],'candidate_topic':ev['topic'],'sampling_frame':'stratified_project_period_topic','stratum_project':pid,'stratum_period':period,'label_target':'','label_topics':'','label_polarity':'','reviewer_type':'','reviewer_id':'','notes':''}
                    bucket=strata[skey]
                    if len(bucket)<2:bucket.append(item)
                    else:
                        j=strat_rng.randrange(strata_seen[skey])
                        if j<2:bucket[j]=item
                for ev in r['analysis']['evidence']:
                    if ev['target']!='area':continue
                    key=(pid,period,ev['topic'],ev['polarity']);examples_seen[key]+=1
                    if key not in excerpts or rng.randrange(examples_seen[key])==0:
                        excerpts[key]={**ev,'review_key':hashlib.sha256(r['review_id'].encode()).hexdigest()[:16],'band':band,'period':period,'date':r['date'],'stars':r['stars']}
        item={'review_id':r['review_id'],'business_id':r['business_id'],'date':r['date'],'memberships':r['memberships'],'text':r['text'],'sampling_frame':'random_review','label_target':'','label_topics':'','label_polarity':'','reviewer_type':'','reviewer_id':'','notes':''}
        if len(random_sample)<200:random_sample.append(item)
        else:
            j=rng.randrange(unique)
            if j<200:random_sample[j]=item
        for ev in r['analysis']['evidence']:
            if ev['topic']=='food_service_value':continue
            candidate_seen+=1
            item={'review_id':r['review_id'],'business_id':r['business_id'],'date':r['date'],'memberships':r['memberships'],'text':ev['text'],'review_text':r['text'],'candidate_topic':ev['topic'],'sampling_frame':'candidate_clause','label_target':'','label_topics':'','label_polarity':'','reviewer_type':'','reviewer_id':'','notes':''}
            if len(candidate_sample)<200:candidate_sample.append(item)
            else:
                j=rng.randrange(candidate_seen)
                if j<200:candidate_sample[j]=item
    stratified_sample=[row for key in sorted(strata) for row in strata[key]]
    annotation={'method':'Seeded reservoirs: 200 uniformly sampled eligible reviews and 200 uniformly sampled noncommercial candidate clauses. Different sampling frames; not prevalence weighted. Additional strata contain up to two candidate clauses per nearby project/period/topic. These enriched strata are not population-weighted. Labels blank. Reviewers should not view rule polarity before annotation.','independently_human_reviewed':0,'agent_reviewed':0,'rows':random_sample+candidate_sample+stratified_sample,'strata':{'|'.join(k):{'eligible_clauses':strata_seen[k],'sampled':len(strata[k])} for k in sorted(strata)}}
    (LOCAL/'annotation_sample.json').write_text(json.dumps(annotation,indent=2)+'\n')
    result=[]
    for p in projects:
        pid=p['id'];periods={band:{period:summarize(cells[(pid,band,period)]) for period in ('early','pre','post')} for band in ('near','far')}
        pre=periods['near']['pre'];primary=primary_outcome(periods['near'],periods['far'],p['cost_millions'])
        near_ids=set(inventories[pid]['near']);overlap={q['id']:len(near_ids & set(inventories[q['id']]['near'])) for q in projects if q['id']!=pid}
        result.append({**p,'periods':periods,'features':{'near_pre_reviews':pre['n_reviews'],'near_baseline_reviewed':pre['n_businesses'],'baseline_review_intensity':pre['n_reviews']/pre['n_businesses'] if pre['n_businesses'] else None,**{k:pre[k] for k in ('place_discussion_share','access_friction_share','public_realm_complaint_share')}},'primary':primary,
          'excerpts':[v for k,v in sorted(excerpts.items()) if k[0]==pid],
          'coverage':{'near_listings':len(inventories[pid]['near']),'far_listings':len(inventories[pid]['far']),'near_listing_overlap':{k:v for k,v in overlap.items() if v},'geography_method':'fixed full-route cohort fixture' if p.get('cohort_fixture') else 'coordinate distance; no city or state-name cutoff','baseline_timing':'pre-opening; not necessarily pre-construction','pandemic_post_period':2020 in p['post_years'],'source_vintage':'Yelp Open Dataset January 2022'}})
    return {'version':'project-evidence-v1','method':{'outcome':'Near post minus near pre multiplied by comparison post/pre, divided by reported project cost in $M','near_distance_m':500,'comparison_distance_m':[1500,8000],'minimum_baseline_businesses':20,'sentiment':'Whole-review VADER plus provisional clause-level target-aware keyword rules','text_rule_version':VERSION,'polarity_unit':'negative fraction of reviews with nonempty text; topic negative counts require an area target','business_balanced':'Equal mean of each reviewed business text rate; business_reporting_share counts businesses with at least one mention. Excludes missing text.','feature_timing':'Only predefined baseline years enter prediction features; construction timing may overlap','identity':'Reviews scored once by review ID; shared project memberships aggregated separately'},
     'quality':{'status':'provisional_rules_unvalidated','independently_human_reviewed':0,'agent_reviewed':0,'empirical_precision':None,'empirical_recall':None,'annotation_samples':len(random_sample)+len(candidate_sample)+len(stratified_sample),'annotation_frames':{'random_reviews':len(random_sample),'candidate_clauses':len(candidate_sample),'project_period_topic_strata':len(stratified_sample)},'annotation_path':'data/interim/project_evidence/annotation_sample.json','limitations':['Yelp reviewers are not a representative resident sample.','Lexical targets and polarity can be wrong; empirical label accuracy not established.','Review volume is not revenue, economic return, or causal benefit.','Text enrichment adds features, not independent project outcomes.']},
     'coverage':{'n_projects':len(result),'n_eligible_projects':sum(p['primary']['eligible'] for p in result),'unique_reviews_scored':unique,'n_missing_text_reviews':missing_text,'text_completeness':(unique-missing_text)/unique if unique else None,'review_project_period_memberships':membership_count,'reviews_shared_across_projects':multi,'source_vintage':'January 2022','near_baseline_reviews':sum(p['periods']['near']['pre']['n_reviews'] for p in result),'cities':sorted({p['city'] for p in projects}),'cache_manifest':json.loads((LOCAL/'cache_manifest.json').read_text())},'projects':result}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--workers',type=int,default=4);parser.add_argument('--rebuild-cache',action='store_true');args=parser.parse_args()
    projects=load_registry();assignments,inventories,_=build_cohorts(projects)
    for p in projects:print(p['project'], {b:len(v) for b,v in inventories[p['id']].items()},flush=True)
    cache=cache_reviews(assignments,projects,args.workers,args.rebuild_cache)
    artifact=aggregate(cache,projects,inventories);OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(artifact,indent=2,allow_nan=False)+'\n')
    print('Wrote',OUT,artifact['coverage'],flush=True)
if __name__=='__main__':main()
