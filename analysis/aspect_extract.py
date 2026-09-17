"""Stage 1 of aspect-based neighbourhood sentiment: find and score aspect sentences.

Whole-review VADER is the wrong instrument for this project. Its compound score is
normalised across the document, so a long complaint about the street drifts positive
if the food was good -- we measured that: among 1-2 star reviews the score flips sign
around 100 words. Scoring the SENTENCE that mentions the aspect removes that failure
mode by construction.

This script is a recall-oriented CANDIDATE GENERATOR, not a classifier. A matched
sentence is a candidate for review, exactly like the award keyword screen in the
Milestone 2 notebook: "dirty" may describe a bathroom rather than a street. Precision
is an open question to be settled by hand-labelling a sample, not asserted here.

Usage:
  python analysis/aspect_extract.py "<path to yelp_dataset.tar>" [out.csv.gz]

Deterministic: no sampling, no RNG. Output is one row per (review, aspect, sentence).
"""
import sys, json, re, tarfile, io, gzip, csv, time
from pathlib import Path
from collections import Counter
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# --- the study frame -------------------------------------------------------
STUDY = None
for cand in (Path('data/interim/metro_zips.json'), Path('nsm/data/interim/metro_zips.json'),
             Path(__file__).resolve().parent.parent / 'data/interim/metro_zips.json'):
    if cand.exists():
        STUDY = {z for zs in json.loads(cand.read_text()).values() for z in zs}
        print(f'study frame: {len(STUDY)} ZIPs from {cand}')
        break
if STUDY is None:
    sys.exit('metro_zips.json not found -- cannot define the study frame')

# --- aspect lexicon --------------------------------------------------------
# Neighbourhood attributes, not business attributes. Ambiguity is deliberate and
# documented: these generate candidates, and precision is measured downstream.
ASPECTS = {
    'parking':      r'\bparking\b|\bvalet\b|\bparked\b|\bparking lot\b|\bparking garage\b',
    'safety':       r'\bunsafe\b|\bsketchy\b|\bsketch\b|\bcrime\b|\brobbed\b|\bmugged\b'
                    r'|\bdangerous\b|\bshady\b|\bbroken into\b|\bpanhandl\w*|\bfeel safe\b',
    'cleanliness':  r'\bdirty\b|\bfilthy\b|\btrash\b|\blitter\w*|\bgarbage\b|\bgraffiti\b'
                    r'|\bgrimy\b|\brun[- ]?down\b|\bstink\w*|\bsmell(?:s|ed|y)?\b',
    'walkability':  r'\bwalkable\b|\bwalking distance\b|\bsidewalk\b|\bbus stop\b|\bsubway\b'
                    r'|\bmetro station\b|\blight rail\b|\bstreetcar\b|\bbike lane\b|\bcrosswalk\b',
    'noise':        r'\bnoisy\b|\bnoise\b|\btraffic noise\b|\bloud outside\b|\bsiren\w*\b',
    'construction': r'\bconstruction\b|\broad ?work\b|\bdetour\b|\bscaffolding\b|\btorn up\b',
    'area_general': r'\bneighborhood\b|\bneighbourhood\b|\bthis area\b|\bpart of town\b'
                    r'|\bgentrif\w*|\bup and coming\b|\brevitaliz\w*|\bthe block\b',
}
COMPILED = {a: re.compile(p, re.I) for a, p in ASPECTS.items()}
ANY = re.compile('|'.join(f'(?:{p})' for p in ASPECTS.values()), re.I)
# a cheap literal pre-filter so most reviews never touch a regex
PREFILTER = ('parking', 'valet', 'parked', 'unsafe', 'sketch', 'crime', 'robbed', 'mugged',
             'dangerous', 'shady', 'panhandl', 'safe', 'dirty', 'filthy', 'trash', 'litter',
             'garbage', 'graffiti', 'grimy', 'rundown', 'run-down', 'run down', 'stink', 'smell',
             'walkable', 'walking distance', 'sidewalk', 'bus stop', 'subway', 'metro station',
             'light rail', 'streetcar', 'bike lane', 'crosswalk', 'noisy', 'noise', 'siren',
             'construction', 'roadwork', 'road work', 'detour', 'scaffolding', 'torn up',
             'neighborhood', 'neighbourhood', 'this area', 'part of town', 'gentrif',
             'up and coming', 'revitaliz', 'the block')

