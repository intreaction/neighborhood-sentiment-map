import * as React from 'react';
import {createRoot} from 'react-dom/client';
import {Check,ChevronsUpDown,ChevronDown,Minus,Plus,ZoomIn,ZoomOut,Maximize2,Crosshair,RotateCcw,ArrowDown} from 'lucide-react';
import {Select,SelectContent,SelectGroup,SelectItem,SelectLabel,SelectSeparator,SelectTrigger,SelectValue} from './components/ui/select';
import {Popover,PopoverContent,PopoverTrigger} from './components/ui/popover';
import {Command,CommandEmpty,CommandGroup,CommandInput,CommandItem,CommandList} from './components/ui/command';
import {Accordion,AccordionContent,AccordionItem,AccordionTrigger} from './components/ui/accordion';
import {Collapsible,CollapsibleContent,CollapsibleTrigger} from './components/ui/collapsible';
import {ToggleGroup,ToggleGroupItem} from './components/ui/toggle-group';
import {Card,CardContent,CardHeader,CardTitle} from './components/ui/card';
import {Button} from './components/ui/button';
import {Input} from './components/ui/input';
import {Label} from './components/ui/label';
import {Switch} from './components/ui/switch';
import {Separator} from './components/ui/separator';
import {cn} from './lib/utils';

// The app logic (place_app.js, place_area_ui.js) computes everything and writes it here;
// the panel only renders this view and reports user intent through actions.
export type PanelView={[key:string]:any};
export function createPanelStore(initial:PanelView) {
  let view=initial;const listeners=new Set<()=>void>();
  return {get:()=>view,set(patch:PanelView){view={...view,...patch};listeners.forEach(f=>f());},
    subscribe(f:()=>void){listeners.add(f);return ()=>{listeners.delete(f);};}};
}
type Store=ReturnType<typeof createPanelStore>;

const SINGLE_FOCUSES=[['activity','Reach active business areas'],['income','Support lower-income areas'],['decline','Explore declining activity'],['experience','Explore worsening experiences'],['access','Investigate access concerns'],['none','No heatmap']];
const COMBINED_FOCUSES=[['combined','Poverty + activity'],['poverty_experience','Poverty + sentiment'],['poverty_access','Poverty + access discussion'],['decline_experience','Activity + sentiment']];
const fieldLabel='text-[10px] font-semibold uppercase tracking-wider text-muted-foreground';
const smallButton='h-8 gap-1 px-2.5 text-[11px]';

function ZipCombobox({zips,zip,onSelect,disabled}:{zips:string[],zip:string|null,onSelect:(z:string)=>void,disabled:boolean}) {
  const [open,setOpen]=React.useState(false);
  return <Popover open={open} onOpenChange={setOpen}>
    <PopoverTrigger asChild><Button id="areaSelect" variant="outline" role="combobox" aria-expanded={open} aria-label="Project ZIP" disabled={disabled} className="w-full justify-between bg-card font-semibold">
      {zip?`ZIP ${zip}`:'Choose a ZIP'}<ChevronsUpDown className="opacity-50"/>
    </Button></PopoverTrigger>
    <PopoverContent className="w-[220px] p-0" align="start">
      <Command><CommandInput placeholder="Search ZIP…"/><CommandList>
        <CommandEmpty>No mapped ZIP.</CommandEmpty>
        <CommandGroup>{zips.map(z=><CommandItem key={z} value={z} onSelect={()=>{onSelect(z);setOpen(false);}}>
          ZIP {z}<Check className={cn('ml-auto',z===zip?'opacity-100':'opacity-0')}/>
        </CommandItem>)}</CommandGroup>
      </CommandList></Command>
    </PopoverContent>
  </Popover>;
}

function Legend({legend}:{legend:any}) {
  if(!legend||legend.hidden)return null;
  return <div className="flex flex-col gap-2 py-3">
    <strong className="text-[10px]">{legend.title}</strong>
    {legend.combined?<div className="combined-legend">
      <table><caption>{legend.combined.columnTitle} →</caption>
        <thead><tr><td/>{legend.combined.columns.map((c:string[],i:number)=><th key={i} scope="col">{c[0]}<br/>{c[1]}</th>)}</tr></thead>
        <tbody>{legend.combined.rows.map((r:any,i:number)=><tr key={i}><th scope="row">{r.label[0]}<br/>{r.label[1]}</th>
          {r.cells.map((cell:any,j:number)=><td key={j} aria-label={cell.aria} style={{backgroundColor:cell.color,color:cell.text}}>{cell.label}</td>)}</tr>)}</tbody>
      </table><p>{legend.combined.note}</p>
    </div>:<div className="w-full">
      <div className={cn('heat-ramp',legend.diverging&&'diverging')}/>
      <div className="heat-scale-labels"><span>{legend.low}</span><span>{legend.high}</span></div>
    </div>}
    <span className="missing-key"><i/> Limited data</span>
  </div>;
}

