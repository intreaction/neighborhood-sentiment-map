import * as React from 'react';
import {Info,Pause,Play,RotateCcw} from 'lucide-react';
import {Slider} from './components/ui/slider';
import {Button} from './components/ui/button';
import {ToggleGroup,ToggleGroupItem} from './components/ui/toggle-group';
import {Select,SelectContent,SelectItem,SelectTrigger,SelectValue} from './components/ui/select';
import {Popover,PopoverContent,PopoverTrigger} from './components/ui/popover';
import type {createPanelStore} from './place_panel';

type Store=ReturnType<typeof createPanelStore>;
const LENGTHS:Record<string,[number,string][]>={
  quarter:[[1,'1 quarter'],[4,'1 year'],[8,'2 years'],[12,'3 years']],
  month:[[1,'1 month'],[3,'3 months'],[12,'1 year'],[24,'2 years'],[36,'3 years']]
};
const SMOOTH:[number,string][]=[[1,'1 month'],[3,'3-mo avg'],[12,'12-mo avg']];
const pct=(i:number,n:number)=>`${100*i/(n-1)}%`;
const toggle='h-7 px-2 text-[11px]';

// Compact time control for the sticky header: one period at a time, or two equal periods compared.
// Past-project openings are landmarks on the track; choosing one compares the years either side.
export function TimelineControls({store,actions}:{store:Store,actions:any}) {
  const v=React.useSyncExternalStore(store.subscribe,store.get);
  // Year labels get their own band under the track; on a narrow track, label every other year.
  const track=React.useRef<HTMLDivElement>(null),[width,setWidth]=React.useState(600);
  React.useEffect(()=>{const el=track.current;if(!el)return;const ro=new ResizeObserver(([e])=>setWidth(e.contentRect.width));ro.observe(el);return ()=>ro.disconnect();},[v.ready]);
  if(!v.ready)return null;
  const s=v.setting,n=v.count,compare=s.mode==='compare',u=s.grain==='quarter'?1:3;
  const allYears=v.periods.map((p:string,i:number)=>({p,i})).filter(({i}:any)=>i%(4*u)===0);
  const every=width/allYears.length>=40?1:2,years=allYears.filter((_:any,k:number)=>k%every===0);
  const windowBox=(start:number,len:number,tone:string,name:string)=><span aria-hidden="true" title={name}
    className={`absolute top-1/2 h-2.5 -translate-y-1/2 rounded-sm ${tone}`} style={{left:`calc(${pct(start,n)} - ${50/(n-1)}%)`,width:`${100*len/(n-1)}%`}}/>;
  return <div className="flex min-w-0 flex-1 flex-wrap items-center gap-x-2.5 gap-y-1.5" role="group" aria-label="Map time period">
    <ToggleGroup type="single" variant="outline" size="sm" value={s.mode} onValueChange={(m:string)=>m&&actions.setMode(m)} aria-label="Time mode">
      <ToggleGroupItem value="snapshot" className={toggle}>One period</ToggleGroupItem><ToggleGroupItem value="compare" className={toggle}>Compare</ToggleGroupItem>
    </ToggleGroup>
    <ToggleGroup type="single" variant="outline" size="sm" value={s.grain} onValueChange={(g:string)=>g&&actions.setGrain(g)} aria-label="Time grain">
      <ToggleGroupItem value="quarter" className={toggle} aria-label="Quarters">Qtr</ToggleGroupItem><ToggleGroupItem value="month" className={toggle} aria-label="Months">Mo</ToggleGroupItem>
    </ToggleGroup>
    {(compare||s.grain==='month')&&<Select value={String(compare?s.length:s.smooth)} onValueChange={(x:string)=>actions.setTime(compare?{length:Number(x)}:{smooth:Number(x)})}>
      <SelectTrigger size="sm" className="h-7 w-[96px] bg-card px-2 text-[11px]" aria-label={compare?'Length of each period':'Rolling average'}><SelectValue/></SelectTrigger>
      <SelectContent>{(compare?LENGTHS[s.grain]:SMOOTH).map(([k,l])=><SelectItem key={k} value={String(k)}>{l}</SelectItem>)}</SelectContent>
    </Select>}
    {!compare&&<Button variant="outline" size="icon" className="size-7" onClick={actions.togglePlay} aria-pressed={v.playing} aria-label={v.playing?'Pause':'Play through periods'}>{v.playing?<Pause/>:<Play/>}</Button>}
    {/* Track: openings above, years below, COVID shaded from March 2020. */}
    <div ref={track} className="relative min-w-[260px] flex-1 px-1.5 pt-3">
      <span aria-hidden="true" className="timeline-covid absolute top-[16px] h-2.5 rounded-sm" style={{left:`calc(0.375rem + (100% - 0.75rem) * ${v.covidIndex/(n-1)})`,right:'0.375rem'}} title="COVID-19, from March 2020"/>
      <div className="absolute inset-x-1.5 top-0 h-3">
        {v.markers.map((m:any)=><Popover key={m.id}><PopoverTrigger asChild>
          <button type="button" className="timeline-marker" style={{left:pct(m.index,n)}} aria-label={`${m.name}, opened ${m.opening}`}>◆</button></PopoverTrigger>
          <PopoverContent className="w-64 text-xs" side="bottom">
            <p className="m-0 font-serif text-base">{m.name}</p><p className="mt-1 mb-3 text-muted-foreground">Opened {m.opening}. Compare the ZIP map before and after this date, or open the project's own before-and-after comparison.</p>
            <div className="flex flex-wrap gap-2"><Button size="sm" onClick={()=>actions.projectStart(m.id)}>Compare around opening</Button><Button size="sm" variant="outline" onClick={()=>actions.openProject(m.id)}>Project details</Button></div>
          </PopoverContent></Popover>)}
      </div>
      <Slider min={compare?0:v.minAt} max={n-1} step={1} showRange={!compare}
        value={compare?[s.from,s.to]:[s.at]} minStepsBetweenThumbs={compare?s.length:0}
        onValueChange={(x:number[])=>actions.setTime(compare?{from:x[0],to:x[1]}:{at:x[0]})}
        thumbLabels={compare?['Start of the earlier period','Start of the later period']:['Period shown']}
        aria-valuetext={compare?v.text.change:v.text.level}>
        {compare&&windowBox(s.from,s.length,'bg-[var(--c-b9c2b5)]/70','Earlier period')}
        {compare&&windowBox(s.to,s.length,'bg-primary/35','Later period')}
      </Slider>
      <div className="relative mt-1.5 h-3.5 border-t border-border/60 pt-0.5 text-[9px] leading-none text-muted-foreground" aria-hidden="true">
        {years.map(({p,i}:any)=><span key={i} className="absolute -translate-x-1/2 tabular-nums" style={{left:pct(i,n)}}>{p.slice(-4)}</span>)}
      </div>
    </div>
    <p className="m-0 w-[150px] text-[11px] leading-tight font-semibold" aria-live="polite">
      {compare?v.text.change:<>{v.text.level}<span className="block font-normal text-muted-foreground">vs. {v.text.base}</span></>}
    </p>
    <Button variant="ghost" size="icon" className="size-7" onClick={actions.reset} disabled={v.isDefault} aria-label="Reset to 2012–2014 against 2019–2021" title="Reset to 2012–2014 against 2019–2021"><RotateCcw/></Button>
    <Popover><PopoverTrigger asChild><Button variant="ghost" size="icon" className="size-7" aria-label="About the time bar"><Info/></Button></PopoverTrigger>
      <PopoverContent className="w-72 text-xs leading-relaxed" align="end">
        <p className="m-0">◆ marks past-project openings in this city. The hatched band is COVID-19, from March 2020.</p>
        <p className="mt-2 mb-0">{v.text.minimum?`Each period needs ${v.text.minimum} reviews, or the ZIP shows limited data.`:'This period falls outside the data.'}{v.text.access?'':' Access discussion needs at least one whole quarter.'} Income and poverty stay at their ACS baseline.</p>
        <p className="mt-2 mb-0">"One period" compares with the same period a year earlier, so seasons don't read as change.</p>
      </PopoverContent></Popover>
  </div>;
}
