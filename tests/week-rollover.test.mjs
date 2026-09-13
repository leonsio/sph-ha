import test from 'node:test';
import assert from 'node:assert/strict';
import {selectSchoolWeek,selectSchoolDay,weekForDate,visibleSchoolBadges,schoolNow,SchoolContext} from '../custom_components/sph/static/school-hacks.js';
import kfg from '../custom_components/sph/static/school-hacks/kfg.js';
const a={subject:'A-Fach',fach:'A-Unterricht',teacher:'Her',badge:'A',start:'12:25',end:'13:10',index:7,duration:1};
const b={...a,subject:'B-Fach',fach:'B-Unterricht',badge:'B',end:'15:20'};
const attrs={wochenkennung:'A',wochenbeginn:'2026-09-07',klasse:'7n',eigener_plan:Array.from({length:5},()=>[a,b]),freie_tage:[]};
const key=d=>`${d.getFullYear()}-${d.getMonth()+1}-${d.getDate()}`;
test('Friday switches at the last active lesson end, not the inactive B end',()=>{
 const before=selectSchoolWeek(attrs,kfg,new Date(2026,8,11,13,9,59));
 assert.equal(key(before.monday),'2026-9-7');assert.equal(before.week,'A');assert.equal(before.days[4][0].subject,'A-Fach');
 const after=selectSchoolWeek(attrs,kfg,new Date(2026,8,11,13,10));
 assert.equal(key(after.monday),'2026-9-14');assert.equal(after.week,'B');assert.deepEqual(after.days[4],[b]);
});
test('weekend and Monday keep B; stale data uses the reference week',()=>{
 for(const date of [new Date(2026,8,12),new Date(2026,8,13),new Date(2026,8,14,8)]){
  const view=selectSchoolWeek(attrs,kfg,date);assert.equal(key(view.monday),'2026-9-14');assert.equal(view.week,'B');
 }
 assert.equal(weekForDate({...attrs,wochenkennung:'B',wochenbeginn:'2026-09-14'},new Date(2026,8,14)),'B');
});
test('B to A waits for the later last B lesson',()=>{
 const source={...attrs,wochenkennung:'B'};
 assert.equal(selectSchoolWeek(source,kfg,new Date(2026,8,11,13,10)).week,'B');
 assert.equal(selectSchoolWeek(source,kfg,new Date(2026,8,11,15,20)).week,'A');
});
test('missing Friday and missing end time use deterministic fallbacks',()=>{
 const empty={...attrs,eigener_plan:attrs.eigener_plan.map((day,i)=>i===4?[]:day)};
 assert.equal(selectSchoolWeek(empty,kfg,new Date(2026,8,10,23,59)).week,'A');
 assert.equal(selectSchoolWeek(empty,kfg,new Date(2026,8,11)).week,'B');
 const missing={...attrs,eigener_plan:Array.from({length:5},()=>[{...a,end:''}])};
 assert.equal(selectSchoolWeek(missing,kfg,new Date(2026,8,11,23,59)).week,'A');
 assert.equal(selectSchoolWeek(missing,kfg,new Date(2026,8,12)).week,'B');
});
test('unmasked plan restores next week lessons and free dates apply to target dates',()=>{
 const source={...attrs,eigener_grundplan:attrs.eigener_plan,eigener_plan:[[],[],[],[],[]],freie_tage:['2026-09-07','2026-09-15']};
 const view=selectSchoolWeek(source,kfg,new Date(2026,8,13));
 assert.deepEqual(view.days[0],[b]);assert.deepEqual(view.days[1],[]);
 assert.deepEqual(source.eigener_plan,[[],[],[],[],[]]);
});
test('DST, year boundary, unknown badge, and no profile',()=>{
 assert.equal(weekForDate({wochenkennung:'A',wochenbeginn:'2026-10-19'},new Date(2026,9,26)),'B');
 assert.equal(weekForDate({wochenkennung:'B',wochenbeginn:'2026-12-28'},new Date(2027,0,4)),'A');
 assert.equal(selectSchoolWeek({...attrs,wochenkennung:null},kfg,new Date(2026,8,13)).week,'');
 const view=selectSchoolWeek(attrs,undefined,new Date(2026,8,13));
 assert.equal(key(view.monday),'2026-9-7');assert.deepEqual(view.days,attrs.eigener_plan);
});
test('only A/B lesson badges are hidden; data and other badges remain',()=>{
 const card={_school:{profile:kfg}};
 for(const value of ['A','(b)',['A','B'],null,''])assert.deepEqual(visibleSchoolBadges(card,value),[]);
 assert.deepEqual(visibleSchoolBadges(card,'A; Prüfung'),[' Prüfung']);
 assert.equal(visibleSchoolBadges({},'A'),'A');assert.equal(a.badge,'A');
});
test('daily view also selects B lessons and header after Friday and Sunday',()=>{
 for(const date of [new Date(2026,8,11,13,10),new Date(2026,8,13)]){
 const selected=selectSchoolDay(attrs,kfg,date);assert.equal(key(selected.date),'2026-9-14');assert.equal(selected.week,'B');assert.deepEqual(selected.lessons,[b]);
 }
});
test('school time zone determines Friday closing time',()=>{
 const now=schoolNow({_hass:{config:{time_zone:'Europe/Berlin'}}},new Date('2026-09-11T11:10:00Z'));
 assert.equal(now.getHours(),13);assert.equal(selectSchoolWeek(attrs,kfg,now).week,'B');
});
test('undated weekday substitutions are not replayed into next week',()=>{
 const context=new SchoolContext(kfg,{});
 assert.equal(context._dateMatch({datum:'Montag'},new Date(2026,8,14),0,new Date(2026,8,7)),false);
 assert.equal(context._dateMatch({datum:'14.09.2026'},new Date(2026,8,14),0,new Date(2026,8,7)),true);
});
const registry=new Map();
globalThis.customElements={get:n=>registry.get(n),define:(n,c)=>registry.set(n,c)};
globalThis.document={createElement:()=>({set textContent(v){this.innerHTML=String(v);}})};
globalThis.HTMLElement=class{attachShadow(){this.shadowRoot={innerHTML:'',querySelector:()=>null};}};
let tick,clears=0;
globalThis.window={customCards:[],setInterval:fn=>{tick=fn;return 1;},clearInterval:()=>{clears++;}};
for(const name of ['sph-stundenplan-card','sph-stundenplan-grid-card']){
 test(`${name} updates dates, filtering and headings on the clock; grid keeps scroll container`,async(t)=>{
  t.mock.timers.enable({apis:['Date'],now:new Date(2026,8,11,13,9,59).getTime()});
  await import(`../custom_components/sph/static/${name}.js?v=0.4.24`);
  const c=new (registry.get(name))();c.isConnected=true;c.setConfig({entity:'sensor.plan','school-hacks':'kfg'});
  c.hass={states:{'sensor.plan':{entity_id:'sensor.plan',attributes:attrs}}};await c._schoolReady;
  assert.match(c.shadowRoot.innerHTML,/(?:Woche|Schulwoche) A/);assert.match(c.shadowRoot.innerHTML,/A-Unterricht/);assert.doesNotMatch(c.shadowRoot.innerHTML,/>\(?A\)?<\/span>/);
  const isGrid=name.includes('grid');
  if(isGrid){
   assert.equal((c.shadowRoot.innerHTML.match(/Schulwoche A/g)||[]).length,1);
   assert.doesNotMatch(c.shadowRoot.innerHTML.split('<thead>')[1].split('</thead>')[0],/Woche|Schulwoche/);
   assert.match(c.shadowRoot.innerHTML,/text-align:right/);
   assert.ok(c.shadowRoot.innerHTML.indexOf('class="school-week"')<c.shadowRoot.innerHTML.indexOf('class="table-wrap"'));
  }
  const wrap={innerHTML:'',scrollLeft:120},weekLine={textContent:'Schulwoche A',hidden:false};
  if(isGrid)c.shadowRoot.querySelector=selector=>selector==='.table-wrap'?wrap:selector==='.school-week'?weekLine:null;
  t.mock.timers.setTime(new Date(2026,8,11,13,10).getTime());tick();
  const html=name.includes('grid')?wrap.innerHTML:c.shadowRoot.innerHTML;
  assert.match(html,/14\.9\.2026/);
  if(isGrid){assert.equal(weekLine.textContent,'Schulwoche B');assert.equal(weekLine.hidden,false);assert.doesNotMatch(html,/Woche|Schulwoche/);}
  else assert.match(html,/Woche B/);
  assert.match(html,/B-Unterricht/);assert.doesNotMatch(html,/A-Unterricht/);assert.equal(wrap.scrollLeft,120);
  if(isGrid){
   c.setConfig({entity:'sensor.plan','school-hacks':false});assert.equal(weekLine.hidden,true);assert.equal(weekLine.textContent,'');
   c.setConfig({entity:'sensor.plan','school-hacks':'kfg'});await c._schoolReady;assert.equal(weekLine.textContent,'Schulwoche B');assert.equal(weekLine.hidden,false);
  }
  const oldClears=clears;c.disconnectedCallback();assert.ok(clears>oldClears);
 });
}
