// Browser side of agent navigation: smooth scrolling, keyboard focus, a highlight on
// the item an agent is talking about, and a caption plus live region for what it said.
import {SECTIONS} from './place_navigation.mjs';

const SECTION_TARGETS={map:'mapTitle',zip_profile:'results',past_projects:'past-projects',project_charts:'project-charts',notes:'notes'};
const reducedMotion=()=>window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
// Hidden tabs never run animation frames or smooth scrolls (an agent may drive a background tab).
const visible=()=>document.visibilityState==='visible';
const scrollBehavior=()=>reducedMotion()||!visible()?'auto':'smooth';
const afterRender=fn=>visible()?requestAnimationFrame(()=>requestAnimationFrame(fn)):setTimeout(fn,30);

export function createNavigator(){
  // After an agent moves the view, keep its section until the person scrolls by hand;
  // reading the scroll position mid-animation would report the section being left.
  let section='map',pinned=false,captionTimer=null;
  const pin=key=>{section=key;pinned=true;};
  const unpin=()=>{pinned=false;};
  for(const type of ['wheel','touchmove'])window.addEventListener(type,unpin,{passive:true});
  window.addEventListener('keydown',e=>{if(['PageUp','PageDown','Home','End','ArrowUp','ArrowDown',' '].includes(e.key))unpin();});
  const caption=document.getElementById('agentCaption'),live=document.getElementById('agentLive');

  function headingOf(key){
    const root=document.getElementById(SECTION_TARGETS[key]);
    if(!root)return null;
    return root.matches('h1,h2,h3')?root:root.querySelector('h1,h2,h3')??root;
  }
  // Scroll the element into view (smoothly unless reduced motion) and move keyboard focus to it.
  function bring(element,block='start'){
    if(!element)return;
    if(!element.hasAttribute('tabindex')&&!element.matches('a,button,input,select,textarea'))element.setAttribute('tabindex','-1');
    element.scrollIntoView({behavior:scrollBehavior(),block});
    element.focus({preventScroll:true});
  }
  function highlight(element){
    document.querySelectorAll('[data-agent-focus]').forEach(e=>e.removeAttribute('data-agent-focus'));
    if(element)element.setAttribute('data-agent-focus','');
  }
  // The section nearest the top of the viewport, so "down" works after the user scrolls by hand.
  function sectionInView(){
    let best=section,bestTop=-Infinity;
    for(const {key} of SECTIONS){
      const el=document.getElementById(SECTION_TARGETS[key]);
      if(!el)continue;
      const top=el.getBoundingClientRect().top;
      if(top<=window.innerHeight*.35&&top>bestTop){best=key;bestTop=top;}
    }
    return best;
  }
  return {
    section(){if(!pinned)section=sectionInView();return section;},
    goTo(key){pin(key);highlight(null);bring(key==='map'?headingOf('map'):headingOf(key));if(key==='map')window.scrollTo({top:0,behavior:scrollBehavior()});},
    // Wait for React to render the change before scrolling to the row it produced.
    focusItem(selector,key){
      pin(key);
      afterRender(()=>{const el=document.querySelector(selector);highlight(el);bring(el,'center');});
    },
    announce(text){
      if(!text)return;
      if(live)live.textContent=text;
      if(!caption)return;
      caption.textContent=text;caption.hidden=false;
      clearTimeout(captionTimer);captionTimer=setTimeout(()=>{caption.hidden=true;},6000);
    }
  };
}
