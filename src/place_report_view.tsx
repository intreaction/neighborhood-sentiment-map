import * as React from 'react';
import {createRoot} from 'react-dom/client';
import {FAMILIES,OUTCOMES,projectEffects,familySummary,leaveOneOut} from './place_projection.mjs';
import {Table,TableBody,TableCell,TableHead,TableHeader,TableRow} from './components/ui/table';
import {ToggleGroup,ToggleGroupItem} from './components/ui/toggle-group';
import {Card,CardContent,CardHeader,CardTitle} from './components/ui/card';
import {Select,SelectContent,SelectItem,SelectTrigger,SelectValue} from './components/ui/select';
import {Label} from './components/ui/label';
import {Badge} from './components/ui/badge';
import {Alert,AlertDescription,AlertTitle} from './components/ui/alert';
import {Button} from './components/ui/button';
import {cn} from './lib/utils';
import {HistoryTabs} from './place_history_charts';
import {areaColor,rampColor} from './place_area_math.mjs';
import {zipProfile} from './place_measures.mjs';

const fixed=(v:number|null|undefined,d=0)=>Number.isFinite(v)?(v as number).toLocaleString('en-US',{maximumFractionDigits:d,minimumFractionDigits:d}):'—';
const signed=(v:number|null|undefined,d:number)=>Number.isFinite(v)?((v as number)>0?'+':(v as number)<0?'−':'')+fixed(Math.abs(v as number),d):'—';
const ordinal=(n:number)=>n+(['th','st','nd','rd'][(n%100-20)%10]||['th','st','nd','rd'][n%100]||'th');

// A defined term: opens the shared glossary dialog through the [data-term] listener.
function Term({k,children}:{k:string,children:React.ReactNode}) {
  return <button type="button" className="term" data-term={k}>{children}</button>;
}
function Limited() {return <span className="text-xs italic text-muted-foreground"><Term k="limited_data">Limited data</Term></span>;}

// Each row reads one ZIP field; rank 1 is the highest value in the city.
const OUTCOME_FMT:Record<string,(v:number)=>string>={
  activity:v=>signed(v,0)+'%',sentiment:v=>signed(v,3),access:v=>signed(v,2)+' pp',realm:v=>signed(v,2)+' pp'
};
const OUTCOME_HEAD:Record<string,[string,string]>={activity:['Business engagement','engagement_change'],sentiment:['Sentiment','sentiment'],access:['Negative access','negative_access'],realm:['Negative public space','negative_realm']};
const tone=(key:string,v:number)=>{const b=(OUTCOMES as any[]).find(o=>o.key===key).better;return v*b>0?'text-[#23767a]':v*b<0?'text-[#a63824]':'';};

function SectionHeading({eyebrow,title,children}:{eyebrow:string,title:React.ReactNode,children:React.ReactNode}) {
  return <div className="mb-5 flex flex-col gap-3 md:flex-row md:items-end md:justify-between md:gap-9">
    <div><p className="eyebrow">{eyebrow}</p><h2 className="mt-1 font-serif text-[26px] md:text-[32px]">{title}</h2></div>
    <p className="max-w-[420px] text-xs leading-relaxed text-muted-foreground">{children}</p>
  </div>;
}
const tableFrame='overflow-hidden rounded-lg border bg-card';
const headClass='h-auto min-h-11 bg-muted/70 px-4 py-2.5 align-top text-[10px] font-semibold uppercase tracking-wider text-muted-foreground whitespace-normal';
const cellClass='px-4 py-3 tabular-nums';

function Swatch({color}:{color:string}) {
  return <span aria-hidden="true" className="inline-block size-3.5 shrink-0 rounded-[3px] border border-black/10" style={{backgroundColor:color}}/>;
}
// Where the ZIP sits among the city's ZIPs: 0 = lowest, 1 = highest; the tick marks the median.
function RankStrip({position,color,label}:{position:number,color:string,label:string}) {
  return <span className="relative inline-block h-1.5 w-24 shrink-0 rounded-full bg-muted" role="img" aria-label={label} title={label}>
    <span className="absolute top-1/2 left-1/2 h-3 w-px -translate-y-1/2 bg-muted-foreground/50"/>
    <span className="absolute top-1/2 size-3 -translate-x-1/2 -translate-y-1/2 rounded-full ring-2 ring-card" style={{left:`${position*100}%`,backgroundColor:color}}/>
  </span>;
}

