"""Build the stacked-investment demo page.

A six-beat, click-through instrument for the question "do public investments stack
into a delayed effect on business sentiment?". The honest answer this data gives is
no detectable effect, so the page is built to demonstrate the search and the two
ways the search manufactures a false positive, rather than to announce a finding.

All numbers come from data/interim/lag_model.json, which build_lag_model.py
computes from the panel. Nothing here is hand-entered.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODEL = ROOT / "data" / "interim" / "lag_model.json"
OUT = ROOT / "web" / "lag.html"

BEATS = [
    {
        "title": "Two clocks",
        "says": "Two clocks. The dashed line is the metro average - sentiment fell across the "
                "decade in every one of the five metros and dropped off a cliff in 2020Q2. The "
                "wedges above are federal money arriving in lumps over the same years. Correlate "
                "those two without removing both trends and you are correlating the clocks, not "
                "the effect. The controls are off right now, and it reads +0.15.",
        "set": {"P": 4, "H": 8, "fe": "none", "pad": False, "focus": "series"},
    },
    {
        "title": "The hypothesis machine",
        "says": "This is what 'investments stack' means mechanically. Every dollar obligated in a "
                "quarter is weighted into a stock that peaks P quarters later and fades with "
                "half-life H. Peak 4, half-life 8 says construction shows up about a year after "
                "the award and fades over two. Drag the knobs: any shape here is a version of the "
                "hypothesis, and we test all forty-eight.",
        "set": {"P": 4, "H": 8, "fe": "both", "pad": False, "focus": "kernel"},
    },
    {
        "title": "Turn the controls off",
        "says": "With no controls this reads r = +0.15. That is a publishable-looking number and it "
                "is wrong. It is downtowns: the ZIPs that get money have more reviews and a "
                "different sentiment level. Add ZIP fixed effects and it falls to -0.01. Add "
                "quarter effects too and it is +0.004. The finding was the sample composition.",
        "set": {"P": 4, "H": 8, "fe": "none", "pad": False, "focus": "readout"},
    },
    {
        "title": "Walk the surface",
        "says": "Now try every kernel with the controls on. Not one cell leaves the noise band. The "
                "largest correlation anywhere is 0.011. Randomly hand each ZIP's award history to a "
                "different ZIP and you get a bigger best cell 94 times out of 100. There is no peak "
                "to find, and the interval tells you what this design could have seen: nothing "
                "below about 0.09.",
        "set": {"P": 8, "H": 2, "fe": "both", "pad": False, "focus": "surface"},
    },
    {
        "title": "The trap",
        "says": "For an afternoon this looked like a finding. The kernel reaches back 48 quarters "
                "but award data starts in 2010, so early stock was built on fabricated zeros - 22% "
                "real data in 2012Q1, 99.6% by 2021Q4. That ramp times each ZIP's total dollars "
                "manufactures a correlation. Renormalise by the history that actually exists and "
                "the corner collapses to -0.003.",
        "set": {"P": 10, "H": 16, "fe": "both", "pad": True, "focus": "surface"},
    },
    {
        "title": "Same money, opposite stories",
        "says": "North Philadelphia took $1.5B of housing-authority money across 37 quarters and "
                "closed its gap to the metro. Gentilly took $424M of the same programme family "
                "across 48 quarters and its gap widened. Across the twenty ZIPs that received over "
                "$100M, the gap moved the right way in exactly ten. That coin flip is why the panel "
                "averages to zero.",
        "set": {"P": 4, "H": 8, "fe": "both", "pad": False, "focus": "cases"},
    },
]

CASE_META = {
    "19121": ("North Philadelphia", "converged", "PHA capital + Choice Neighborhoods"),
    "37201": ("Downtown Nashville", "resilient", "CDBG entitlement, same grant yearly"),
    "33755": ("Downtown Clearwater", "resilient", "small steady place-based awards"),
    "70122": ("Gentilly", "diverged", "sustained HUD public housing"),
    "33607": ("West Tampa", "diverged", "public housing capital + operating"),
    "37206": ("East Nashville", "flat", "housing money in a gentrifying ZIP"),
    "19107": ("Center City", "flat", "mostly SEPTA/Amtrak transit formula"),
}


def main():
    model = json.loads(MODEL.read_text())
    for c in model["cases"]:
        nm, direction, note = CASE_META.get(c["zip"], (c["zip"], "", ""))
        c["name"] = nm
        c["direction"] = direction
        c["note"] = note
    payload = {**model, "beats": BEATS}
    html = TEMPLATE.replace("__M__", json.dumps(payload, separators=(",", ":")))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html)
    print(f"{len(model['surface'])} surface cells, {len(model['cases'])} cases, "
          f"{len(BEATS)} beats")
    print(f"wrote {OUT} ({OUT.stat().st_size/1e3:.0f} KB)")


TEMPLATE = r"""<title>Does Investment Stack?</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root{
  color-scheme:light;
  --bg:#f4f4f4; --layer:#ffffff; --layer-2:#f4f4f4; --hover:#e8e8e8;
  --line:#e0e0e0; --line-2:#8d8d8d;
  --text:#161616; --text-2:#525252; --text-3:#6f6f6f;
  --link:#0f62fe; --focus:#0f62fe;
  --pos:#0f62fe; --neg:#da1e28; --noise:#e0e0e0; --band:#c6c6c6;
  --stock:#0f62fe; --sentl:#8a3ffc; --metrol:#a8a8a8; --award:#009d9a;
  --warn:#ff832b; --warnbg:#fff2e8;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  color-scheme:dark;
  --bg:#161616; --layer:#262626; --layer-2:#161616; --hover:#333333;
  --line:#393939; --line-2:#6f6f6f;
  --text:#f4f4f4; --text-2:#c6c6c6; --text-3:#8d8d8d;
  --link:#4589ff; --focus:#4589ff;
  --pos:#4589ff; --neg:#fa4d56; --noise:#393939; --band:#525252;
  --stock:#4589ff; --sentl:#be95ff; --metrol:#6f6f6f; --award:#08bdba;
  --warn:#ff832b; --warnbg:#3a1f0b;
}}
:root[data-theme="dark"]{
  color-scheme:dark;
  --bg:#161616; --layer:#262626; --layer-2:#161616; --hover:#333333;
  --line:#393939; --line-2:#6f6f6f;
  --text:#f4f4f4; --text-2:#c6c6c6; --text-3:#8d8d8d;
  --link:#4589ff; --focus:#4589ff;
  --pos:#4589ff; --neg:#fa4d56; --noise:#393939; --band:#525252;
  --stock:#4589ff; --sentl:#be95ff; --metrol:#6f6f6f; --award:#08bdba;
  --warn:#ff832b; --warnbg:#3a1f0b;
}
*{box-sizing:border-box}
html,body{margin:0;height:100%}
body{background:var(--bg);color:var(--text);overflow:hidden;display:flex;
  flex-direction:column;font:400 14px/1.43 "IBM Plex Sans",Arial,sans-serif;
  -webkit-font-smoothing:antialiased}
