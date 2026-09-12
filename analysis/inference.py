"""EXPLORATORY (not pre-registered). Three questions the pooled null cannot answer
on its own:
  A. How big an effect could we have detected? (no-effect vs underpowered)
  B. Does anything appear at the top of the dose distribution? (too little money?)
  C. Is the cross-sectional signal just a proxy for how busy a place is?
"""
import json
import numpy as np, pandas as pd
from pathlib import Path

ROOT = Path('nsm')
metro = json.loads((ROOT / 'data/interim/metro_zips.json').read_text())
zip_metro = {z: m for m, zs in metro.items() for z in zs}
valid = pd.read_pickle('funding_valid.pkl')
sent = pd.read_csv(ROOT / 'data/interim/sentiment_zip_quarter.csv', dtype={'zip5': str})
sent['q'] = pd.PeriodIndex(sent.quarter, freq='Q')

PLACE_CFDA = {'14.218', '14.239', '14.850', '20.205', '20.507', '66.458', '66.468'}
valid = valid.copy()
valid['q'] = pd.PeriodIndex(valid.date.dt.to_period('Q'), freq='Q')
valid['place'] = valid.cfda_number.isin(PLACE_CFDA)

def panel(expo, lag=0):
    agg = expo.groupby(['zip5', 'q'], observed=True).obligation.sum().rename('amount').reset_index()
    agg['q'] = agg['q'] + lag
    j = sent[sent.n_reviews >= 30].merge(agg, on=['zip5', 'q'], how='inner', validate='one_to_one')
    j = j.copy()
    j['x'] = np.sign(j.amount) * np.log10(1 + j.amount.abs())
    return j

print('=' * 74)
print('A. WHAT SIZE OF EFFECT COULD WE HAVE SEEN?')
print('=' * 74)
j = panel(valid)
# intraclass correlation of sentiment within ZIP -> design effect -> effective n
g = j.groupby('zip5').mean_compound
k = g.size()
grand = j.mean_compound.mean()
ms_between = ((g.mean() - grand) ** 2 * k).sum() / (len(k) - 1)
ms_within = j.assign(d=(j.mean_compound - j.groupby('zip5').mean_compound.transform('mean')) ** 2
                     ).d.sum() / (len(j) - len(k))
m_bar = len(j) / len(k)
icc = max(0.0, (ms_between - ms_within) / (ms_between + (m_bar - 1) * ms_within))
deff = 1 + (m_bar - 1) * icc
n_eff = len(j) / deff
z = 1.959963985 + 0.841621234          # alpha .05 two-sided, 80% power


def mde(n):
    return float(np.tanh(z / np.sqrt(max(n - 3, 1))))


print(f'  observations (ZIP-quarters)        {len(j):>8,}')
print(f'  independent places (ZIPs)          {len(k):>8,}')
print(f'  mean cells per ZIP                 {m_bar:>8.1f}')
print(f'  intraclass correlation of sentiment{icc:>8.3f}')
print(f'  design effect                      {deff:>8.1f}')
print(f'  EFFECTIVE sample size              {n_eff:>8.0f}')
print()
print(f'  minimum detectable r, naive  (n={len(j):,})      {mde(len(j)):.3f}')
print(f'  minimum detectable r, clustered (n_eff={n_eff:.0f})  {mde(n_eff):.3f}')
print(f'  observed within-ZIP r                        ~0.010')
print(f'  -> any true correlation below |{mde(n_eff):.2f}| is invisible to this design.')

print()
print('=' * 74)
print('B. IS THERE A DOSE WHERE SOMETHING APPEARS?')
print('=' * 74)
pl = panel(valid[valid.place])
pl = pl[pl.amount > 0].copy()
pl['decile'] = pd.qcut(pl.amount, 10, labels=False, duplicates='drop') + 1
# within-ZIP demeaned sentiment, so we compare a place against itself
pl['s_dm'] = pl.mean_compound - pl.groupby('zip5').mean_compound.transform('mean')
tab = pl.groupby('decile').agg(cells=('amount', 'size'),
                               median_usd=('amount', 'median'),
                               mean_sentiment=('mean_compound', 'mean'),
                               within_zip_sentiment=('s_dm', 'mean'))
tab['median_usd'] = tab.median_usd.round(0)
print('  place-based investment only, ZIP-quarters with positive obligations')
print(tab.round(4).to_string())
top, bot = pl[pl.decile == pl.decile.max()], pl[pl.decile == 1]
print(f'\n  top decile (median ${top.amount.median():,.0f}) vs bottom (median ${bot.amount.median():,.0f})')
print(f'    within-ZIP sentiment difference: {top.s_dm.mean() - bot.s_dm.mean():+.4f}')
print(f'    (scale: sentiment sd across ZIP-quarters = {j.mean_compound.std():.3f})')

print()
print('=' * 74)
print('C. IS THE CROSS-SECTIONAL SIGNAL JUST "BUSY PLACE"?')
print('=' * 74)
z_lvl = j.groupby('zip5').agg(x=('x', 'mean'),
                              sentiment=('mean_compound', 'mean'),
                              reviews=('n_reviews', 'sum'))
z_lvl['activity'] = np.log10(z_lvl.reviews)
r_raw = z_lvl[['x', 'sentiment']].corr().iloc[0, 1]


def partial(df, a, b, ctrl):
    resid = {}
    for v in (a, b):
        s = df[[v, ctrl]].dropna()
        beta = np.polyfit(s[ctrl], s[v], 1)
        resid[v] = df[v] - np.polyval(beta, df[ctrl])
    return float(np.corrcoef(resid[a], resid[b])[0, 1])


r_partial = partial(z_lvl, 'x', 'sentiment', 'activity')
print(f'  ZIPs                                           {len(z_lvl):>7,}')
print(f'  corr(funding, sentiment)                       {r_raw:>+7.4f}')
print(f'  corr(funding, review volume)                   {z_lvl[["x","activity"]].corr().iloc[0,1]:>+7.4f}')
print(f'  corr(review volume, sentiment)                 {z_lvl[["activity","sentiment"]].corr().iloc[0,1]:>+7.4f}')
print(f'  PARTIAL corr(funding, sentiment | volume)      {r_partial:>+7.4f}')
share = 0 if r_raw == 0 else (1 - r_partial / r_raw)
print(f'  -> {share:.0%} of the cross-sectional signal is explained by how busy the place is.')
