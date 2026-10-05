import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {FAMILIES,PROJECT_FAMILY,projectEffects,familyEstimate,familySummary,leaveOneOut} from '../src/place_projection.mjs';
const period=(n,s,a,r)=>({n_reviews:n,mean_sentiment:s,access_friction_share:a,public_realm_complaint_share:r});
const project=(id,nearPost,farPost)=>({id,project:id,opening:'2015-01-01',periods:{near:{pre:period(100,.5,.02,.02),post:nearPost},far:{pre:period(1000,.5,.02,.02),post:farPost}}});

test('effects subtract the comparison-area change',()=>{
 const [row]=projectEffects({projects:[project('lafitte',period(300,.6,.01,.03),period(2000,.55,.02,.02))]});
 assert.ok(Math.abs(row.effects.activity-Math.log(1.5))<1e-12);
 assert.ok(Math.abs(row.effects.sentiment-.05)<1e-12);
 assert.ok(Math.abs(row.effects.access+1)<1e-9);
 assert.ok(Math.abs(row.effects.realm-1)<1e-9);
});
test('excluded and unmapped projects are left out',()=>{
 const p=period(100,.5,.02,.02);
 const rows=projectEffects({projects:[project('lafitte',p,{...p,n_reviews:1000}),project('water-works-park',p,{...p,n_reviews:1000}),project('unknown',p,{...p,n_reviews:1000})]},['water-works-park']);
 assert.deepEqual(rows.map(r=>r.id),['lafitte']);
});
const row=(family,v)=>({family,effects:{activity:v,sentiment:v,access:v,realm:v}});
test('family means shrink toward the overall mean by the prior weight',()=>{
 const rows=[row('trail',1),row('trail',1),row('civic',-1),row('civic',-1)];
 const e=familyEstimate(rows,'trail',2).outcomes.activity;
 assert.equal(e.overall_mean,0);assert.equal(e.family_mean,1);assert.equal(e.pooled,.5);
 assert.equal(familyEstimate(rows,'transit',2).outcomes.activity.pooled,0);
});
test('leave-one-out never uses the held-out project',()=>{
 const rows=[row('trail',1),row('trail',1),row('civic',-1),row('civic',-1)];
 const r=leaveOneOut(rows,0).activity;
 assert.equal(r.family_mae,0);assert.ok(r.overall_mae>1);
});
test('family summary reports plain means, ranges and how many projects improved',()=>{
 const rows=[row('trail',Math.log(1.5)),row('trail',0),row('civic',-1)];
 const s=familySummary(rows,'trail').outcomes;
 assert.ok(Math.abs(s.activity.mean-100*(Math.exp(Math.log(1.5)/2)-1))<1e-9);
 assert.ok(Math.abs(s.activity.max-50)<1e-9);
 assert.equal(s.activity.better,1);
 assert.equal(s.access.better,0);
 assert.equal(familySummary(rows,'all').n,3);
});
test('every shipped historical project has a family',()=>{
 const history=JSON.parse(readFileSync(new URL('../web/place-history.json',import.meta.url)));
 for(const p of history.projects)assert.ok(FAMILIES[PROJECT_FAMILY[p.id]],p.id);
 assert.equal(projectEffects(history,['water-works-park']).length,10);
});
