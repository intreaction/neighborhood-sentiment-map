import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {GLOSSARY,CATEGORIES} from '../src/place_glossary.mjs';
const read=path=>readFileSync(new URL('../'+path,import.meta.url),'utf8');
test('every referenced term has a glossary entry',()=>{
 const sources=['src/place_template.html','src/place_report_view.tsx','src/place_projection.mjs','src/methods_template.html'].map(read).join('\n');
 const keys=new Set([...sources.matchAll(/data-term="([a-z_]+)"|term:'([a-z_]+)'|<Term k="([a-z_]+)"|#term-([a-z_]+)/g)].map(m=>m.slice(1).find(Boolean)));
 assert.ok(keys.size>20);
 for(const key of keys)assert.ok(GLOSSARY[key],key);
});
test('entries are complete and categorised',()=>{
 for(const [key,e] of Object.entries(GLOSSARY)){assert.ok(e.term&&e.definition,key);assert.ok(CATEGORIES[e.category],key);}
});