.mono{font-family:"IBM Plex Mono",monospace;font-variant-numeric:tabular-nums}

.shell{flex:none;display:flex;align-items:stretch;min-height:46px;background:var(--layer);
  border-bottom:1px solid var(--line)}
.shell .b{display:flex;align-items:center;gap:10px;padding:0 16px;border-right:1px solid var(--line)}
.shell .b b{font-weight:600}
.shell .b span{color:var(--text-3);font-size:12px;letter-spacing:.32px}
.shell .q{display:flex;align-items:center;padding:0 16px;color:var(--text-2);font-size:13px}
.shell .sp{flex:1}
.shell .st{display:flex;align-items:center;gap:6px;padding:0 14px;border-left:1px solid var(--line);
  font-family:"IBM Plex Mono",monospace;font-size:11px;color:var(--text-3)}
.shell .st b{color:var(--text-2);font-weight:500}
@media (max-width:1180px){.shell .q,.shell .st{display:none}}

main{flex:1;min-height:0;display:grid;gap:12px;padding:12px;
  grid-template-columns:206px minmax(0,1fr) 336px}
@media (max-width:1280px){main{grid-template-columns:190px minmax(0,1fr) 300px}}
@media (max-width:1040px){main{grid-template-columns:190px minmax(0,1fr)}.right{display:none}}
.col{min-width:0;min-height:0;display:flex;flex-direction:column;gap:12px}
.col:first-child > .panel{overflow-y:auto;scrollbar-width:thin}
.panel{background:var(--layer);border:1px solid var(--line);min-height:0}
.panel.lit{border-color:var(--link);box-shadow:0 0 0 1px var(--link)}
.grp{padding:9px 12px;border-bottom:1px solid var(--line)}
.grp:last-child{border-bottom:0}
h2{margin:0 0 7px;font-size:11px;letter-spacing:.32px;color:var(--text-3);
  font-weight:600;text-transform:uppercase}
