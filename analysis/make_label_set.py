"""Stage 2: build the hand-labelling set that turns the aspect screen into a classifier.

The regex screen in aspect_extract.py is recall-oriented and its precision is poor:
inspection found venue noise, hotel-room trash, a business's own parking lot and the
idiom "should be a crime" all matched. Those are BUSINESS attributes, not NEIGHBOURHOOD
attributes, and the distinction is the whole point of the project.

This draws a stratified sample for humans to label on two axes:

  relevance : does the sentence describe the AREA AROUND the business (street, block,
              parking situation, transit, safety of the surroundings), or the business
              itself (its interior, its staff, its own lot)?  -> area / business / unclear
  polarity  : if area-relevant, is the area described positively, negatively or neutrally?
              -> pos / neg / neu / na

Stratified by aspect and by sentence-level VADER band so the labelled set covers the
score range rather than piling up on the mode. Seeded; rerunning gives the same sample.

Usage:
  python analysis/make_label_set.py <aspect_sentences.csv.gz> [out.csv] [n_per_aspect]
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd

SEED = 509
src = Path(sys.argv[1])
out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path('aspect_label_set.csv')
per_aspect = int(sys.argv[3]) if len(sys.argv) > 3 else 100

d = pd.read_csv(src)
print(f'loaded {len(d):,} sentences across {d.aspect.nunique()} aspects')

# VADER band -- so the sample spans the score range, not just the mode
d['band'] = pd.cut(d.sentence_compound, [-1.01, -0.5, -0.05, 0.05, 0.5, 1.01],
                   labels=['very neg', 'neg', 'neutral', 'pos', 'very pos'])

rng = np.random.default_rng(SEED)
picks = []
for aspect, g in d.groupby('aspect'):
    bands = [b for b in g.band.cat.categories if (g.band == b).any()]
    per_band = max(1, per_aspect // len(bands))
    for b in bands:
        gb = g[g.band == b]
        take = min(per_band, len(gb))
        idx = rng.choice(len(gb), take, replace=False)
        picks.append(gb.iloc[idx])
sample = pd.concat(picks, ignore_index=True)
sample = sample.sample(frac=1, random_state=SEED).reset_index(drop=True)  # shuffle so
# labellers cannot infer the aspect from position and anchor on it

sample.insert(0, 'row_id', range(1, len(sample) + 1))
sample['label_relevance'] = ''      # area | business | unclear
sample['label_polarity'] = ''       # pos | neg | neu | na
sample['labeller'] = ''
sample['notes'] = ''

cols = ['row_id', 'sentence', 'aspect', 'label_relevance', 'label_polarity',
        'labeller', 'notes', 'sentence_compound', 'stars', 'zip5', 'quarter',
        'review_id', 'business_id']
sample[cols].to_csv(out, index=False)

print(f'\nwrote {out}  ({len(sample)} sentences to label)')
print('\nper aspect:')
print(sample.aspect.value_counts().to_string())
print('\nper VADER band:')
print(sample.band.value_counts().reindex(
    ['very neg', 'neg', 'neutral', 'pos', 'very pos']).to_string())
print(f"""
HOW TO LABEL
  label_relevance
    area      the sentence says something about the surroundings -- the street, the
              block, the walk to it, street parking, the safety or state of the area
    business  the sentence is about the business itself: its interior, its staff, its
              own lot, its food. Includes idioms ("should be a crime").
    unclear   genuinely ambiguous; use sparingly and say why in notes
  label_polarity   only when relevance == area
    pos / neg / neu, else na

  Split the file between labellers, keep ~40 rows overlapping so inter-rater
  agreement can be reported. Do NOT look at sentence_compound while labelling -- it
  is the thing being validated.
""")
