import * as React from 'react';
import {createRoot} from 'react-dom/client';
import {Select,SelectContent,SelectGroup,SelectItem,SelectLabel,SelectSeparator,SelectTrigger,SelectValue} from './components/ui/select';
import {ToggleGroup,ToggleGroupItem} from './components/ui/toggle-group';
import {COMBINED_FOCUSES,SINGLE_FOCUSES,ZipCombobox} from './place_panel';
import {TimelineControls} from './place_timeline_bar';
import {cn} from './lib/utils';
import type {createPanelStore} from './place_panel';

type Store=ReturnType<typeof createPanelStore>;

// The sticky header's controls: where (city, ZIP), what (map focus) and when (timeline).
// They stay on screen while the user reads the ZIP profile and past projects below the map.
function PlaceFilters({panel,actions}:{panel:Store,actions:any}) {
  const v=React.useSyncExternalStore(panel.subscribe,panel.get);
  const ready=v.cities.length>0,isCombined=COMBINED_FOCUSES.some(([k])=>k===v.focus);
  return <div className="flex flex-wrap items-center gap-2" role="toolbar" aria-label="Map filters">
      <Select value={v.city||undefined} onValueChange={actions.setCity} disabled={!ready}>
        <SelectTrigger id="citySelect" size="sm" className="h-8 w-[140px] bg-card text-xs font-semibold" aria-label="Map city"><SelectValue placeholder="Loading…"/></SelectTrigger>
        <SelectContent>{v.cities.map((c:any)=><SelectItem key={c.id} value={c.id}>{c.label}</SelectItem>)}</SelectContent>
      </Select>
      <div className="w-[118px] [&_button]:h-8 [&_button]:text-xs"><ZipCombobox zips={v.zips} zip={v.zip} onSelect={actions.setZip} disabled={!ready}/></div>
      <Select value={v.focus} onValueChange={actions.setFocus}>
        <SelectTrigger id="focusSelect" size="sm" aria-label="Map focus" className={cn('h-8 w-[220px] border-primary bg-primary dark:bg-primary dark:hover:bg-primary text-xs font-semibold text-primary-foreground [&_svg]:text-primary-foreground! [&_svg]:opacity-80',isCombined&&'border-[var(--c-684779)] bg-[var(--c-684779)] dark:bg-[var(--c-684779)] dark:hover:bg-[var(--c-684779)]')}><SelectValue/></SelectTrigger>
        <SelectContent>
          <SelectGroup><SelectLabel>Single focus</SelectLabel>{SINGLE_FOCUSES.map(([k,l])=><SelectItem key={k} value={k}>{l}</SelectItem>)}</SelectGroup>
          <SelectSeparator/>
          <SelectGroup><SelectLabel className="text-[var(--c-59396d)]">Combined views</SelectLabel>{COMBINED_FOCUSES.map(([k,l])=><SelectItem key={k} value={k} className="text-[var(--c-59396d)] focus:bg-[var(--c-eee6f3)] focus:text-[var(--c-59396d)]">◈ {l}</SelectItem>)}</SelectGroup>
        </SelectContent>
      </Select>
      {v.focus==='income'&&<ToggleGroup type="single" variant="outline" size="sm" value={v.economic} onValueChange={(x:string)=>x&&actions.setEconomic(x)} aria-label="Economic measure">
        <ToggleGroupItem value="income" className="h-7 px-2 text-[11px]">Income</ToggleGroupItem><ToggleGroupItem value="poverty" className="h-7 px-2 text-[11px]">Poverty</ToggleGroupItem>
      </ToggleGroup>}
  </div>;
}

// Filters sit in the masthead row; the timeline gets its own full-width row beneath it.
export function mountToolbar(filters:HTMLElement,timelineRow:HTMLElement,panel:Store,actions:any,time:Store|null,timeActions:any) {
  createRoot(filters).render(<PlaceFilters panel={panel} actions={actions}/>);
  if(time)createRoot(timelineRow).render(<TimelineControls store={time} actions={timeActions}/>);else timelineRow.hidden=true;
}