.kv{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:5px}
.kv b{font-family:"IBM Plex Mono",monospace;font-size:15px;font-weight:500}
input[type=range]{width:100%;accent-color:var(--link);margin:0}
.seg{display:flex;flex-direction:column;border:1px solid var(--line-2)}
.seg button{appearance:none;border:0;border-bottom:1px solid var(--line-2);background:var(--layer);
  color:var(--text-2);font:400 12px/16px "IBM Plex Sans",sans-serif;padding:6px 9px;
  text-align:left;cursor:pointer}
.seg button:last-child{border-bottom:0}
.seg button[aria-pressed="true"]{background:var(--link);color:#fff}
.seg button:focus-visible{outline:2px solid var(--focus);outline-offset:-2px}
.chk{display:flex;align-items:flex-start;gap:8px;font-size:12px;cursor:pointer;line-height:16px}
.chk input{accent-color:var(--warn);margin:1px 0 0}
.cases{display:flex;flex-direction:column}
.cases button{appearance:none;border:0;border-bottom:1px solid var(--line);background:var(--layer);
  text-align:left;padding:5px 4px;cursor:pointer;color:var(--text);font:400 12px/15px "IBM Plex Sans",sans-serif}
.cases button:last-child{border-bottom:0}
.cases button:hover{background:var(--hover)}
.cases button[aria-pressed="true"]{background:var(--hover);box-shadow:inset 2px 0 0 var(--link)}
.cases .z{font-family:"IBM Plex Mono",monospace;font-size:11px;color:var(--text-3)}
.cases .d{font-size:10px;letter-spacing:.3px;text-transform:uppercase}
.d.converged{color:var(--pos)} .d.diverged{color:var(--neg)}
.d.resilient{color:var(--text-2)} .d.flat{color:var(--text-3)}
.help{margin:6px 0 0;font-size:10px;line-height:14px;color:var(--text-3)}

.card{padding:11px 13px 8px;display:flex;flex-direction:column;min-height:0}
.card h3{margin:0;font-size:13px;font-weight:600}
.card p.sub{margin:2px 0 6px;font-size:11px;line-height:15px;color:var(--text-3)}
.plotbox{flex:1;min-height:0}
svg.plot{display:block;width:100%;height:100%}
.gl{stroke:var(--line);stroke-width:1}
.ax{fill:var(--text-3);font-size:9px;font-family:"IBM Plex Mono",monospace}
.lg{fill:var(--text-2);font-size:10px;font-family:"IBM Plex Sans",sans-serif;font-weight:600}

.read{display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--line)}
.read div{background:var(--layer);padding:8px 10px}
.read .lab{font-size:10px;letter-spacing:.32px;color:var(--text-3);text-transform:uppercase}
.read .val{font-family:"IBM Plex Mono",monospace;font-size:19px;font-weight:500;margin-top:2px}
.read .sm{font-size:10px;color:var(--text-3);margin-top:1px}
.verdict{padding:8px 12px;font-size:11px;line-height:15px;border-top:1px solid var(--line)}
.verdict.null{color:var(--text-2)}
.verdict.trap{background:var(--warnbg);color:var(--text);border-left:3px solid var(--warn)}

.beat{flex:none;display:flex;align-items:stretch;gap:0;background:var(--layer);
  border-top:1px solid var(--line)}
.beat .nav{display:flex;align-items:center;gap:0;border-right:1px solid var(--line)}
.beat .nav button{appearance:none;width:40px;height:100%;border:0;border-right:1px solid var(--line);
  background:var(--layer);color:var(--text);cursor:pointer;font-size:13px}
.beat .nav button:last-child{border-right:0}
.beat .nav button:hover:not(:disabled){background:var(--hover)}
.beat .nav button:disabled{color:var(--text-3);cursor:default}
.beat .nav button:focus-visible{outline:2px solid var(--focus);outline-offset:-2px}
.beat .body{flex:1;padding:9px 14px;min-width:0}
.beat .t{font-size:11px;letter-spacing:.32px;text-transform:uppercase;color:var(--link);
  font-weight:600}
.beat .s{margin-top:2px;font-size:13px;line-height:18px;color:var(--text-2);max-width:118ch}
.beat .ct{display:flex;align-items:center;padding:0 14px;border-left:1px solid var(--line);
  font-family:"IBM Plex Mono",monospace;font-size:11px;color:var(--text-3)}
