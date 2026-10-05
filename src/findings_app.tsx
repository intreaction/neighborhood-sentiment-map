import * as React from 'react';
import {createRoot} from 'react-dom/client';
import {Bar,BarChart,CartesianGrid,Cell,ReferenceLine,Scatter,ScatterChart,XAxis,YAxis,ZAxis} from 'recharts';
import {ChartContainer,ChartLegend,ChartLegendContent,ChartTooltip,ChartTooltipContent} from './components/ui/chart';
import {Card,CardContent,CardDescription,CardFooter,CardHeader,CardTitle} from './components/ui/card';
import {Table,TableBody,TableCell,TableHead,TableHeader,TableRow} from './components/ui/table';
import {Badge} from './components/ui/badge';
import {projectEffects} from './place_projection.mjs';

// Every figure here is computed from files the site already serves; nothing is hand-entered.
const NOTEBOOK='https://github.com/intreaction/neighborhood-sentiment-map/blob/main/output/jupyter-notebook/Project_Research_Walkthrough.ipynb';
const GREEN='#245c49',GREY='#889686',ORANGE='#b56b32',RED='#a63824';
const CITY_COLORS:Record<string,string>={Philadelphia:'#245c49',TampaBay:'#b56b32',Nashville:'#5992b5',NewOrleans:'#75578a',Tucson:'#c49a2c'};
const fmt=(v:number,d=0)=>Number.isFinite(v)?v.toLocaleString('en-US',{minimumFractionDigits:d,maximumFractionDigits:d}):'—';
const signed=(v:number,d=0)=>(v>0?'+':v<0?'−':'')+fmt(Math.abs(v),d);
const median=(xs:number[])=>{const v=xs.filter(Number.isFinite).sort((a,b)=>a-b),m=v.length>>1;return v.length%2?v[m]:(v[m-1]+v[m])/2;};
function spearman(x:number[],y:number[]){
  const rank=(v:number[])=>{const o=v.map((x,i)=>[x,i]).sort((a,b)=>a[0]-b[0]),r=new Array(v.length);o.forEach(([,i],k)=>{r[i]=k+1;});return r;};
  const rx=rank(x),ry=rank(y),n=x.length,mx=(n+1)/2;
  let num=0,dx=0,dy=0;for(let i=0;i<n;i++){num+=(rx[i]-mx)*(ry[i]-mx);dx+=(rx[i]-mx)**2;dy+=(ry[i]-mx)**2;}
  return num/Math.sqrt(dx*dy);
}
const head='h-9 bg-muted/70 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground';

function Finding({n,title,lede,source,children,meaning}:{n:number,title:string,lede:string,source:[string,string],children:React.ReactNode,meaning:React.ReactNode}) {
  return <Card className="gap-4 shadow-none" id={`finding-${n}`}>
    <CardHeader>
      <Badge variant="secondary" className="text-[10px] uppercase tracking-wider">Finding {n}</Badge>
      <CardTitle className="font-serif text-2xl leading-snug font-normal md:text-[28px]">{title}</CardTitle>
      <CardDescription className="text-sm leading-relaxed">{lede}</CardDescription>
    </CardHeader>
    <CardContent>{children}</CardContent>
    <CardFooter className="flex flex-col items-start gap-2 border-t pt-4 text-xs leading-relaxed text-muted-foreground">
      <p className="m-0"><strong className="text-foreground">What it means:</strong> {meaning}</p>
      <a className="font-semibold text-primary underline-offset-4 hover:underline" href={`${NOTEBOOK}#${source[1]}`}>Notebook {source[0]} →</a>
    </CardFooter>
  </Card>;
}