SENT_SPLIT = re.compile(r'(?<=[.!?])\s+|\n+')

src = Path(sys.argv[1]).expanduser()
out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path('aspect_sentences.csv.gz')


def member(name):
    tf = tarfile.open(src)
    for m in tf.getmembers():
        if Path(m.name).name == name:
            return io.TextIOWrapper(tf.extractfile(m), encoding='utf-8')
    raise FileNotFoundError(name)


def records(fh):
    first = fh.read(1)
    while first and first.isspace():
        first = fh.read(1)
    fh.seek(0)
    if first == '[':
        yield from json.load(fh)
    else:
        for line in fh:
            line = line.strip().rstrip(',')
            if line and line not in '[]':
                try:
                    yield json.loads(line)
                except ValueError:
                    continue


print('reading businesses...')
biz = {}
with member('yelp_academic_dataset_business.json') as fh:
    for b in records(fh):
        z = str(b.get('postal_code') or '').strip()
        if z in STUDY:
            biz[b['business_id']] = z
print(f'study businesses: {len(biz):,}')

analyzer = SentimentIntensityAnalyzer()
stats = Counter()
t0 = time.time()

with gzip.open(out_path, 'wt', newline='', encoding='utf-8') as gz:
    w = csv.writer(gz)
    w.writerow(['review_id', 'business_id', 'zip5', 'date', 'quarter', 'stars',
                'aspect', 'sentence_compound', 'review_words', 'sentence'])
    with member('yelp_academic_dataset_review.json') as fh:
        for r in records(fh):
            stats['scanned'] += 1
            z = biz.get(r.get('business_id'))
            if z is None:
                continue
            d = r.get('date') or ''
            if not ('2012' <= d[:4] <= '2021'):
                continue
            stats['in_frame'] += 1
            text = r.get('text') or ''
            low = text.lower()
            if not any(k in low for k in PREFILTER):
                continue
            if not ANY.search(text):
                continue
            stats['review_has_aspect'] += 1
            n_words = len(text.split())
            q = f"{d[:4]}Q{(int(d[5:7]) - 1) // 3 + 1}"
            wrote_for_review = set()
            for sent in SENT_SPLIT.split(text):
                sent = sent.strip()
                if not (10 <= len(sent) <= 600):
                    continue
                hits = [a for a, rx in COMPILED.items() if rx.search(sent)]
                if not hits:
                    continue
                comp = analyzer.polarity_scores(sent)['compound']
                for a in hits:
                    stats[f'sent::{a}'] += 1
                    wrote_for_review.add(a)
                    w.writerow([r.get('review_id'), r.get('business_id'), z, d[:10], q,
                                r.get('stars'), a, f'{comp:.4f}', n_words, sent])
                    stats['rows'] += 1
            for a in wrote_for_review:
                stats[f'rev::{a}'] += 1
            if stats['scanned'] % 1_000_000 == 0:
                print(f"  {stats['scanned']:,} scanned  {stats['rows']:,} rows  "
                      f"{time.time() - t0:.0f}s")

print(f"\ndone in {time.time() - t0:.0f}s -> {out_path}  ({out_path.stat().st_size / 1e6:.1f} MB)")
print(f"  reviews scanned        {stats['scanned']:,}")
print(f"  in study frame         {stats['in_frame']:,}")
print(f"  with >=1 aspect        {stats['review_has_aspect']:,} "
      f"({stats['review_has_aspect'] / max(stats['in_frame'],1):.1%} of frame)")
print(f"  aspect sentences       {stats['rows']:,}")
print('\n  reviews mentioning each aspect:')
for a in ASPECTS:
    n = stats[f'rev::{a}']
    print(f"    {a:<14}{n:>9,}  ({n / max(stats['in_frame'],1):5.2%} of reviews)")