.tip{position:fixed;pointer-events:none;z-index:70;background:var(--layer);
  border:1px solid var(--line-2);padding:6px 9px;font-size:11px;opacity:0;
  box-shadow:0 2px 6px rgba(0,0,0,.2)}
.tip.on{opacity:1}
.tip b{font-family:"IBM Plex Mono",monospace}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
</style>

<div class="shell">
  <div class="b"><b>Does Investment Stack?</b><span>CIS 509 &middot; Team 4</span></div>
  <div class="q">Do public investments accumulate into a delayed effect on business review sentiment?</div>
  <div class="sp"></div>
  <div class="st">ZIPs <b id="sZ">&mdash;</b></div>
  <div class="st">ZIP-quarters <b id="sC">&mdash;</b></div>
  <div class="st">2012Q1&ndash;2021Q4</div>
</div>

<main>
  <div class="col">
    <div class="panel" id="pCtl">
      <div class="grp">
        <h2>Kernel</h2>
        <div class="kv"><span>Peak lag</span><b id="vP">&mdash;</b></div>
        <input type="range" id="sP" min="0" max="7" step="1" aria-label="Peak lag">
        <div class="kv" style="margin-top:9px"><span>Half-life</span><b id="vH">&mdash;</b></div>
        <input type="range" id="sH" min="0" max="5" step="1" aria-label="Half-life">
        <p class="help">Quarters. Peak is when a dollar's weight is largest; half-life is how long
        after the peak its weight halves.</p>
      </div>
      <div class="grp">
        <h2>Controls</h2>
        <div class="seg" id="fe">
          <button data-fe="none">No fixed effects</button>
          <button data-fe="zip">ZIP only</button>
          <button data-fe="quarter">Quarter only</button>
          <button data-fe="both" aria-pressed="true">ZIP + quarter</button>
        </div>
        <p class="help">Fixed effects remove fixed differences between ZIPs and shocks common to
        every ZIP in a quarter.</p>
      </div>
      <div class="grp">
        <h2>Known artifact</h2>
        <label class="chk"><input type="checkbox" id="pad">
          <span>Pad missing pre-2010 history with zeros</span></label>
        <p class="help">Leave off. On, the kernel is fed fabricated zeros for years the award data
        does not cover &mdash; the exact bug that produced our one apparent finding.</p>
      </div>
      <div class="grp">
        <h2>Case ZIP</h2>
        <div class="cases" id="cases"></div>
      </div>
    </div>
  </div>

  <div class="col">
    <div class="panel card" id="pKernel" style="flex:0 0 122px">
      <h3>Kernel shape</h3>
      <p class="sub">Weight given to a dollar obligated k quarters ago.</p>
      <div class="plotbox"><svg class="plot" id="cK" role="img"
        aria-label="Kernel weight by lag"></svg></div>
    </div>
    <div class="panel card" id="pSeries" style="flex:1">
      <h3 id="stkTitle">Awards stacking into an investment stock</h3>
      <p class="sub">Each award contributes a decaying wedge; together they make the stock line.
      Sentiment for the same ZIP is plotted beneath, on its own scale.</p>
      <div class="plotbox"><svg class="plot" id="cS" role="img"
        aria-label="Stacked investment contributions and sentiment"></svg></div>
    </div>
  </div>

  <div class="col right">
    <div class="panel" id="pRead">
      <div class="read">
        <div><div class="lab">Correlation</div><div class="val" id="rVal">&mdash;</div>
             <div class="sm" id="rSub">&mdash;</div></div>
        <div><div class="lab">Permutation p</div><div class="val" id="pVal">&mdash;</div>
             <div class="sm">shuffled award histories</div></div>
      </div>
      <div class="verdict" id="verdict"></div>
    </div>
    <div class="panel card" id="pSurf" style="flex:1">
      <h3>All 48 hypotheses</h3>
      <p class="sub">Every peak lag &times; half-life pair. Grey is inside the noise band from
      shuffling; nothing here leaves it.</p>
      <div class="plotbox"><svg class="plot" id="cG" role="img"
        aria-label="Correlation surface over peak lag and half-life"></svg></div>
    </div>
  </div>
</main>

<div class="beat">
  <div class="nav">
    <button id="bPrev" aria-label="Previous beat">&#9664;</button>
    <button id="bNext" aria-label="Next beat">&#9654;</button>
  </div>
  <div class="body"><div class="t" id="bT">&mdash;</div><div class="s" id="bS">&mdash;</div></div>
  <div class="ct" id="bC">&mdash;</div>