function Findings({areas,history,model,extra}:any) {
  const cities=areas.cities.map((c:any)=>({id:c.id,label:c.id.replace('TampaBay','Tampa Bay').replace('NewOrleans','New Orleans'),areas:c.areas}));
  const cityRows=cities.map((c:any)=>({city:c.label,zips:c.areas.length,early:c.areas.reduce((s:number,a:any)=>s+a.early.reviews,0),late:c.areas.reduce((s:number,a:any)=>s+a.late.reviews,0),
    growth:median(c.areas.map((a:any)=>a.growth_pct)),engagement:median(c.areas.map((a:any)=>a.annual_review_density)),sentiment:median(c.areas.map((a:any)=>a.late.sentiment))}));
  const zips=cities.flatMap((c:any)=>c.areas.filter((a:any)=>Number.isFinite(a.annual_review_density)&&Number.isFinite(a.late?.sentiment)).map((a:any)=>({city:c.id,label:c.label,zip:a.zip,x:Math.log10(a.annual_review_density),density:a.annual_review_density,y:a.late.sentiment,poverty:a.poverty_pct})));
  const rhoEngagement=spearman(zips.map((z:any)=>z.x),zips.map((z:any)=>z.y));
  const withPoverty=zips.filter((z:any)=>Number.isFinite(z.poverty));
  const rhoPoverty=spearman(withPoverty.map((z:any)=>z.poverty),withPoverty.map((z:any)=>z.y));
  const rows=projectEffects(history,model.excluded_projects.map((p:any)=>p.id));
  const growth=history.projects.filter((p:any)=>rows.some((r:any)=>r.id===p.id)).map((p:any)=>{
    const {near,far}=p.periods,r=rows.find((r:any)=>r.id===p.id)!;
    return {project:p.project,raw:100*(near.post.n_reviews/near.pre.n_reviews-1),comparison:100*(far.post.n_reviews/far.pre.n_reviews-1),adjusted:100*(Math.exp(r.effects.activity)-1),sentiment:r.effects.sentiment};
  }).sort((a:any,b:any)=>b.adjusted-a.adjusted);
  const sentimentUp=growth.filter((g:any)=>g.sentiment>0).length;
  const v=extra.text_validation,b=v.embedding_benchmark;
  const f1=[['Clause is about the area','area_target'],['Negative comment about the area','negative_area']].map(([label,k])=>({task:label,rules:b[k].rules.f1,bert:b[k].embedding_lr.f1}));
  f1.push({task:'Clause sentiment (macro-F1)',rules:b.polarity.vader.macro_f1,bert:b.polarity.embedding_lr.macro_f1});
  const mae=[{model:'Predict the average',all:model.mean_baseline.city_metrics.mae},{model:'Ridge baseline',all:model.candidates.baseline.city_metrics.mae},
    {model:'+ text shares',all:model.candidates.text.city_metrics.mae},{model:'+ pre-opening trend',all:model.candidates.trend.city_metrics.mae},{model:'+ TF-IDF/NMF topics',all:model.candidates.advanced_text.city_metrics.mae}];
  const timing=[{sample:`All ${model.mean_baseline.city_metrics.n} projects`,ridge:model.candidates.baseline.city_metrics.mae,mean:model.mean_baseline.city_metrics.mae},
    ...Object.values(model.sensitivities).map((s:any)=>({sample:`${s.n_projects} projects (${s.excluded.length} excluded)`,ridge:s.candidates.baseline.city_metrics.mae,mean:s.mean_baseline?.city_metrics?.mae??null}))];
  const rr=v.random_reviews;

  return <div className="grid gap-6">
    <Finding n={1} source={['§3','3.-Build-the-ZIP-dataset-from-existing-quarterly-analysis']} title="Yelp grew unevenly, so raw growth misleads"
      lede={`Across ${cityRows.reduce((n:number,c:any)=>n+c.zips,0)} mapped ZIPs, review counts between 2012–2014 and 2019–2021 grew far faster in some metros than others.`}
      meaning="Much of the growth in reviews is Yelp's own adoption, and it differs by metro. That is why every project comparison subtracts the change in a nearby comparison area.">
      <div className="overflow-x-auto rounded-lg border"><Table>
        <TableHeader><TableRow><TableHead className={head}>Metro</TableHead><TableHead className={head}>ZIPs</TableHead><TableHead className={head}>Reviews 2012–14</TableHead><TableHead className={head}>Reviews 2019–21</TableHead><TableHead className={head}>Median ZIP change</TableHead><TableHead className={head}>Median engagement</TableHead></TableRow></TableHeader>
        <TableBody>{cityRows.map((c:any)=><TableRow key={c.city}><TableCell className="font-medium">{c.city}</TableCell><TableCell className="tabular-nums">{c.zips}</TableCell><TableCell className="tabular-nums">{fmt(c.early)}</TableCell><TableCell className="tabular-nums">{fmt(c.late)}</TableCell><TableCell className="tabular-nums font-semibold">{signed(c.growth)}%</TableCell><TableCell className="tabular-nums">{fmt(c.engagement)} / km² / yr</TableCell></TableRow>)}</TableBody>
      </Table></div>
    </Finding>

    <Finding n={2} source={['§3','3.-Build-the-ZIP-dataset-from-existing-quarterly-analysis']} title="Busier areas get warmer reviews; poverty does not predict sentiment"
      lede={`Each dot is one of the ${zips.length} ZIPs with enough reviews for both measures. Business engagement and average sentiment rise together (Spearman ρ = ${fmt(rhoEngagement,2)}); poverty and sentiment are unrelated (ρ = ${fmt(rhoPoverty,2)}).`}
      meaning="Review sentiment mostly reflects the kind of places people review, and dense commercial areas review well. Low sentiment is not a stand-in for disadvantage, so the map shows poverty and review measures side by side rather than combining them.">
      <p className="chart-axis-label">Average review sentiment, 2019–2021 (VADER)</p>
      <ChartContainer config={Object.fromEntries(cities.map((c:any)=>[c.id,{label:c.label,color:CITY_COLORS[c.id]}]))} className="decision-chart" style={{height:340}} aria-label="ZIP engagement against sentiment">
        <ScatterChart margin={{top:10,right:20,left:0,bottom:10}}>
          <CartesianGrid/><XAxis type="number" dataKey="x" domain={['auto','auto']} tickFormatter={(t:number)=>fmt(10**t)} tickLine={false} axisLine={false}/>
          <YAxis type="number" dataKey="y" domain={['auto','auto']} tickFormatter={(t:number)=>fmt(t,2)} tickLine={false} axisLine={false} width={50}/><ZAxis range={[36,36]}/>
          <ChartTooltip content={<ChartTooltipContent hideLabel formatter={(_v:any,_n:any,item:any,i:number)=>i>0?null:<div><strong>ZIP {item.payload.zip}</strong> · {item.payload.label}<p>{fmt(item.payload.density)} reviews / km² / yr · sentiment {fmt(item.payload.y,3)}</p></div>}/>}/>
          <ChartLegend content={<ChartLegendContent/>}/>
          {cities.map((c:any)=><Scatter key={c.id} name={c.id} data={zips.filter((z:any)=>z.city===c.id)} fill={`var(--color-${c.id})`} fillOpacity={.75} isAnimationActive={false}/>)}
        </ScatterChart>
      </ChartContainer>
      <p className="chart-axis-label chart-x-label">Business engagement · reviews / km² / year (log scale)</p>
    </Finding>

    <Finding n={3} source={['§4','4.-Historical-project-dataset-and-outcome-construction']} title="Raw growth near a project and adjusted growth often disagree"
      lede="Review growth near each project from two years before opening to two years after, shown raw and after subtracting the comparison area's growth."
      meaning="Sun Link's nearby reviews nearly tripled, yet its comparison area grew faster, so the adjusted change is negative. Reading raw counts alone would credit projects with growth that was happening citywide.">
      <p className="chart-axis-label">Change in reviews · %</p>
      <ChartContainer config={{raw:{label:'Raw change near the project',color:GREY},adjusted:{label:'Adjusted for comparison area',color:GREEN}}} className="decision-chart" style={{height:380}} aria-label="Raw and adjusted review growth by project">
        <BarChart data={growth} layout="vertical" margin={{top:5,right:30,left:10,bottom:5}}>
          <CartesianGrid horizontal={false}/><XAxis type="number" tickFormatter={(t:number)=>signed(t)+'%'} tickLine={false} axisLine={false}/>
          <YAxis type="category" dataKey="project" width={160} tick={{fontSize:11}} tickLine={false} axisLine={false}/><ReferenceLine x={0} stroke="#a8baa3"/>
          <ChartTooltip content={<ChartTooltipContent formatter={(val:any,name:any,item:any)=><div className="chart-tooltip-row"><span style={{color:item.color}}>{name==='raw'?'Raw':'Adjusted'}</span><strong>{signed(val)}%</strong></div>}/>}/>
          <ChartLegend content={<ChartLegendContent/>}/>
          <Bar dataKey="raw" fill="var(--color-raw)" radius={3} maxBarSize={12} isAnimationActive={false}/>
          <Bar dataKey="adjusted" radius={3} maxBarSize={12} isAnimationActive={false}>{growth.map((g:any,i:number)=><Cell key={i} fill={g.adjusted<0?ORANGE:GREEN}/>)}</Bar>
        </BarChart>
      </ChartContainer>
    </Finding>

    <Finding n={4} source={['§5','5.-How-unstructured-text-contributes']} title={`Sentiment held up near ${sentimentUp} of ${growth.length} projects, by small amounts`}
      lede="Comparison-adjusted change in average review sentiment near each project (VADER compound, −1 to +1)."
      meaning="This answers the question in our proposal most directly: near most projects, reviews became slightly more positive relative to their surroundings. The changes are small (all under 0.1) and cannot be attributed to the projects alone.">
      <p className="chart-axis-label">Adjusted sentiment change</p>
      <ChartContainer config={{sentiment:{label:'Adjusted sentiment change',color:GREEN}}} className="decision-chart" style={{height:340}} aria-label="Adjusted sentiment change by project">
        <BarChart data={[...growth].sort((a:any,b:any)=>b.sentiment-a.sentiment)} layout="vertical" margin={{top:5,right:30,left:10,bottom:5}}>
          <CartesianGrid horizontal={false}/><XAxis type="number" tickFormatter={(t:number)=>signed(t,2)} tickLine={false} axisLine={false}/>
          <YAxis type="category" dataKey="project" width={160} tick={{fontSize:11}} tickLine={false} axisLine={false}/><ReferenceLine x={0} stroke="#a8baa3"/>
          <ChartTooltip content={<ChartTooltipContent hideLabel formatter={(val:any,_n:any,item:any)=><div><strong>{item.payload.project}</strong><p>{signed(val,3)}</p></div>}/>}/>
          <Bar dataKey="sentiment" radius={3} maxBarSize={18} isAnimationActive={false}>{[...growth].sort((a:any,b:any)=>b.sentiment-a.sentiment).map((g:any,i:number)=><Cell key={i} fill={g.sentiment<0?ORANGE:GREEN}/>)}</Bar>
        </BarChart>
      </ChartContainer>
    </Finding>

    <Finding n={5} source={['§5.4','5.4-BERT-sentence-embeddings-(Week-6)']} title="Most of Yelp is about food; place talk is a minority"
      lede={`Topics learned from all reviews describe food, hotels and coffee. Only ${rr.with_place_mention} of ${rr.n} randomly sampled reviews (${fmt(100*rr.place_rate_ci[0])}–${fmt(100*rr.place_rate_ci[1])}% at 95% confidence) mention the surroundings at all.`}
      meaning="Yelp is a business-review source, so civic signals have to be found inside it. When BERTopic is run on place-related excerpts instead, it recovers parking, safety, streetcars, construction and trash on its own.">
      <div className="overflow-x-auto rounded-lg border"><Table>
        <TableHeader><TableRow><TableHead className={head}>Learned topic (TF-IDF + NMF, all reviews)</TableHead><TableHead className={head}>Leading terms</TableHead></TableRow></TableHeader>
        <TableBody>{extra.topics.map((t:any)=><TableRow key={t.id}><TableCell className="font-medium">{t.id.replace('topic_','Topic ')}</TableCell><TableCell>{t.top_terms.slice(0,8).join(', ')}</TableCell></TableRow>)}</TableBody>
      </Table></div>
    </Finding>

    <Finding n={6} source={['§5.5','5.5-How-accurate-are-the-rules?-Validation-against-labelled-clauses']} title="Keyword rules miss most complaints; BERT embeddings do better"
      lede={`F1 against ${v.labels.n_items} labelled items (agent labels pending human recheck). The BERT model is logistic regression on all-MiniLM-L6-v2 embeddings, cross-validated with folds grouped by business.`}
      meaning="Our negative access and public-space measures come from the rules, which found about one in six negative area comments, so Place Lab marks them low reliability. Sentence embeddings roughly double the F1 for complaints; rescoring the full corpus with them is the next step.">
      <p className="chart-axis-label">F1 score (1 = perfect)</p>
      <ChartContainer config={{rules:{label:'Keyword rules / VADER',color:GREY},bert:{label:'BERT embeddings + logistic regression',color:GREEN}}} className="decision-chart" style={{height:260}} aria-label="Rules versus BERT F1">
        <BarChart data={f1} layout="vertical" margin={{top:5,right:30,left:10,bottom:5}}>
          <CartesianGrid horizontal={false}/><XAxis type="number" domain={[0,1]} tickFormatter={(t:number)=>fmt(t,1)} tickLine={false} axisLine={false}/>
          <YAxis type="category" dataKey="task" width={190} tick={{fontSize:11}} tickLine={false} axisLine={false}/>
          <ChartTooltip content={<ChartTooltipContent formatter={(val:any,name:any,item:any)=><div className="chart-tooltip-row"><span style={{color:item.color}}>{name==='rules'?'Rules / VADER':'BERT'}</span><strong>{fmt(val,2)}</strong></div>}/>}/>
          <ChartLegend content={<ChartLegendContent/>}/>
          <Bar dataKey="rules" fill="var(--color-rules)" radius={3} maxBarSize={16} isAnimationActive={false}/>
          <Bar dataKey="bert" fill="var(--color-bert)" radius={3} maxBarSize={16} isAnimationActive={false}/>
        </BarChart>
      </ChartContainer>
    </Finding>

    <Finding n={7} source={['§6','6.-Reproduce-the-baseline-and-inspect-alternatives']} title="Ten projects cannot forecast a new one"
      lede="Mean absolute error when each city's projects are held out (excess reviews per $1M; lower is better). Text features did not help, and the baseline's edge over simply predicting the average disappears once projects with 2020 or construction-overlap windows are removed."
      meaning="This is why Place Lab shows what happened and does not project outcomes for a new budget or location. The evidence supports investigation, not a recommendation.">
      <div className="grid gap-6 md:grid-cols-2">
        <div><p className="chart-axis-label">City-held-out error, all eligible projects</p>
          <ChartContainer config={{all:{label:'Mean absolute error',color:GREEN}}} className="decision-chart" style={{height:250}} aria-label="Model comparison">
            <BarChart data={mae} layout="vertical" margin={{top:5,right:30,left:10,bottom:5}}>
              <CartesianGrid horizontal={false}/><XAxis type="number" tickLine={false} axisLine={false}/><YAxis type="category" dataKey="model" width={130} tick={{fontSize:11}} tickLine={false} axisLine={false}/>
              <ChartTooltip content={<ChartTooltipContent hideLabel formatter={(val:any,_n:any,item:any)=><div><strong>{item.payload.model}</strong><p>{fmt(val,1)}</p></div>}/>}/>
              <Bar dataKey="all" radius={3} maxBarSize={18} isAnimationActive={false}>{mae.map((m:any,i:number)=><Cell key={i} fill={i===0?GREY:i===1?GREEN:'#9fb59f'}/>)}</Bar>
            </BarChart>
          </ChartContainer></div>
        <div className="overflow-x-auto self-start rounded-lg border"><Table>
          <TableHeader><TableRow><TableHead className={head}>Sample</TableHead><TableHead className={head}>Ridge</TableHead><TableHead className={head}>Average</TableHead></TableRow></TableHeader>
          <TableBody>{timing.map((t:any)=><TableRow key={t.sample}><TableCell>{t.sample}</TableCell><TableCell className={`tabular-nums font-semibold ${t.mean!=null&&t.ridge>t.mean?'text-[#a63824]':''}`}>{fmt(t.ridge,1)}</TableCell><TableCell className="tabular-nums">{t.mean==null?'—':fmt(t.mean,1)}</TableCell></TableRow>)}</TableBody>
        </Table></div>
      </div>
    </Finding>
  </div>;
}

async function init() {
  const load=(path:string)=>fetch(path).then(r=>{if(!r.ok)throw new Error('Missing '+path);return r.json();});
  const [areas,history,model,extra]=await Promise.all(['place-areas.json','place-history.json','place-model.json','findings-data.json'].map(load));
  createRoot(document.getElementById('findingsRoot')!).render(<Findings areas={areas} history={history} model={model} extra={extra}/>);
}
init().catch(error=>{document.getElementById('findingsRoot')!.textContent='Findings could not load: '+error.message;});
