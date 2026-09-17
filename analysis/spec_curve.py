"""Specification curve + placebo tests for the assistance/sentiment association.

Runs every defensible analytic choice rather than selecting one, so the reported
result does not depend on researcher degrees of freedom. Deterministic: no
sampling, no RNG, fixed input hashes.
"""
import json, hashlib, itertools, sys
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path('nsm')
OUT = Path('spec_curve_results.csv')

# ---------------------------------------------------------------- inputs
metro = json.loads((ROOT / 'data/interim/metro_zips.json').read_text())
zip_metro = {z: m for m, zs in metro.items() for z in zs}
valid = pd.read_pickle('funding_valid.pkl')
sent = pd.read_csv(ROOT / 'data/interim/sentiment_zip_quarter.csv', dtype={'zip5': str})
sent['metro'] = sent.zip5.map(zip_metro)
sent['q'] = pd.PeriodIndex(sent.quarter, freq='Q')
sent['year'] = sent.q.dt.year

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]

PROVENANCE = {
    'metro_zips.json': sha(ROOT / 'data/interim/metro_zips.json'),
    'sentiment_zip_quarter.csv': sha(ROOT / 'data/interim/sentiment_zip_quarter.csv'),
    'funding_rows': int(len(valid)),
    'sentiment_rows': int(len(sent)),
}

# ---------------------------------------------------------------- exposure definitions
KEYWORD = (r'\bhousing\b|community development|\btransit\b|transportation'
           r'|infrastructure|\bwater\b|\bsewer\b|construction')
# programs whose money plausibly changes a street, not a balance sheet
PLACE_CFDA = {'14.218', '14.239', '14.850', '20.205', '20.507', '66.458', '66.468'}

valid = valid.copy()
valid['q'] = pd.PeriodIndex(valid.date.dt.to_period('Q'), freq='Q')
valid['kw'] = (valid.cfda_title + ' ' + valid.transaction_description
               ).str.contains(KEYWORD, case=False, regex=True)
valid['place'] = valid.cfda_number.isin(PLACE_CFDA)

valid['pos'] = valid.obligation.clip(lower=0)
valid['one'] = 1.0

EXPOSURES = {
    'all assistance':      valid,
    'keyword-screened':    valid[valid.kw],
    'place-based CFDA':    valid[valid.place],
}
AMOUNTS = {'net obligations':'obligation', 'gross positive':'pos', 'transaction count':'one'}
THRESHOLDS = [10, 30, 100]
LAGS = [0, 1, 2, 4]              # quarters between funding and sentiment
PLACEBO_LAGS = [-1, -2, -4]      # funding AFTER sentiment: must be null
VARIATIONS = ['pooled', 'within-ZIP', 'between-ZIP']
WINDOWS = {'2012-2021': None, '2012-2019': 2019}


def build(expo_df, amount_col, lag, window_end):
    """Funding aggregated to ZIP-quarter, shifted by `lag` quarters, joined to sentiment."""
    f = expo_df
    if window_end is not None:
        f = f[f.date.dt.year <= window_end]
    if not len(f):
        return None
    agg = f.groupby(['zip5', 'q'], observed=True)[amount_col].sum().rename('amount').reset_index()
    agg['q'] = agg['q'] + lag          # funding at t-lag lines up with sentiment at t
    return agg


def run(expo_name, amount_name, thresh, lag, variation, window_name):
    window_end = WINDOWS[window_name]
    agg = build(EXPOSURES[expo_name], AMOUNTS[amount_name], lag, window_end)
    if agg is None:
        return None
    s = sent[sent.n_reviews >= thresh]
    if window_end is not None:
        s = s[s.year <= window_end]
    j = s.merge(agg, on=['zip5', 'q'], how='inner', validate='one_to_one')
    if len(j) < 100:
        return None
    j = j.copy()
    j['x'] = np.sign(j.amount) * np.log10(1 + j.amount.abs())
    if variation == 'within-ZIP':
        keep = j.groupby('zip5').zip5.transform('size') >= 2
        j = j[keep].copy()
        if len(j) < 100:
            return None
        for c in ('x', 'mean_compound'):
            j[c] = j[c] - j.groupby('zip5')[c].transform('mean')
    elif variation == 'between-ZIP':
        j = j.groupby('zip5')[['x', 'mean_compound']].mean().reset_index()
        if len(j) < 30:
            return None
    if j.x.std() == 0 or j.mean_compound.std() == 0:
        return None
    r = float(j[['x', 'mean_compound']].corr().iloc[0, 1])
    return dict(exposure=expo_name, amount=amount_name, min_reviews=thresh, lag=lag,
                variation=variation, window=window_name, n=int(len(j)), r=round(r, 5))


def sweep(lags, tag):
    rows = []
    for e, a, t, l, v, w in itertools.product(
            EXPOSURES, AMOUNTS, THRESHOLDS, lags, VARIATIONS, WINDOWS):
        out = run(e, a, t, l, v, w)
        if out:
            out['family'] = tag
            rows.append(out)
    return pd.DataFrame(rows)


real = sweep(LAGS, 'specification')
placebo = sweep(PLACEBO_LAGS, 'placebo (funding after sentiment)')
res = pd.concat([real, placebo], ignore_index=True)
res.to_csv(OUT, index=False)

pd.set_option('display.width', 150)
print('PROVENANCE', json.dumps(PROVENANCE))
print(f'\nspecifications run: {len(real)}   placebo: {len(placebo)}\n')

def describe(df, label):
    r = df.r
    print(f'{label}')
    print(f'  n specs {len(df):>4} | median r {r.median():+.4f} | IQR [{r.quantile(.25):+.4f}, {r.quantile(.75):+.4f}]'
          f' | min {r.min():+.4f} max {r.max():+.4f}')
    print(f'  share positive {(r > 0).mean():.1%} | share |r|>0.05 {(r.abs() > .05).mean():.1%}'
          f' | share |r|>0.10 {(r.abs() > .10).mean():.1%}')

describe(real, 'ALL SPECIFICATIONS')
print()
describe(placebo, 'PLACEBO (funding dated AFTER the sentiment it "predicts")')

print('\nBY VARIATION (the choice that matters most)')
print(real.groupby('variation').r.agg(['size', 'median', 'min', 'max']).round(4).to_string())
print('\nBY EXPOSURE DEFINITION')
print(real.groupby('exposure').r.agg(['size', 'median', 'min', 'max']).round(4).to_string())
print('\nWITHIN-ZIP ONLY, BY EXPOSURE AND LAG  (the causal-relevant cell)')
w = real[real.variation == 'within-ZIP']
print(w.pivot_table(index='exposure', columns='lag', values='r', aggfunc='median').round(4).to_string())