</div>
<div class="tip" id="tip"></div>

<script>
const M=__M__;
const AQ=M.awardQuarters, SQ=M.sentQuarters, PEAKS=M.peaks, HALVES=M.halves;
const css=n=>getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const el=(t,a)=>{const e=document.createElementNS("http://www.w3.org/2000/svg",t);
  for(const k in a)e.setAttribute(k,a[k]);return e;};
const usd=v=>v>=1e9?"$"+(v/1e9).toFixed(2)+"B":v>=1e6?"$"+(v/1e6).toFixed(0)+"M"
  :v>=1e3?"$"+(v/1e3).toFixed(0)+"K":"$"+Math.round(v);

let P=M.default.P, H=M.default.H, fe="both", pad=false, caseIdx=0, beat=0;

/* kernel: same formula as build_lag_model.py */
function kernel(P,H,n=AQ.length){
  let w;
  if(P<=0){ w=Array.from({length:n},(_,k)=>Math.exp(-k*Math.LN2/H)); }
  else{
    const b=(P*Math.log((P+H)/P)-H)/Math.log(0.5), a=P/b;
    w=[0]; for(let k=1;k<n;k++) w.push(Math.exp(a*Math.log(k)-k/b));
  }
  const s=w.reduce((x,y)=>x+y,0);
  return s? w.map(x=>x/s) : w;
}
const cell=()=>M.surface.find(c=>c.P===P&&c.H===H)||M.surface[0];
function rNow(){
  const c=cell();
  if(pad) return c.r_padded;
  return fe==="both"?c.r:fe==="none"?c.r_none:fe==="zip"?c.r_zip:c.r_quarter;
}

/* ---------------- kernel chart ---------------- */
function drawKernel(){
  const s=document.getElementById("cK"), box=s.parentElement;
  const W=Math.max(240,box.clientWidth), Hh=Math.max(60,box.clientHeight);
  s.setAttribute("viewBox",`0 0 ${W} ${Hh}`); s.textContent="";
  const m={t:6,r:8,b:14,l:26}, w=kernel(P,H), N=28;
  const mx=Math.max(...w.slice(0,N));
  const px=k=>m.l+(W-m.l-m.r)*k/(N-1), py=v=>m.t+(Hh-m.t-m.b)*(1-v/(mx||1));
  s.append(el("line",{x1:m.l,x2:W-m.r,y1:Hh-m.b,y2:Hh-m.b,class:"gl"}));
  let d=`M${m.l} ${Hh-m.b} `;
  for(let k=0;k<N;k++) d+=`L${px(k).toFixed(1)} ${py(w[k]).toFixed(1)} `;
  d+=`L${px(N-1).toFixed(1)} ${Hh-m.b} Z`;
  s.append(el("path",{d,fill:css("--stock"),"fill-opacity":.22,
    stroke:css("--stock"),"stroke-width":1.6}));
  // mark the peak
  let pk=0; for(let k=0;k<N;k++) if(w[k]>w[pk]) pk=k;
  s.append(el("line",{x1:px(pk),x2:px(pk),y1:m.t,y2:Hh-m.b,
    stroke:css("--link"),"stroke-width":1,"stroke-dasharray":"2 2"}));
  const lp=el("text",{x:px(pk)+3,y:m.t+9,class:"lg",fill:css("--link")});
  lp.textContent=`peak ${pk}q`; s.append(lp);
  [0,7,14,21,27].forEach(k=>{const t=el("text",{x:px(k),y:Hh-3,class:"ax",
    "text-anchor":k===0?"start":k===27?"end":"middle"});t.textContent=k+"q";s.append(t);});
}

