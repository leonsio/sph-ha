import test from 'node:test';
import assert from 'node:assert/strict';
import { filterDay, SchoolContext, schoolCard, schoolDescription, schoolBadges } from '../custom_components/sph/static/school-hacks.js';
import kfg from '../custom_components/sph/static/school-hacks/kfg.js';
const lesson = {subject:'M',fach:'Mathematik',teacher:'Her',index:1,duration:2,start:'07:55',end:'09:25'};
const timetable = {entity_id:'sensor.stundenplan_maxim_mk',attributes:{klasse:'7n',kind_kürzel:'Mk',wochenkennung:'A',eigener_plan:[[lesson]]}};
const card = {config:{entity:timetable.entity_id,type:'custom:sph-stundenplan-card'}};
const hass = {states:{[timetable.entity_id]:timetable,'sensor.kfg_kollegium':{attributes:{lehrer:{HER:'Herr Beispiel',Drg:'Frau Test'}}},'sensor.vertretungsplan_7n':{attributes:{entries:[{klasse:'7n',datum:'Montag',stunde:'1-2',fach:'M',art:'Entf'}]}},'sensor.vertretungsplan':{attributes:{entries:[]}}}};
for (const [id, state] of Object.entries(hass.states)) state.entity_id = id;
const ctx = new SchoolContext(kfg,card);
for (const [badges,a,b] of [ [['A',null],['A'],[null]], [['B',null],[null],['B']], [['A','B'],['A'],['B']], [['A'],['A'],[]], [['B'],[],['B']], [[null],[null],[null]] ]) {
 test(`A/B counterpart ${badges}`,()=>{ const day=badges.map(badge=>({...lesson,badge})); assert.deepEqual(filterDay(day,'A',kfg).map(l=>l.badge),a); assert.deepEqual(filterDay(day,'B',kfg).map(l=>l.badge),b); assert.equal(filterDay(day,'',kfg),day); });
}
test('badge normalization, other badges and independent slots',()=>{
 const day=[{...lesson,badge:'(a)'},{...lesson,badge:null},{...lesson,index:3,start:'10:00',badge:'Prüfung'}];
 assert.deepEqual(filterDay(day,'a',kfg).map(l=>l.badge),['(a)','Prüfung']);
 assert.deepEqual(filterDay([{...lesson,badge:['A','B']}],'B',kfg).length,1);
});
test('teacher lookup case insensitive; source unchanged; cancellation abbreviation',()=>{
 const before=JSON.stringify(hass); const result=ctx.lesson(lesson,new Date(2026,8,7),hass);
 assert.equal(result.displayTeacher,'Herr Beispiel'); assert.equal(result.cancelled,true); assert.equal(result.changeClass,'change-entfall'); assert.equal(JSON.stringify(hass),before);
 assert.equal(ctx.teacher('unknown',hass),'unknown');
});
test('explicit missing substitution does not fall back',()=>{
 const context=new SchoolContext(kfg,{config:{...card.config,vertretungsplan_sensor:'sensor.missing'}});
 assert.equal(context.substitution(hass),null);
});
test('original subject matching and resolved replacement',()=>{
 const h=structuredClone(hass); h.states['sensor.vertretungsplan_7n'].attributes.entries=[{klasse:'7n',datum:'2026-09-07',stunde:'1',fach_original:'M',fach:'E',vertreter:'drg',art:'Vertr',raum:'200'}];
 h.states[timetable.entity_id].attributes.eigener_plan[0].push({...lesson,subject:'E',fach:'Englisch'});
 const result=ctx.lesson(lesson,new Date(2026,8,7),h);
 assert.equal(result.displaySubject,'Englisch'); assert.equal(result.displayTeacher,'Frau Test'); assert.equal(result.originalSubject,'Mathematik'); assert.equal(result.room,'200');
 assert.equal(ctx.lesson(lesson,new Date(2026,8,8),h).changeLabel,undefined);
});
test('calendar teacher details and escaping',()=>{
 const c={_school:ctx,_hass:hass}; assert.equal(schoolDescription(c,'Lehrer: her\nThema: her'),'Lehrer: Herr Beispiel\nThema: her');
 assert.ok(!schoolBadges({changeLabel:'<script>',changeClass:'x"'}).includes('<script>'));
});
class Base {
 setConfig(c){this.config=c;this.shadowRoot={innerHTML:''};}
 set hass(h){this._hass=h;this.renders=(this.renders||0)+1;}
}
test('async loading, config opt-out, stale load and unknown profiles',async()=>{
 const C=schoolCard(Base),c=new C(); c.setConfig({'school-hacks':'kfg'});c.hass=hass;assert.equal(c.renders,undefined);await c._schoolReady;assert.ok(c._school);assert.equal(c.renders,1);
 c.setConfig({});assert.equal(c._school,null);assert.equal(c._hass,hass);
 c.setConfig({'school-hacks':'kfg'});c.setConfig({});await c._schoolReady;assert.equal(c._school,null);
 c.setConfig({'school-hacks':'does-not-exist'});await c._schoolReady;assert.match(c.shadowRoot.innerHTML,/konnte nicht geladen/);
 assert.throws(()=>c.setConfig({'school-hacks':'../kfg'}));
});
test('teacher updates invalidate stable entity render cache',async()=>{
 const C=schoolCard(Base),c=new C();c.setConfig({'school-hacks':'kfg'});await c._schoolReady;c.hass=hass;c._renderedEntity=timetable;c.hass=hass;assert.equal(c._renderedEntity,timetable);
 c.hass={states:{...hass.states,'sensor.kfg_kollegium':{attributes:{lehrer:{Her:'New name'}}}}};assert.equal(c._renderedEntity,null);
});
// Load the real card modules with a minimal DOM surface to exercise their
// rendered HTML and registration order, without Home Assistant dependencies.
const registry = new Map();
globalThis.customElements = {get:name=>registry.get(name),define:(name,klass)=>{assert.ok(!registry.has(name));registry.set(name,klass);}};
globalThis.window = {customCards:[]};
globalThis.document = {createElement:()=>({set textContent(value){this.innerHTML=String(value).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');}})};
globalThis.HTMLElement = class {attachShadow(){this.shadowRoot={innerHTML:'',querySelector:()=>null};}};
for (const name of ['stundenplan-card','stundenplan-tag-card','stundenplan-grid-card']) {
 test(`normal renderer with optional school profile: ${name}`,async()=>{
  await import(`../custom_components/sph/static/sph-${name}.js?v=0.4.22`);
  const h=structuredClone(hass);
  h.states[timetable.entity_id].attributes.eigener_plan=Array.from({length:5},()=>[{...lesson,fach:'Aktives Fach',badge:'A'},{...lesson,subject:'F',fach:'Fallback Fach',badge:null}]);
  for(const prefix of ['sph']){
   const Card=registry.get(`${prefix}-${name}`),c=new Card();
   c.setConfig({entity:timetable.entity_id,'school-hacks':'kfg'});c.hass=h;await c._schoolReady;
   assert.match(c.shadowRoot.innerHTML,/Herr Beispiel/);assert.doesNotMatch(c.shadowRoot.innerHTML,/Fallback Fach/);
   c.setConfig({entity:timetable.entity_id,'school-hacks':false});
   assert.match(c.shadowRoot.innerHTML,/Fallback Fach/);assert.doesNotMatch(c.shadowRoot.innerHTML,/Herr Beispiel/);
  }
 });
}

test('legacy card types are not registered',()=>{
 for(const name of ['stundenplan-card','stundenplan-tag-card','stundenplan-grid-card']) assert.equal(registry.get(`kfg-${name}`),undefined);
});
