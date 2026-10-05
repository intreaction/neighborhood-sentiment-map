import * as React from 'react';
import {Bar,BarChart,CartesianGrid,Cell,ReferenceLine,XAxis,YAxis} from 'recharts';
import {ChevronDown} from 'lucide-react';
import insights from './place_insights.cjs';
import {ChartContainer,ChartLegend,ChartLegendContent,ChartTooltip,ChartTooltipContent} from './components/ui/chart';
import {Tabs,TabsContent,TabsList,TabsTrigger} from './components/ui/tabs';
import {ToggleGroup,ToggleGroupItem} from './components/ui/toggle-group';
import {Collapsible,CollapsibleContent,CollapsibleTrigger} from './components/ui/collapsible';
import {Table,TableBody,TableCell,TableHead,TableHeader,TableRow} from './components/ui/table';
import {Button} from './components/ui/button';

const NEAR='#245c49',FAR='#889686',UP='#245c49',DOWN='#b56b32';
const PERIODS:[string,string][]=[['early','Early'],['pre','Pre-opening'],['post','Post-opening']];
// One chart per projection measure; shares are stored as fractions and shown as percentages.
export const PERIOD_MEASURES:Record<string,{label:string,unit:string,field:string,scale:number,digits:number,better:number,note:string}>={
  sentiment:{label:'Sentiment',unit:'Mean VADER compound score',field:'mean_sentiment',scale:1,digits:3,better:1,note:'Scores the whole review, so it mostly reflects how the business went.'},
  access:{label:'Negative access',unit:'% of reviews with a negative access or parking clause',field:'access_friction_share',scale:100,digits:2,better:-1,note:'Negative clauses about walking, transit or parking around the business. Lower is better.'},
  realm:{label:'Negative public space',unit:'% of reviews with a negative public-space clause',field:'public_realm_complaint_share',scale:100,digits:2,better:-1,note:'Negative clauses about safety, cleanliness, public space, construction or the neighborhood around the business. Lower is better.'}
};
const TOPIC_LABELS:Record<string,string>={walking_accessibility:'Walking / accessibility',transit:'Transit',parking:'Parking',safety:'Safety',cleanliness_maintenance:'Cleanliness',public_space:'Public space',construction:'Construction',food_service_value:'Food / service',neighborhood:'Neighbourhood'};
const fmt=(v:number,d:number)=>Number.isFinite(v)?v.toLocaleString('en-US',{minimumFractionDigits:d,maximumFractionDigits:d}):'—';
const signed=(v:number,d:number)=>(v>0?'+':v<0?'−':'')+fmt(Math.abs(v),d);
const years=(p:any)=>{const y=Object.keys(p?.by_year||{}).sort();return y.length?(y.length>1?`${y[0]}–${y.at(-1)!.slice(2)}`:y[0]):'';};

function ChartData({headers,rows}:{headers:string[],rows:(string|number)[][]}) {
  return <Collapsible className="mt-3 border-t pt-2">
    <CollapsibleTrigger asChild><Button variant="ghost" size="sm" className="group -ml-2.5 h-7 text-[11px]"><ChevronDown className="transition-transform group-data-[state=open]:rotate-180"/>View chart data</Button></CollapsibleTrigger>
    <CollapsibleContent><Table className="text-xs"><TableHeader><TableRow>{headers.map(h=><TableHead key={h} className="h-8 text-[10px]">{h}</TableHead>)}</TableRow></TableHeader>
      <TableBody>{rows.map((r,i)=><TableRow key={i}>{r.map((c,j)=><TableCell key={j} className="py-1.5 tabular-nums">{c}</TableCell>)}</TableRow>)}</TableBody></Table></CollapsibleContent>
  </Collapsible>;
}

function PeriodChart({project,measure}:{project:any,measure:string}) {
  const m=PERIOD_MEASURES[measure],{near,far}=project.periods;
  const data=PERIODS.filter(([k])=>near[k]?.n_reviews&&far[k]?.n_reviews).map(([k,label])=>({period:`${label} ${years(near[k])}`,near:near[k][m.field]*m.scale,far:far[k][m.field]*m.scale,nearN:near[k].n_reviews,farN:far[k].n_reviews}));
  const adjusted=((near.post[m.field]-near.pre[m.field])-(far.post[m.field]-far.pre[m.field]))*m.scale;
  const config={near:{label:'Near (within 500 m)',color:NEAR},far:{label:'Comparison (1.5–8 km)',color:FAR}};
  const tone=adjusted*m.better>0?'text-[#23767a]':adjusted*m.better<0?'text-[#a63824]':'';
  return <>
    <p className="chart-axis-label">{m.unit}</p>
    <ChartContainer config={config} className="decision-chart" style={{height:300}} aria-label={`${project.project}: ${m.label} by period`}>
      <BarChart accessibilityLayer data={data} margin={{top:10,right:20,left:0,bottom:5}}>
        <CartesianGrid vertical={false}/><XAxis dataKey="period" tickLine={false} axisLine={false} tick={{fontSize:11}}/>
        <YAxis tickLine={false} axisLine={false} width={55} tickFormatter={v=>fmt(v,m.digits>2?2:1)}/>
        <ReferenceLine y={0} stroke="#b4c2ae"/>
        <ChartTooltip content={<ChartTooltipContent formatter={(value:any,name:any,item:any)=><div className="chart-tooltip-row"><span style={{color:item.color}}>{(config as any)[name].label}</span><strong>{fmt(value,m.digits)}{m.scale===100?'%':''}</strong></div>}/>}/>
        <ChartLegend content={<ChartLegendContent/>}/>
        <Bar dataKey="near" fill="var(--color-near)" radius={3} maxBarSize={44} isAnimationActive={false}/>
        <Bar dataKey="far" fill="var(--color-far)" radius={3} maxBarSize={44} isAnimationActive={false}/>
      </BarChart>
    </ChartContainer>
    <p className="mt-2 text-sm">Comparison-adjusted change, before to after opening: <strong className={tone}>{signed(adjusted,m.digits)}{m.scale===100?' pp':''}</strong></p>
    <p className="chart-note text-muted-foreground">{m.note} Each bar is the share or mean across all reviews in that two-year period.</p>
    <ChartData headers={['Period','Near','Near reviews','Comparison','Comparison reviews']} rows={data.map(d=>[d.period,fmt(d.near,m.digits),d.nearN.toLocaleString('en-US'),fmt(d.far,m.digits),d.farN.toLocaleString('en-US')])}/>
  </>;
}