function CoordinateForm({longitude,latitude,onSubmit}:{longitude:string,latitude:string,onSubmit:(lon:number,lat:number)=>void}) {
  const [lon,setLon]=React.useState(longitude),[lat,setLat]=React.useState(latitude);
  React.useEffect(()=>{setLon(longitude);setLat(latitude);},[longitude,latitude]);
  return <form className="grid grid-cols-2 gap-2 pt-2" onSubmit={e=>{e.preventDefault();onSubmit(Number(lon),Number(lat));}}>
    <div className="grid gap-1"><Label htmlFor="longitude" className="text-[10px]">Longitude</Label><Input id="longitude" className="bg-card" type="number" step="any" min="-180" max="180" required value={lon} onChange={e=>setLon(e.target.value)}/></div>
    <div className="grid gap-1"><Label htmlFor="latitude" className="text-[10px]">Latitude</Label><Input id="latitude" className="bg-card" type="number" step="any" min="-90" max="90" required value={lat} onChange={e=>setLat(e.target.value)}/></div>
    <Button type="submit" size="sm" className="col-span-2">Set location</Button>
  </form>;
}

function FocusCard({card}:{card:any}) {
  const [open,setOpen]=React.useState(true);
  if(!card)return null;
  return <Collapsible open={open} onOpenChange={setOpen} asChild>
    <Card className="my-3 gap-0 rounded-xl py-4 shadow-none" aria-live="polite">
      <CardHeader className="px-5">
        <div className="flex items-center justify-between"><p className="eyebrow m-0!">Selected focus</p>
          <CollapsibleTrigger asChild><Button variant="ghost" size="icon" className="size-7" aria-label={open?'Collapse focus details':'Expand focus details'}>{open?<Minus/>:<Plus/>}</Button></CollapsibleTrigger></div>
        <CardTitle className="font-serif text-2xl leading-tight font-normal">{card.title}</CardTitle>
        <p className="text-[10px] text-muted-foreground">{card.meta}</p>
      </CardHeader>
      <CollapsibleContent><CardContent className="px-5 text-[11px] leading-relaxed [&_p]:my-2">
        <div className={cn('mt-3 font-serif text-[48px] leading-[1.1] tracking-tight',card.combined&&'text-[23px] leading-snug')} style={{color:card.signalColor,borderLeft:`5px solid ${card.signalBorder}`,paddingLeft:12}}>{card.signal}</div>
        <p className="text-[10px] text-muted-foreground">{card.signalLabel}</p>
        {card.combinedValues?.length>0&&<div className="my-3 grid grid-cols-2 gap-3">{card.combinedValues.map((m:any)=><div key={m.label}>
          <span className="block text-[10px]">{m.label}</span><strong className="block font-serif text-[27px] font-normal">{m.value}</strong><small className="block text-[10px] text-muted-foreground">{m.period}</small></div>)}</div>}
        <p>{card.opportunity}</p><p>{card.reach}</p>{card.move&&<p>{card.move}</p>}
        <a className="font-semibold text-primary underline-offset-4 hover:underline" href="#results">Explore the full analysis ↓</a>
      </CardContent></CollapsibleContent>
    </Card>
  </Collapsible>;
}

