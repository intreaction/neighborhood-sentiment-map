import {CATEGORIES,glossaryEntries} from './place_glossary.mjs';
const esc=text=>String(text).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

const entries=glossaryEntries();
document.getElementById('glossaryList').innerHTML=Object.entries(CATEGORIES).map(([category,label])=>`<h3>${esc(label)}</h3><dl class="glossary">${
  entries.filter(e=>e.category===category).map(e=>`<div id="term-${esc(e.key)}"><dt>${esc(e.term)}</dt><dd><p>${esc(e.definition)}</p>${e.formula?`<code>${esc(e.formula)}</code>`:''}${e.caution?`<p class="glossary-caution">${esc(e.caution)}</p>`:''}</dd></div>`).join('')
}</dl>`).join('');
// The list renders after load, so re-apply a #term-… hash and highlight the target.
function highlight(){
  document.querySelector('.glossary-target')?.classList.remove('glossary-target');
  const target=location.hash.startsWith('#term-')&&document.getElementById(location.hash.slice(1));
  if(target){target.scrollIntoView();target.classList.add('glossary-target');}
}
highlight();
addEventListener('hashchange',highlight);