function TopicChart({project}:{project:any}) {
  const [mode,setMode]=React.useState('discussion');
  const rows=insights.historicalTopics(project,mode).map((r:any)=>({...r,label:TOPIC_LABELS[r.topic]||r.topic}));
  if(!rows.length)return <p className="text-sm text-muted-foreground">This project has no topic data.</p>;
  const complaints=mode==='complaints';
  return <>
    <ToggleGroup type="single" variant="outline" size="sm" value={mode} onValueChange={(v:string)=>v&&setMode(v)} aria-label="Topic measure" className="mb-2">
      <ToggleGroupItem value="discussion" className="px-3 text-[11px]">All mentions</ToggleGroupItem><ToggleGroupItem value="complaints" className="px-3 text-[11px]">Negative area mentions</ToggleGroupItem>
    </ToggleGroup>
    <p className="chart-axis-label">Comparison-adjusted change · percentage points</p>
    <ChartContainer config={{value:{label:'Adjusted change',color:NEAR}}} className="decision-chart" style={{height:Math.max(280,rows.length*36)}} aria-label={`${project.project}: topic changes`}>
      <BarChart accessibilityLayer layout="vertical" data={rows} margin={{top:5,right:30,left:5,bottom:5}}>
        <CartesianGrid horizontal={false}/><XAxis type="number" axisLine={false} tickLine={false} tickFormatter={v=>fmt(v,1)}/>
        <YAxis type="category" dataKey="label" width={130} axisLine={false} tickLine={false} tick={{fontSize:11}}/>
        <ReferenceLine x={0} stroke="#a8baa3"/>
        <ChartTooltip content={<ChartTooltipContent hideLabel formatter={(value:any,_n:any,item:any)=><div><strong>{item.payload.label}</strong><p>{signed(value,2)} pp adjusted</p><p>Near: {fmt(item.payload.nearPre,1)}% → {fmt(item.payload.nearPost,1)}%</p>{item.payload.sparse&&<p>Few mentions, so read with care.</p>}</div>}/>}/>
        <Bar dataKey="value" radius={3} maxBarSize={22} isAnimationActive={false}>{rows.map((r:any,i:number)=><Cell key={i} fill={complaints?(r.value>0?DOWN:UP):(r.value<0?DOWN:UP)} fillOpacity={r.sparse?.45:1}/>)}</Bar>
      </BarChart>
    </ChartContainer>
    <p className="chart-note text-muted-foreground">{complaints?'Below zero means fewer complaints near the project than in its comparison area.':'Above zero means more discussion, which counts praise and complaints alike.'} Faded bars have fewer than 20 nearby mentions in a period. Keyword rules made these labels, and no person has checked them yet.</p>
    <ChartData headers={['Topic','Near pre %','Near post %','Comparison change · pp','Adjusted · pp']} rows={rows.map((r:any)=>[r.label+(r.sparse?' · few mentions':''),fmt(r.nearPre,2),fmt(r.nearPost,2),signed(r.farChange,2),signed(r.value,2)])}/>
  </>;
}

// Engagement keeps the existing line chart, which place_charts.js mounts into #historyChart.
export function HistoryTabs({project,tab,onTab,onEngagement}:{project:any,tab:string,onTab:(t:string)=>void,onEngagement:()=>void}) {
  const setTab=onTab;
  React.useEffect(()=>{if(tab==='engagement')onEngagement();},[tab,project?.id]);
  if(!project)return null;
  return <Tabs value={tab} onValueChange={setTab} className="gap-4">
    <TabsList className="h-auto flex-wrap justify-start">
      <TabsTrigger value="engagement" className="text-xs">Business engagement</TabsTrigger>
      {Object.entries(PERIOD_MEASURES).map(([k,m])=><TabsTrigger key={k} value={k} className="text-xs">{m.label}</TabsTrigger>)}
      <TabsTrigger value="topics" className="text-xs">Topics</TabsTrigger>
    </TabsList>
    <TabsContent value="engagement" forceMount className="data-[state=inactive]:hidden">
      <div id="historyChart" className="insight-chart"/><p id="historyNote" className="chart-note text-muted-foreground"/>
    </TabsContent>
    {Object.keys(PERIOD_MEASURES).map(k=><TabsContent key={k} value={k}><PeriodChart project={project} measure={k}/></TabsContent>)}
    <TabsContent value="topics"><TopicChart project={project}/></TabsContent>
  </Tabs>;
}