function PlacePanel({store,actions}:{store:Store,actions:any}) {
  const v=React.useSyncExternalStore(store.subscribe,store.get);
  const [open,setOpen]=React.useState(true);
  const ready=v.cities.length>0,isCombined=COMBINED_FOCUSES.some(([k])=>k===v.focus);
  return <aside id="proposalControls" className="floating-controls" aria-label="Map and project controls">
    <div className="flex items-start justify-between gap-3">
      <div><p className="eyebrow">Place Lab / ZIP explorer</p><h1 id="mapTitle" className="m-0 font-serif text-[38px] leading-tight tracking-tight">{v.cityLabel}</h1></div>
      <Button variant="ghost" size="icon" onClick={()=>setOpen(!open)} aria-expanded={open} aria-controls="panelBody" aria-label={open?'Collapse controls':'Expand controls'}>{open?<Minus/>:<Plus/>}</Button>
    </div>
    {open&&<div id="panelBody">
      <div className="mt-3 grid grid-cols-2 gap-2.5">
        <div className="grid gap-1.5"><Label htmlFor="citySelect" className={fieldLabel}>Map city</Label>
          <Select value={v.city||undefined} onValueChange={actions.setCity} disabled={!ready}>
            <SelectTrigger id="citySelect" className="w-full bg-card font-semibold"><SelectValue placeholder="Loading…"/></SelectTrigger>
            <SelectContent>{v.cities.map((c:any)=><SelectItem key={c.id} value={c.id}>{c.label}</SelectItem>)}</SelectContent>
          </Select></div>
        <div className="grid gap-1.5"><Label htmlFor="areaSelect" className={fieldLabel}>Project ZIP</Label>
          <ZipCombobox zips={v.zips} zip={v.zip} onSelect={actions.setZip} disabled={!ready}/></div>
      </div>

      <div className="grid gap-1.5 pt-4 pb-1">
        <Label htmlFor="focusSelect" className={fieldLabel}>Your focus</Label>
        <Select value={v.focus} onValueChange={actions.setFocus}>
          <SelectTrigger id="focusSelect" className={cn('w-full border-primary bg-primary font-semibold text-primary-foreground [&_svg]:text-primary-foreground! [&_svg]:opacity-80',isCombined&&'border-[#684779] bg-[#684779]')}><SelectValue/></SelectTrigger>
          <SelectContent>
            <SelectGroup><SelectLabel>Single focus</SelectLabel>{SINGLE_FOCUSES.map(([k,l])=><SelectItem key={k} value={k}>{l}</SelectItem>)}</SelectGroup>
            <SelectSeparator/>
            <SelectGroup><SelectLabel className="text-[#59396d]">Combined views</SelectLabel>{COMBINED_FOCUSES.map(([k,l])=><SelectItem key={k} value={k} className="text-[#59396d] focus:bg-[#eee6f3] focus:text-[#59396d]">◈ {l}</SelectItem>)}</SelectGroup>
          </SelectContent>
        </Select>
        {v.focus==='income'&&<ToggleGroup type="single" variant="outline" size="sm" value={v.economic} onValueChange={(x:string)=>x&&actions.setEconomic(x)} aria-label="Economic measure" className="mt-1.5 w-full">
          <ToggleGroupItem value="income" className="flex-1 text-[11px]">Household income</ToggleGroupItem><ToggleGroupItem value="poverty" className="flex-1 text-[11px]">Poverty rate</ToggleGroupItem>
        </ToggleGroup>}
        <span className="text-[9px] text-muted-foreground">{v.heatPeriod}</span>
      </div>

      <div className="mt-1 mb-1 flex flex-wrap gap-1.5">
        <Button variant="outline" size="icon" className="size-8" aria-label="Zoom in" onClick={actions.zoomIn}><ZoomIn/></Button>
        <Button variant="outline" size="icon" className="size-8" aria-label="Zoom out" onClick={actions.zoomOut}><ZoomOut/></Button>
        <Button variant="outline" size="sm" className={smallButton} onClick={actions.cityView}><Maximize2/>City view</Button>
        <Button variant="outline" size="sm" className={smallButton} onClick={actions.focusSelection}><Crosshair/>Selected ZIP</Button>
      </div>
      <Legend legend={v.legend}/>

      <Accordion type="multiple" className="border-t">
        <AccordionItem value="past">
          <AccordionTrigger className="py-3 text-xs">Past projects</AccordionTrigger>
          <AccordionContent className="grid gap-3">
            <p className="m-0 text-[11px] text-muted-foreground">Jump to the ZIP around one of the eleven historical projects. The tables below the map show what changed there.</p>
            <div className="grid gap-1.5"><Label htmlFor="landmarkSelect" className="text-xs">Historical project</Label>
              <Select value={v.landmark||'custom'} onValueChange={actions.setLandmark}>
                <SelectTrigger id="landmarkSelect" className="w-full bg-card"><SelectValue/></SelectTrigger>
                <SelectContent><SelectItem value="custom">Choose a project</SelectItem>{v.landmarks.map((l:any)=><SelectItem key={l.id} value={l.id}>{l.label}</SelectItem>)}</SelectContent>
              </Select></div>
            <div className="flex flex-wrap gap-2"><Button asChild size="sm"><a href="#results">See the evidence<ArrowDown/></a></Button><Button variant="ghost" size="sm" onClick={actions.reset}><RotateCcw/>Reset map</Button></div>
            {v.formStatus&&<p className="m-0 text-[10px] text-muted-foreground" role="status">{v.formStatus}</p>}
          </AccordionContent>
        </AccordionItem>
        <AccordionItem value="settings">
          <AccordionTrigger className="py-3 text-xs">Map settings &amp; evidence notes</AccordionTrigger>
          <AccordionContent className="grid gap-3 text-[11px]">
            <div className="grid gap-1.5"><span className={fieldLabel}>Map detail</span>
              <ToggleGroup type="single" variant="outline" size="sm" value={v.basemap} onValueChange={(x:string)=>x&&actions.setBasemap(x)} aria-label="Map detail" className="w-full">
                <ToggleGroupItem value="streets" className="flex-1 text-[11px]">Streets · online</ToggleGroupItem><ToggleGroupItem value="offline" className="flex-1 text-[11px]">ZIP boundaries · offline</ToggleGroupItem>
              </ToggleGroup></div>
            <div className="flex items-center gap-2"><Switch id="showBusinesses" checked={v.showBusinesses} onCheckedChange={actions.setBusinesses}/><Label htmlFor="showBusinesses" className="text-xs">Business dots</Label></div>
            <Separator/>
            <p className="m-0">{v.heatExplanation}</p>{v.heatCoverage&&<p className="m-0">{v.heatCoverage}</p>}
            <p className="m-0 text-muted-foreground">Area colors follow ZIP/ZCTA boundaries, including at street-level zoom.</p>
            <div className="map-legend"><span><i/>ZIP/ZCTA areas</span><span><i className="legend-business"/>Reviewed businesses</span></div>
            <Collapsible><CollapsibleTrigger asChild><Button variant="ghost" size="sm" className="group -ml-2.5 h-7 text-[11px]"><ChevronDown className="transition-transform group-data-[state=open]:rotate-180"/>Enter exact coordinates</Button></CollapsibleTrigger>
              <CollapsibleContent><CoordinateForm longitude={v.longitude} latitude={v.latitude} onSubmit={actions.setCoordinates}/></CollapsibleContent></Collapsible>
            <p className="m-0 text-[10px] text-muted-foreground" role="status">{v.basemapStatus}</p>
            <p className="m-0 text-[10px] text-muted-foreground" role="status">{v.sceneStatus}</p>
          </AccordionContent>
        </AccordionItem>
      </Accordion>

      <FocusCard card={v.card}/>

      <Accordion type="multiple">
        <AccordionItem value="area" className="border-t">
          <AccordionTrigger className="py-3 text-xs">More ZIP evidence</AccordionTrigger>
          <AccordionContent className="text-[11px]">
            <p className="eyebrow">Area evidence</p>
            <div className="flex items-center justify-between gap-2"><h2 className="m-0 font-serif text-xl">{v.area?.heading}</h2>
              <Button variant="ghost" size="sm" className="h-7 text-[11px]" onClick={actions.focusArea}>Zoom to area<Crosshair/></Button></div>
            <div className={cn('area-metric',v.area?.combined&&'text-[23px]! leading-snug!')} style={{color:v.area?.metricColor}}>{v.area?.metric}</div>
            <p className="text-[10px] text-muted-foreground">{v.area?.metricLabel}</p>
            <div aria-live="polite">{v.area?.evidence?.map((line:string,i:number)=><p key={i} className="my-1.5">{line}</p>)}</div>
          </AccordionContent>
        </AccordionItem>
      </Accordion>
      <p className="mt-2 text-[10px] text-muted-foreground">{v.selectionLabel}</p>
    </div>}
  </aside>;
}

export function mountPanel(container:HTMLElement,store:Store,actions:any) {
  createRoot(container).render(<PlacePanel store={store} actions={actions}/>);
}
