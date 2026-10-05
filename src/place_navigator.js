// Browser side of agent navigation: smooth scrolling, keyboard focus, a highlight on
// the item an agent is talking about, and a caption plus live region for what it said.
import {SECTIONS} from './place_navigation.mjs';

const SECTION_TARGETS={map:'mapTitle',zip_profile:'results',past_projects:'past-projects',project_charts:'project-charts',notes:'notes'};
const reducedMotion=()=>window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;

export function createNavigator(){
  // After a programmatic move the smooth scroll is still running, so trust the target briefly.
  let section='map',pinnedUntil=0,captionTimer=null;
  const pin=key=>{section=key;pinnedUntil=performance.now()+1500;};
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
    element.scrollIntoView({behavior:reducedMotion()?'auto':'smooth',block});
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
    section(){if(performance.now()>pinnedUntil)section=sectionInView();return section;},
    goTo(key){pin(key);highlight(null);bring(key==='map'?headingOf('map'):headingOf(key));if(key==='map')window.scrollTo({top:0,behavior:reducedMotion()?'auto':'smooth'});},
    // Wait for React to render the change before scrolling to the row it produced.
    focusItem(selector,key){
      pin(key);
      requestAnimationFrame(()=>requestAnimationFrame(()=>{const el=document.querySelector(selector);highlight(el);bring(el,'center');}));
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
