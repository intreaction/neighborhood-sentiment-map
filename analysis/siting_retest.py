"""Business-level site-selection retest on the FULL Yelp Open Dataset.

The 100k course sample said neighbourhood features do not predict a business's
own outcome (R2 -0.34 on rating, -0.11 on volume). That sample has a median of
8 reviews per business, so the target was mostly sampling noise. This rebuilds
the same test on the full corpus and varies the review threshold, which
separates "no signal" from "noisy target".

Usage
-----
  python analysis/siting_retest.py /path/to/yelp_dataset            # extracted dir
  python analysis/siting_retest.py /path/to/yelp_dataset.tar        # official tar

Accepts JSONL (official format) or a JSON array (the course sample's format).
Deterministic: fixed seed, fixed folds, no sampling.
"""
import sys, json, tarfile, io
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.model_selection import GroupKFold
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import RidgeCV
from sklearn.dummy import DummyRegressor
from sklearn.metrics import r2_score, mean_absolute_error

SEED = 509
STUDY_ZIPS = None
mz = Path('data/interim/metro_zips.json')
for cand in (mz, Path('nsm') / mz, Path(__file__).resolve().parent.parent / mz):
    if cand.exists():
        STUDY_ZIPS = {z for zs in json.loads(cand.read_text()).values() for z in zs}
        print(f'study ZIP frame: {len(STUDY_ZIPS)} ZIPs from {cand}')
        break
if STUDY_ZIPS is None:
    print('metro_zips.json not found -- running on all ZIPs in the dataset')


def iter_records(fh):
    """Yield dicts from JSONL or from a single JSON array."""
    first = fh.read(1)
    while first and first.isspace():
        first = fh.read(1)
    fh.seek(0)
    if first == '[':
        for rec in json.load(fh):
            yield rec
    else:
        for line in fh:
            line = line.strip().rstrip(',')
            if line and line not in '[]':
                try:
                    yield json.loads(line)
                except ValueError:
                    continue


def open_member(src: Path, name: str):
    if src.is_dir():
        for p in (src / name, src / 'yelp_dataset' / name):
            if p.exists():
                return open(p, encoding='utf-8')
        raise FileNotFoundError(f'{name} not under {src}')
    tf = tarfile.open(src)
    for m in tf.getmembers():
        if Path(m.name).name == name:
            return io.TextIOWrapper(tf.extractfile(m), encoding='utf-8')
    raise FileNotFoundError(f'{name} not in {src}')


src = Path(sys.argv[1]).expanduser()
print(f'source: {src}')

# ---- businesses ---------------------------------------------------------
rows = []
with open_member(src, 'yelp_academic_dataset_business.json') as fh:
    for b in iter_records(fh):
        z = str(b.get('postal_code') or '').strip()
        if STUDY_ZIPS is not None and z not in STUDY_ZIPS:
            continue
        if not z.isdigit() or len(z) != 5:
            continue
        attrs = b.get('attributes') or {}
        cats = b.get('categories') or ''
        rows.append((b['business_id'], z, attrs.get('RestaurantsPriceRange2'),
                     bool(set(cats.split(', ')) & {'Restaurants', 'Food', 'Bars', 'Cafes', 'Coffee & Tea'}),
                     b.get('is_open')))
B = pd.DataFrame(rows, columns=['business_id', 'zip5', 'price', 'is_food', 'is_open'])
B['price'] = pd.to_numeric(B.price, errors='coerce')
print(f'study businesses: {len(B):,} in {B.zip5.nunique()} ZIPs')
keep = set(B.business_id)

# ---- reviews: stream, accumulate per business ---------------------------
n_rev, sum_stars = {}, {}
scanned = 0
with open_member(src, 'yelp_academic_dataset_review.json') as fh:
    for r in iter_records(fh):
        scanned += 1
        bid = r.get('business_id')
        if bid not in keep:
            continue
        d = r.get('date') or ''
        if not ('2012' <= d[:4] <= '2021'):
            continue
        n_rev[bid] = n_rev.get(bid, 0) + 1
        sum_stars[bid] = sum_stars.get(bid, 0.0) + float(r.get('stars') or 0)
print(f'reviews scanned: {scanned:,}   matched to study businesses: {sum(n_rev.values()):,}')

B['n_rev'] = B.business_id.map(n_rev).fillna(0).astype(int)
B['sum_stars'] = B.business_id.map(sum_stars).fillna(0.0)

zs = B.groupby('zip5').agg(z_n=('n_rev', 'sum'), z_sum=('sum_stars', 'sum'),
                           z_biz=('business_id', 'size'))
B = B.join(zs, on='zip5')

FEATURES = ['loo_stars', 'log_loo_n', 'log_zip_biz', 'price', 'is_food']


def evaluate(min_rev):
    d = B[B.n_rev >= min_rev].copy()
    d['loo_n'] = d.z_n - d.n_rev
    d['loo_stars'] = (d.z_sum - d.sum_stars) / d.loo_n.replace(0, np.nan)
    d['zip_biz'] = d.z_biz - 1
    d = d[(d.loo_n >= 30) & (d.zip_biz >= 5)].dropna(subset=['loo_stars'])
    if len(d) < 500 or d.zip5.nunique() < 10:
        return None
    d['own_stars'] = d.sum_stars / d.n_rev
    d['log_rev'] = np.log10(d.n_rev)
    d['log_loo_n'] = np.log10(d.loo_n)
    d['log_zip_biz'] = np.log10(d.zip_biz)
    # CONCEPT features describe the business the founder already intends to open.
    # PLACE features describe the neighbourhood, and are the only thing a site
    # decision actually changes. The question is what PLACE adds on top of CONCEPT.
    CONCEPT = ['price', 'is_food']
    PLACE = ['loo_stars', 'log_loo_n', 'log_zip_biz']
    g = d.zip5
    out = {'min_rev': min_rev, 'n': len(d), 'zips': d.zip5.nunique()}

    def cv_r2(cols, y):
        if not cols:
            X0 = pd.DataFrame(index=d.index, data={'_c': 1.0})
        else:
            X0 = d[cols].astype(float)
        pred = np.zeros(len(y))
        for tr, te in GroupKFold(n_splits=5).split(X0, y, g):
            med = X0.iloc[tr].median()
            pred[te] = RidgeCV().fit(X0.iloc[tr].fillna(med), y.iloc[tr]
                                     ).predict(X0.iloc[te].fillna(med))
        return r2_score(y, pred)

    for label, col in (('rating', 'own_stars'), ('volume', 'log_rev')):
        y = d[col].astype(float)
        r_concept = cv_r2(CONCEPT, y)
        r_place = cv_r2(PLACE, y)
        r_full = cv_r2(CONCEPT + PLACE, y)
        out[f'{label}_concept'] = r_concept
        out[f'{label}_place'] = r_place
        out[f'{label}_full'] = r_full
        out[f'{label}_place_adds'] = r_full - r_concept   # <- the site-selection number
    return out


print('\nDoes the null survive a less noisy target?')
res = [r for r in (evaluate(m) for m in (3, 5, 10, 20, 50, 100)) if r]
R = pd.DataFrame(res).set_index('min_rev')
pd.set_option('display.width', 160)
print(R.round(4).to_string())
print('\nR2 below 0 means the features generalise worse than predicting the mean.')
print('If R2 rises toward 0+ as the threshold rises, the pilot null was target noise.')
print('If it stays negative at every threshold, neighbourhood genuinely does not')
print('predict an individual business outcome, and site-selection prediction is dead.')
R.to_csv('analysis/siting_retest_results.csv')
print('\nwrote analysis/siting_retest_results.csv')