function ProfileTable({zip,area,city,cityLabel}:any) {
  return <section id="results" className="zip-report" aria-live="polite">
    <SectionHeading eyebrow="03 / ZIP profile" title={zip?`ZIP ${zip} in ${cityLabel}`:'Choose a ZIP'}>
      Historical Yelp and Census measures for the selected ZIP, compared with the {city.areas.length} mapped ZIPs in {cityLabel}. Rank 1 is the highest value. Limited data means too few reviews, not zero.
    </SectionHeading>
    <div className={tableFrame}><Table>
      <TableHeader><TableRow className="hover:bg-transparent">
        <TableHead className={headClass}>Measure</TableHead><TableHead className={headClass}>This ZIP</TableHead>
        <TableHead className={headClass}><Term k="city_median">City median</Term></TableHead><TableHead className={headClass}><Term k="city_rank">City rank</Term></TableHead>
        <TableHead className={headClass}>Period</TableHead>
      </TableRow></TableHeader>
      <TableBody>{zipProfile(city.areas,zip).map((row:any)=>{
        const m=row.measure,v=row.value,ok=v!==null,rank=row.rank,moe=row.moe,position=row.position??.5,values={length:row.compared};
        const color=ok?(m.focus?areaColor(v,m.focus):rampColor(position)):'';
        return <TableRow key={m.term} data-measure={m.key}>
          <TableCell className="px-4 py-3 font-medium"><Term k={m.term}>{m.label}</Term></TableCell>
          <TableCell className={cellClass}>{ok?<span className="flex items-center gap-2.5"><Swatch color={color}/><span>{m.format(v)}{moe!==null&&<span className="ml-1 text-[10px] text-muted-foreground">± ${fixed(moe)}</span>}</span></span>:<Limited/>}</TableCell>
          <TableCell className={cellClass}>{row.median!==null?m.format(row.median):'—'}</TableCell>
          <TableCell className={cellClass}>{ok?<span className="flex items-center gap-3"><RankStrip position={position} color={color} label={`Higher than ${Math.round(position*100)}% of ${cityLabel} ZIPs`}/><span>{ordinal(rank as number)} of {values.length}</span></span>:'—'}</TableCell>
          <TableCell className="px-4 py-3 text-[11px] text-muted-foreground">{row.period}</TableCell>
        </TableRow>;})}
      </TableBody>
    </Table></div>
    <div className="mt-3 flex flex-wrap items-center gap-x-6 gap-y-2 text-[11px] text-muted-foreground">
      <span className="flex items-center gap-2"><span className="h-2 w-24 rounded-full" style={{background:`linear-gradient(90deg,${rampColor(0)},${rampColor(.5)},${rampColor(1)})`}}/>Map colours: darker = more (for income, darker = lower income)</span>
      <span className="flex items-center gap-2"><span className="h-2 w-24 rounded-full" style={{background:`linear-gradient(90deg,${rampColor(0,true)},${rampColor(.5,true)},${rampColor(1,true)})`}}/>Changes: teal = growth or better, red = decline or worse</span>
      <span className="flex items-center gap-2"><RankStrip position={.8} color={rampColor(.8)} label="Example position"/>Position among the city’s ZIPs; tick = median</span>
    </div>
  </section>;
}