/* ---------------- stacking chart ---------------- */
function drawStack(){
  const s=document.getElementById("cS"), box=s.parentElement;
  const W=Math.max(320,box.clientWidth), Hh=Math.max(180,box.clientHeight);
  s.setAttribute("viewBox",`0 0 ${W} ${Hh}`); s.textContent="";
  const c=M.cases[caseIdx]; if(!c) return;
  const m={t:10,r:10,b:16,l:40};
  const split=Math.round((Hh-m.t-m.b)*0.62);
  const topH=split, botY=m.t+split+10, botH=(Hh-m.b)-botY;
  const n=AQ.length, px=i=>m.l+(W-m.l-m.r)*i/(n-1);
  const w=kernel(P,H);

  // contribution of each award quarter to every later quarter
  const contrib=[], stock=new Array(n).fill(0);
  for(let j=0;j<n;j++){
    if(!c.awards[j]) continue;
    const v=Math.log1p(c.awards[j]);
    const row=new Array(n).fill(0);
    for(let t=j;t<n;t++){
      let den=0; for(let k=0;k<=t;k++) den+=w[k];
      row[t]= pad ? w[t-j]*v : (den>0? w[t-j]*v/den : 0);
    }
    contrib.push({j,row,amt:c.awards[j]});
  }
  for(const cc of contrib) for(let t=0;t<n;t++) stock[t]+=cc.row[t];
  const smax=Math.max(1e-9,...stock);
  const sy=v=>m.t+topH*(1-v/smax);

  // stacked wedges
  const base=new Array(n).fill(0);
  contrib.forEach((cc,ix)=>{
    let d=""; const pts=[];
    for(let t=0;t<n;t++){ pts.push([px(t),sy(base[t]+cc.row[t])]); }
    d="M"+pts.map(p=>p[0].toFixed(1)+" "+p[1].toFixed(1)).join("L");
    for(let t=n-1;t>=0;t--) d+="L"+px(t).toFixed(1)+" "+sy(base[t]).toFixed(1);
    d+="Z";
    s.append(el("path",{d,fill:css("--award"),
      "fill-opacity":String(0.10+0.06*(ix%4)),stroke:"none"}));
    for(let t=0;t<n;t++) base[t]+=cc.row[t];
  });
  // stock outline
  let sd=""; for(let t=0;t<n;t++) sd+=(t?"L":"M")+px(t).toFixed(1)+" "+sy(stock[t]).toFixed(1);
  s.append(el("path",{d:sd,fill:"none",stroke:css("--stock"),"stroke-width":2}));
  const lt=el("text",{x:m.l+3,y:m.t+10,class:"lg",fill:css("--stock")});
  lt.textContent="investment stock"; s.append(lt);

  // sentiment panel
  const vals=c.sent.filter(v=>v!=null), mv=c.metroSent.filter(v=>v!=null);
  if(vals.length){
    const lo=Math.min(...vals,...mv), hi=Math.max(...vals,...mv), pd=(hi-lo)*0.15||0.02;
    const y0=lo-pd,y1=hi+pd, qy=v=>botY+botH*(1-(v-y0)/(y1-y0));
    const qx=i=>px(i+(AQ.length-SQ.length));
    s.append(el("line",{x1:m.l,x2:W-m.r,y1:botY,y2:botY,class:"gl"}));
    [y0,(y0+y1)/2,y1].forEach(v=>{const t=el("text",{x:m.l-5,y:qy(v)+3,class:"ax",
      "text-anchor":"end"});t.textContent=v.toFixed(2);s.append(t);});
    const line=(arr,col,wid,dash)=>{
      let d="",go=false;
      arr.forEach((v,i)=>{if(v==null){go=false;return;}
        d+=(go?"L":"M")+qx(i).toFixed(1)+" "+qy(v).toFixed(1)+" ";go=true;});
      if(d) s.append(el("path",Object.assign({d,fill:"none",stroke:col,"stroke-width":wid},
        dash?{"stroke-dasharray":dash}:{})));
    };
    line(c.metroSent,css("--metrol"),1.4,"3 3");
    line(c.sent,css("--sentl"),2);
    const l1=el("text",{x:m.l+3,y:botY+12,class:"lg",fill:css("--sentl")});
    l1.textContent=`${c.name} sentiment`; s.append(l1);
    const l2=el("text",{x:m.l+3,y:botY+24,class:"lg",fill:css("--metrol")});
    l2.textContent="metro average"; s.append(l2);
  }
  [0,Math.floor(n/2),n-1].forEach(i=>{const t=el("text",{x:px(i),y:Hh-4,class:"ax",
    "text-anchor":i===0?"start":i===n-1?"end":"middle"});t.textContent=AQ[i];s.append(t);});
  document.getElementById("stkTitle").textContent=
    `${c.name} (${c.zip}) \u2014 ${usd(c.total)} across ${c.quarters_funded} quarters`;
}

