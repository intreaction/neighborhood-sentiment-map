import * as React from 'react';
import {createRoot} from 'react-dom/client';
import {GLOSSARY,CATEGORIES} from './place_glossary.mjs';
import {Dialog,DialogContent,DialogDescription,DialogFooter,DialogHeader,DialogTitle} from './components/ui/dialog';
import {Badge} from './components/ui/badge';

const EVENT='place:term';
export const openTerm=(key:string)=>window.dispatchEvent(new CustomEvent(EVENT,{detail:key}));

function TermDialog() {
  const [key,setKey]=React.useState<string|null>(null);
  React.useEffect(()=>{
    const onTerm=(e:Event)=>setKey((e as CustomEvent<string>).detail);
    window.addEventListener(EVENT,onTerm);
    return ()=>window.removeEventListener(EVENT,onTerm);
  },[]);
  const entry=key?(GLOSSARY as Record<string,any>)[key]:null;
  return <Dialog open={!!entry} onOpenChange={open=>{if(!open)setKey(null);}}>
    {entry&&<DialogContent className="sm:max-w-lg">
      <DialogHeader className="gap-3">
        <Badge variant="secondary" className="uppercase tracking-wider text-[10px]">{(CATEGORIES as Record<string,string>)[entry.category]}</Badge>
        <DialogTitle className="font-serif text-2xl font-normal">{entry.term}</DialogTitle>
        <DialogDescription className="text-sm leading-relaxed text-foreground">{entry.definition}</DialogDescription>
      </DialogHeader>
      {entry.formula&&<div className="border-t pt-3">
        <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">How it is calculated</p>
        <code className="inline-block rounded-md bg-muted px-2.5 py-1.5 font-mono text-[13px] leading-relaxed">{entry.formula}</code>
      </div>}
      {entry.caution&&<div className="border-t pt-3">
        <p className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">Read with care</p>
        <p className="text-xs leading-relaxed text-muted-foreground">{entry.caution}</p>
      </div>}
      <DialogFooter className="sm:justify-start">
        <a className="text-xs font-semibold text-primary underline-offset-4 hover:underline" href={`methods.html#term-${key}`}>Methodology &amp; glossary →</a>
      </DialogFooter>
    </DialogContent>}
  </Dialog>;
}

// One dialog serves every [data-term] trigger, whether rendered by React or plain HTML.
export function initTerms(container:HTMLElement) {
  createRoot(container).render(<TermDialog/>);
  document.addEventListener('click',event=>{
    const trigger=(event.target as Element).closest?.('[data-term]') as HTMLElement|null;
    if(trigger){event.preventDefault();openTerm(trigger.dataset.term!);}
  });
}