function PastProjects({rows,check,history,projects,onHistory}:any) {
  const [family,setFamily]=React.useState('all');
  const [historyId,setHistoryId]=React.useState<string|null>(null);
  const [chart,setChart]=React.useState('engagement');
  const summary=familySummary(rows,family),members=summary.members;
  const selectedHistory=members.some((m:any)=>m.id===historyId)?historyId:members[0]?.id;
  // Agent tools ask for a kind, project or chart through this event, and read the result back.
  React.useEffect(()=>{
    const onRequest=(e:Event)=>{const d=(e as CustomEvent).detail;if(d.kind)setFamily(d.kind);if(d.project_id)setHistoryId(d.project_id);if(d.chart)setChart(d.chart);};
    window.addEventListener('place:past-projects',onRequest);
    return ()=>window.removeEventListener('place:past-projects',onRequest);
  },[]);
  React.useEffect(()=>{window.dispatchEvent(new CustomEvent('place:report-state',{detail:{kind:family,project_id:selectedHistory??null,chart}}));},[family,selectedHistory,chart]);
  const project=history.projects.find((p:any)=>p.id===selectedHistory);
  const city=(id:string)=>projects.find((p:any)=>p.id===id)?.city_label??'';
  const a=check.activity;
  const choices:[string,string,number][]=[['all','All projects',rows.length],...Object.entries(FAMILIES).map(([k,f]:[string,any])=>[k,f.label,rows.filter((r:any)=>r.family===k).length] as [string,string,number])];
  return <section id="past-projects" className="zip-report" aria-live="polite">
    <SectionHeading eyebrow="04 / Past projects" title="What happened around similar past projects?">
      Each row is a past project. Figures are the <Term k="adjusted_change">change near the project</Term> (within 500 m) from two years before opening to two years after, minus the same change in its <Term k="comparison_area">comparison area</Term> 1.5–8 km away.
    </SectionHeading>
    <ToggleGroup type="single" variant="outline" value={family} onValueChange={(v:string)=>v&&setFamily(v)} aria-label="Kind of project" className="mb-4 grid w-full grid-cols-2 gap-2.5 shadow-none md:grid-cols-5">
      {choices.map(([key,label,n])=><ToggleGroupItem key={key} value={key} className="h-auto flex-col items-start gap-1.5 rounded-lg! border bg-card px-4 py-3.5 text-left data-[state=on]:border-primary data-[state=on]:bg-primary data-[state=on]:text-primary-foreground">
        <span className="font-serif text-lg font-normal">{label}</span>
        <Badge variant="secondary" className="text-[10px] font-medium">{n} project{n===1?'':'s'}</Badge>
      </ToggleGroupItem>)}
    </ToggleGroup>
    <div className={tableFrame}><Table>
      <TableHeader><TableRow className="hover:bg-transparent">
        <TableHead className={headClass}>Project</TableHead><TableHead className={headClass}>Opened</TableHead>
        {OUTCOMES.map((o:any)=><TableHead key={o.key} className={headClass}><Term k={OUTCOME_HEAD[o.key][1]}>{OUTCOME_HEAD[o.key][0]}</Term>
          {(o.key==='access'||o.key==='realm')&&<Badge variant="outline" className="mt-1 flex w-fit border-[#b56b32] px-1.5 text-[9px] text-[#a63824] normal-case tracking-normal">low reliability</Badge>}</TableHead>)}
      </TableRow></TableHeader>
      <TableBody>
        {members.map((m:any)=><TableRow key={m.id} data-project={m.id} data-state={m.id===selectedHistory?'selected':undefined} className="data-[state=selected]:bg-muted/60">
          <TableCell className="px-4 py-3"><Button variant="link" className="h-auto p-0 text-left font-medium text-foreground" onClick={()=>setHistoryId(m.id)} aria-label={`Show ${m.project} in the charts below`}>{m.project}</Button>
            <span className="block text-[10px] text-muted-foreground">{city(m.id)} · {(FAMILIES as any)[m.family].label}</span></TableCell>
          <TableCell className={cellClass}>{m.opening.slice(0,7)}</TableCell>
          {OUTCOMES.map((o:any)=>{const v=o.key==='activity'?100*(Math.exp(m.effects[o.key])-1):m.effects[o.key];return <TableCell key={o.key} className={cn(cellClass,tone(o.key,v))}>{OUTCOME_FMT[o.key](v)}</TableCell>;})}
        </TableRow>)}
        <TableRow className="bg-muted/40 font-semibold hover:bg-muted/40">
          <TableCell className="px-4 py-3"><Term k="family_average">{family==='all'?'All projects':(FAMILIES as any)[family].label}: average</Term></TableCell><TableCell className={cellClass}>n = {summary.n}</TableCell>
          {OUTCOMES.map((o:any)=>{const s=summary.outcomes[o.key];return <TableCell key={o.key} className={cn(cellClass,tone(o.key,s.mean))}>{OUTCOME_FMT[o.key](s.mean)}<span className="block text-[10px] font-normal text-muted-foreground">{s.better} of {summary.n} improved</span></TableCell>;})}
        </TableRow>
      </TableBody>
    </Table></div>
    <div className="my-4 grid gap-6 text-[11px] leading-relaxed text-muted-foreground md:grid-cols-2">
      <p><strong className="text-foreground">Read the rows, not the average.</strong> <Term k="loo_check">Holding out</Term> each of the {a.n} projects in turn, the average for its <Term k="project_family">kind of project</Term> missed its engagement change by {fixed(100*a.family_mae)} log points, against {fixed(100*a.overall_mae)} for the plain all-project average. Project kind did not predict better on any measure; projects of the same kind differed more than kinds did.</p>
      <p><strong className="text-foreground">Low-reliability columns.</strong> Negative access and public-space rates come from keyword rules. Checked against labelled clauses, the rules found about one in six negative comments about an area, so these columns undercount complaints. Business engagement counts reviews, not visits or sales, and several post-opening windows include 2020. <a className="font-semibold text-primary underline" href="methods.html#validation">How we checked</a></p>
    </div>
    <Card id="project-charts" className="scroll-mt-4 gap-4 shadow-none">
      <CardHeader>
        <p className="eyebrow">Observed historical activity</p>
        <CardTitle className="font-serif text-2xl font-normal md:text-[29px]">What happened around {project?.project??'this project'}?</CardTitle>
        <p className="text-xs text-muted-foreground">Each tab charts one measure near the project and in its comparison area. Choose a project in the table above or here.</p>
        <div className="mt-2 grid max-w-[350px] gap-1.5"><Label htmlFor="historyProject" className="text-[11px]">Historical project</Label>
          <Select value={selectedHistory??undefined} onValueChange={setHistoryId}>
            <SelectTrigger id="historyProject" className="w-full bg-card"><SelectValue/></SelectTrigger>
            <SelectContent>{members.map((m:any)=><SelectItem key={m.id} value={m.id}>{m.project}</SelectItem>)}</SelectContent>
          </Select></div>
      </CardHeader>
      <CardContent><HistoryTabs project={project} tab={chart} onTab={setChart} onEngagement={()=>onHistory(selectedHistory)}/></CardContent>
    </Card>
  </section>;
}