/* ---------------- surface heatmap ---------------- */
function drawSurface(){
  const s=document.getElementById("cG"), box=s.parentElement;
  const W=Math.max(240,box.clientWidth), Hh=Math.max(150,box.clientHeight);
  s.setAttribute("viewBox",`0 0 ${W} ${Hh}`); s.textContent="";
  const m={t:12,r:8,b:26,l:30};
  const cw=(W-m.l-m.r)/PEAKS.length, ch=(Hh-m.t-m.b)/HALVES.length;
  const band=M.perm.null_max_median;
  const key=pad?"r_padded":(fe==="both"?"r":fe==="none"?"r_none":fe==="zip"?"r_zip":"r_quarter");
  const vals=M.surface.map(c=>Math.abs(c[key]));
  const scale=Math.max(band,...vals);
  PEAKS.forEach((p,i)=>HALVES.forEach((h,j)=>{
    const c=M.surface.find(x=>x.P===p&&x.H===h); if(!c) return;
    const v=c[key], a=Math.min(1,Math.abs(v)/scale);
    const inNoise=Math.abs(v)<band;
    const fill=inNoise?css("--noise"):(v>0?css("--pos"):css("--neg"));
    const r=el("rect",{x:m.l+i*cw+1,y:m.t+j*ch+1,width:cw-2,height:ch-2,
      fill,"fill-opacity":inNoise?0.55:String(0.30+0.70*a),cursor:"pointer"});
    r.addEventListener("mousemove",e=>{
      const t=document.getElementById("tip");
      t.innerHTML=`peak ${p}q &middot; half-life ${h}q<br>r = <b>${v>=0?"+":""}${v.toFixed(4)}</b>`+
        (inNoise?"<br>inside the noise band":"");
      t.classList.add("on");
      t.style.left=Math.min(e.clientX+13,innerWidth-190)+"px";
      t.style.top=Math.min(e.clientY+13,innerHeight-70)+"px";});
    r.addEventListener("mouseleave",()=>document.getElementById("tip").classList.remove("on"));
    r.addEventListener("click",()=>{P=p;H=h;syncInputs();render();});
    s.append(r);
    if(p===P&&h===H) s.append(el("rect",{x:m.l+i*cw+1,y:m.t+j*ch+1,width:cw-2,height:ch-2,
      fill:"none",stroke:css("--text"),"stroke-width":2}));
  }));
  PEAKS.forEach((p,i)=>{const t=el("text",{x:m.l+i*cw+cw/2,y:Hh-14,class:"ax",
    "text-anchor":"middle"});t.textContent=p;s.append(t);});
  HALVES.forEach((h,j)=>{const t=el("text",{x:m.l-5,y:m.t+j*ch+ch/2+3,class:"ax",
    "text-anchor":"end"});t.textContent=h;s.append(t);});
  const xl=el("text",{x:(m.l+W-m.r)/2,y:Hh-3,class:"ax","text-anchor":"middle"});
  xl.textContent="peak lag (quarters)"; s.append(xl);
  const yc=((m.t+Hh-m.b)/2).toFixed(1);
  const yl=el("text",{x:10,y:yc,class:"ax","text-anchor":"middle",
    transform:`rotate(-90 10 ${yc})`});
  yl.textContent="half-life (quarters)"; s.append(yl);
}

/* ---------------- readout ---------------- */
function drawRead(){
  const r=rNow(), band=M.perm.null_max_median;
  const rv=document.getElementById("rVal");
  rv.textContent=(r>=0?"+":"")+r.toFixed(4);
  const suspicious=(fe!=="both")||pad;
  rv.style.color= suspicious?css("--warn"):(Math.abs(r)<band?css("--text-3"):css("--text"));
  document.getElementById("rSub").textContent=
    `${cell().n.toLocaleString()} ZIP-quarters, ${M.nZips} ZIPs`;
  document.getElementById("pVal").textContent =
    (fe==="both"&&!pad) ? M.perm.p_family.toFixed(2) : "n/a";
  const v=document.getElementById("verdict");
  if(pad){
    v.className="verdict trap";
    v.innerHTML=`<b>Artifact.</b> The kernel is being fed fabricated zeros for pre-2010 quarters,
      so the stock ramps with time in proportion to each ZIP's total dollars. A predictor with no
      timing information scores higher than this. Corrected, this cell reads
      ${(cell().r>=0?"+":"")+cell().r.toFixed(4)}.`;
  }else if(fe!=="both"){
    v.className="verdict trap";
    v.innerHTML=`<b>Confounded.</b> ${fe==="none"?"With no controls this is the cross-sectional density confound: funded ZIPs are downtowns with more reviews and different sentiment levels.":fe==="zip"?"ZIP effects removed, but the shared 2012&ndash;2021 decline and the 2020 COVID cliff are still in both series.":"Quarter effects removed, but fixed differences between neighbourhoods remain."}
      With both sets of effects this cell reads ${(cell().r>=0?"+":"")+cell().r.toFixed(4)}.`;
  }else{
    v.className="verdict null";
    v.innerHTML=`Inside the noise band (shuffled-history max |r| median ${band.toFixed(3)}).
      Family-wise p = ${M.perm.p_family}; ZIP-clustered 95% CI at the default kernel
      ${M.clusteredCI[0].toFixed(3)} to ${M.clusteredCI[1].toFixed(3)}. This design cannot see
      anything below about |r| = ${M.minDetectable}.`;
  }
}

