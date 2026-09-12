// Pure transformations shared by the explorer and its numerical checks.
function fundingWindow(values, quarter, lag, width) {
  const end = quarter - lag, start = end - width + 1;
  if (start < 0 || end >= values.length || width < 1 || lag < 0) return null;
  const window = values.slice(start, end + 1);
  if (window.length !== width || window.some(v => v == null || !Number.isFinite(v))) return null;
  return window.reduce((a, b) => a + b, 0);
}
function reviewOutcome(values, quarter, mode) {
  if (values[quarter] == null) return null;
  if (mode === 'level') return values[quarter];
  return quarter >= 4 && values[quarter - 4] != null ? values[quarter] - values[quarter - 4] : null;
}
function signedLog(value) { return Math.sign(value) * Math.log1p(Math.abs(value)); }
function perResident(amount, population, minimum = 0) {
  return Number.isFinite(amount) && Number.isFinite(population) && population > 0 && population >= minimum
    ? amount / population : null;
}
function correlation(pairs) {
  if (pairs.length < 3) return null;
  const n = pairs.length, mx = pairs.reduce((s,p) => s+p[0],0)/n, my = pairs.reduce((s,p) => s+p[1],0)/n;
  let xx=0, yy=0, xy=0;
  for (const [x,y] of pairs) { xx+=(x-mx)**2; yy+=(y-my)**2; xy+=(x-mx)*(y-my); }
  return xx > 1e-15 && yy > 1e-15 ? Math.max(-1,Math.min(1,xy/Math.sqrt(xx*yy))) : null;
}