function ArchiveNote() {
  return <Alert id="notes" className="mx-3.5 mb-8 w-auto max-w-[1440px] bg-[#e9ecdf] md:mx-[4vw]">
    <AlertTitle className="font-serif text-xl font-normal">A record of what happened, not a forecast.</AlertTitle>
    <AlertDescription className="text-xs leading-relaxed">
      <p>Reviews come from Yelp’s January 2022 archive; income and poverty from baseline ACS estimates. Business engagement counts Yelp reviews, not revenue, visits or welfare. Past-project changes were measured within 500 m of each project and describe those places only. Sentiment and mention rates use <Term k="clause_rules">rule-based</Term> and <Term k="vader">VADER</Term> scoring, checked against agent labels pending human review. <a className="font-semibold text-primary underline" href="findings.html">What we found</a> · <a className="font-semibold text-primary underline" href="methods.html">Methodology and glossary</a></p>
    </AlertDescription>
  </Alert>;
}

export function mountZipReport(container:HTMLElement,{history,model,projects,onHistory}:any) {
  const rows=projectEffects(history,model.excluded_projects.map((p:any)=>p.id)),check=leaveOneOut(rows);
  const root=createRoot(container);
  return (context:any)=>root.render(<>
    <ProfileTable {...context}/>
    <PastProjects rows={rows} check={check} history={history} projects={projects} onHistory={onHistory}/>
    <ArchiveNote/>
  </>);
}