/* ---------------- beats ---------------- */
function applyBeat(i){
  beat=(i+M.beats.length)%M.beats.length;
  const b=M.beats[beat];
  P=b.set.P; H=b.set.H; fe=b.set.fe; pad=b.set.pad;
  document.getElementById("bT").textContent=`${beat+1}. ${b.title}`;
  document.getElementById("bS").textContent=b.says;
  document.getElementById("bC").textContent=`${beat+1} / ${M.beats.length}`;
  document.getElementById("bPrev").disabled = beat===0;
  document.getElementById("bNext").disabled = beat===M.beats.length-1;
  for(const [id,f] of [["pSeries","series"],["pKernel","kernel"],
                       ["pRead","readout"],["pSurf","surface"],["pCtl","cases"]])
    document.getElementById(id).classList.toggle("lit", b.set.focus===f);
  // the case beat is about the ZIP list, so bring it into view rather than
  // leaving the presenter to hunt for it below the fold
  if(b.set.focus==="cases")
    document.getElementById("cases").scrollIntoView({block:"nearest"});
  else
    document.getElementById("pCtl").scrollTop=0;
  syncInputs(); render();
}
function syncInputs(){
  document.getElementById("sP").value=PEAKS.indexOf(P);
  document.getElementById("sH").value=HALVES.indexOf(H);
  document.getElementById("vP").textContent=P+"q";
  document.getElementById("vH").textContent=H+"q";
  document.getElementById("pad").checked=pad;
  document.querySelectorAll("#fe button").forEach(b=>
    b.setAttribute("aria-pressed",String(b.dataset.fe===fe)));
}
function render(){drawKernel();drawStack();drawSurface();drawRead();}

/* ---------------- wiring ---------------- */
document.getElementById("sP").max=PEAKS.length-1;
document.getElementById("sH").max=HALVES.length-1;
document.getElementById("sP").addEventListener("input",e=>{P=PEAKS[+e.target.value];syncInputs();render();});
document.getElementById("sH").addEventListener("input",e=>{H=HALVES[+e.target.value];syncInputs();render();});
document.getElementById("fe").addEventListener("click",e=>{
  const b=e.target.closest("button[data-fe]"); if(!b)return;
  fe=b.dataset.fe; syncInputs(); render();});
document.getElementById("pad").addEventListener("change",e=>{pad=e.target.checked;render();});
document.getElementById("bPrev").addEventListener("click",()=>applyBeat(beat-1));
document.getElementById("bNext").addEventListener("click",()=>applyBeat(beat+1));
addEventListener("keydown",e=>{
  if(e.target.tagName==="INPUT")return;
  if(e.key==="ArrowRight"){applyBeat(beat+1);e.preventDefault();}
  if(e.key==="ArrowLeft"){applyBeat(beat-1);e.preventDefault();}});
const cb=document.getElementById("cases");
cb.innerHTML=M.cases.map((c,i)=>`<button data-i="${i}" ${i===0?'aria-pressed="true"':''}>
  <span class="z">${c.zip}</span> ${c.name}<br>
  <span class="d ${c.direction}">${c.direction}</span></button>`).join("");
cb.addEventListener("click",e=>{const b=e.target.closest("button"); if(!b)return;
  caseIdx=+b.dataset.i;
  cb.querySelectorAll("button").forEach(x=>x.setAttribute("aria-pressed",String(x===b)));
  drawStack();});
document.getElementById("sZ").textContent=M.nZips;
document.getElementById("sC").textContent=M.nCells.toLocaleString();
addEventListener("resize",render);
matchMedia("(prefers-color-scheme:dark)").addEventListener("change",render);
applyBeat(0);
</script>
"""


if __name__ == "__main__":
    main()
