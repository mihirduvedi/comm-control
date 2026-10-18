import {test,expect} from '@playwright/test';
import fs from 'node:fs';
import AxeBuilder from '@axe-core/playwright';
const run=()=>JSON.parse(fs.readFileSync('../.data-browser-tests/run.json','utf8'));
const h=()=>({Authorization:'Bearer '+run().operator_token,'Idempotency-Key':crypto.randomUUID()});
test.beforeEach(async({page,request})=>{
 await request.post('/api/demo/reset',{headers:h(),data:{confirmation:'RESET SYNTHETIC RUN'}});
 await request.post('/api/demo/network',{headers:h(),data:{mode:'direct',enabled:true,loss:0,paused_endpoints:[]}});
 for(const endpoint of ['/api/demo/city','/api/demo/usc'])expect((await request.post(endpoint,{headers:h(),data:{}})).ok()).toBeTruthy();
 await expect.poll(async()=>(await(await request.get('/api/control/snapshot',{headers:h()})).json()).reports.length,{timeout:20000}).toBe(10);
 await page.addInitScript((t:string)=>sessionStorage.setItem('comm-token:operator',t),run().operator_token);
});
async function report(request:any,place:string,text:string,kind='fire'){
 const session=await(await request.post('/api/sessions',{headers:h(),data:{name:'Queue test caller',world:'city'}})).json();const headers={Authorization:'Bearer '+session.token,'Idempotency-Key':crypto.randomUUID()};
 const draft=await(await request.post('/api/drafts/manual',{headers,data:{session_id:session.id,text,claims:[{kind,value:text,excerpt:text,location_text:place,location_role:'event',assertion:'asserted',count:-1}]}})).json();
 const result=await request.post('/api/drafts/'+draft.id+'/send',{headers:{...headers,'Idempotency-Key':crypto.randomUUID()},data:{version:draft.version,reviewed:true}});expect(result.ok()).toBeTruthy();const id=(await result.json()).messages[0].id;
 await expect.poll(async()=>(await(await request.get('/api/control/snapshot?world=city',{headers:h()})).json()).reports.some((r:any)=>r.id===id)).toBeTruthy();return id;
}
async function noSevere(page:any,name:string){const a=await new AxeBuilder({page}).analyze();fs.writeFileSync('../evidence/v6-6-'+name+'-axe.json',JSON.stringify(a.violations,null,2));expect(a.violations.filter(v=>['serious','critical'].includes(v.impact||'')).map(v=>({id:v.id,nodes:v.nodes.map(n=>n.target)}))).toEqual([])}

test('locating preserves Leaflet clipping and commits a real event location',async({page,request})=>{
 const id=await report(request,'','Help is needed at an unknown location.','request');await page.goto('/control?world=city&report='+id);
 const canvas=page.locator('.world-map-canvas');await expect(canvas).toHaveClass(/leaflet-container/);
 for(let i=0;i<2;i++){
  await page.getByRole('button',{name:'Locate this incident',exact:true}).click();await expect(canvas).toHaveClass(/leaflet-container/);await expect(page.locator('.world-map')).toHaveClass(/picking/);
  expect(await canvas.evaluate(el=>getComputedStyle(el).overflow)).toBe('hidden');
  expect(await page.locator('.incident-main h1').evaluate(el=>{const b=el.getBoundingClientRect();return !document.elementFromPoint(b.left+5,b.top+b.height/2)?.closest('.leaflet-pane')})).toBeTruthy();
  if(i===0)await page.getByRole('button',{name:'Cancel location',exact:true}).click();
 }
 await page.screenshot({path:'../evidence/v6-6-location-picker.png',fullPage:true});
 // Use the actual local search and confirmation API; no hosted geocoder or model.
 await page.getByLabel('Search places and intersections').fill('City Hall');await page.getByRole('button',{name:'Find place',exact:true}).click();await page.getByRole('button',{name:'Los Angeles City Hall landmark from OpenStreetMap',exact:true}).click();
 await page.getByLabel('How did you confirm this location?').fill('Synthetic test: caller confirmed City Hall.');await page.getByRole('button',{name:'Confirm & update response plan',exact:true}).click();
 await expect(page.getByRole('list',{name:'Report to response status'})).toContainText('Location mapped');await expect(canvas).toHaveClass(/leaflet-container/);
 const saved=(await(await request.get('/api/control/snapshot?world=city',{headers:h()})).json()).reports.find((r:any)=>r.id===id);expect(saved.brief.location.label).toBe('Los Angeles City Hall');
});

test('timeline markers share one axis and incident removal is reversible',async({page,request})=>{
 const snap=await(await request.get('/api/control/snapshot?world=city',{headers:h()})).json(),r=snap.reports.find((r:any)=>r.category==='fire');await page.goto('/control?world=city&report='+r.id);await page.getByRole('tab',{name:'Case history',exact:true}).click();const timeline=page.getByRole('list',{name:'Case timeline'});await expect(timeline.locator('li').first()).toBeVisible();
 const centers=await timeline.locator('li').evaluateAll(els=>els.map(el=>{const dot=getComputedStyle(el,'::before'),line=getComputedStyle(el,'::after'),time=el.querySelector('time')!.getBoundingClientRect(),box=el.getBoundingClientRect();return {axis:Math.abs(parseFloat(dot.left)-parseFloat(line.left)),vertical:Math.abs(box.top+parseFloat(dot.top)-(time.top+time.height/2))}}));expect(centers.every(c=>c.axis<.6&&c.vertical<.6)).toBeTruthy();expect(await timeline.locator('li').last().evaluate(el=>getComputedStyle(el,'::after').display)).toBe('none');await page.screenshot({path:'../evidence/v6-6-case-timeline.png',fullPage:true});
 await page.getByRole('button',{name:'Remove incident',exact:true}).click();await page.getByRole('checkbox',{name:/I reviewed this incident/}).check();await page.getByRole('button',{name:'Remove from queue',exact:true}).click();await expect(page.locator('.incident-row-container[data-report-id="'+r.id+'"]')).toHaveCount(0);await expect(page.getByRole('button',{name:'Archived (1)',exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Archived (1)',exact:true}).click();await page.getByRole('button',{name:/Los Angeles City Hall.*Archived/}).click();await page.getByRole('button',{name:'Restore incident',exact:true}).click();await page.getByRole('button',{name:'Restore to Closed',exact:true}).click();await page.getByRole('button',{name:'Closed',exact:true}).click();await expect(page.locator('.incident-row-container[data-report-id="'+r.id+'"]')).toBeVisible();
 const saved=(await(await request.get('/api/control/snapshot?world=city',{headers:h()})).json()).reports.find((x:any)=>x.id===r.id);expect(saved.archived_at).toBeUndefined();expect(saved.status).toBe('resolved');
});

test('an explicit voice start is blank while a refresh can recover an interrupted call',async({page,request})=>{
 const old=await(await request.post('/api/demo/intake',{headers:h(),data:{world:'city'}})).json();
 // Synthetic recovery payload tests UI restoration without calling a speech model.
 await page.route('**/api/demo/intake/current?world=city',route=>route.fulfill({json:{intake:{...old,transcript:'Previous synthetic call that must not load into a new intake.'}}}));
 await page.goto('/control?world=city&live=1');await expect(page.getByLabel('Call transcript',{exact:true})).toHaveValue(/Previous synthetic/);
 await page.getByRole('button',{name:'Start voice report',exact:true}).click();await expect(page.getByRole('button',{name:'Start microphone',exact:true})).toBeEnabled();await expect(page.getByLabel('Call transcript',{exact:true})).toHaveCount(0);expect((await(await request.get('/api/demo/intake/'+old.id,{headers:h()})).json()).state).toBe('cancelled');
 await page.getByRole('button',{name:'Type live call instead',exact:true}).click();await expect(page.getByLabel('Call transcript',{exact:true})).toHaveValue('');await page.getByLabel('Call transcript',{exact:true}).fill('New unsent test call.');await page.getByRole('button',{name:'Start voice report',exact:true}).click();await expect(page.getByRole('button',{name:'Start microphone',exact:true})).toBeEnabled();await expect(page.getByLabel('Call transcript',{exact:true})).toHaveCount(0);await page.screenshot({path:'../evidence/v6-6-fresh-intake.png',fullPage:true});
});

test('city unit queue persists, reorders, advances and manually reassigns actual allocations',async({page,request})=>{
 const one=await report(request,'Grand Park','Fire reported at Grand Park.'),two=await report(request,'Union Station','Fire reported near Union Station.');
 const state=await(await request.get('/api/dispatch-queues?world=city',{headers:h()})).json(),hall=state.targets.find((t:any)=>t.location==='Los Angeles City Hall'&&t.capabilities.includes('fire')),unit=state.providers.find((p:any)=>p.current?.location.includes('Grand Park'));const next=hall.id;expect(unit).toBeTruthy();await page.goto('/resources?world=city');const row=page.locator('.provider-queue').filter({has:page.locator('summary strong',{hasText:unit.name})});await row.locator('summary').click();
 for(const id of [next,two]){await row.getByLabel('Next stop for '+unit.name,{exact:true}).selectOption(id);await row.getByRole('button',{name:'Add to queue',exact:true}).click();await expect(row.locator('.provider-stops li')).toHaveCount(id===next?1:2)}
 await row.getByRole('button',{name:/Move Fire reported at Union Station up/}).click();await expect(row.locator('.provider-stops li').first()).toContainText('Union Station');await page.reload();await row.locator('summary').click();await expect(row.locator('.provider-stops li').first()).toContainText('Union Station');
 await row.getByRole('button',{name:'Finish assignment & take next',exact:true}).click();await page.getByRole('button',{name:'Finish and check next stop',exact:true}).click();await expect(row.locator('.provider-current')).toContainText('Union Station');
 await row.getByRole('button',{name:'Reassign',exact:true}).click();await page.getByLabel('New assignment',{exact:true}).selectOption(next);await page.getByLabel('Reason for reassignment',{exact:true}).fill('Move an additional unit to City Hall.');await page.getByRole('button',{name:'Confirm reassignment',exact:true}).click();await expect(row.locator('.provider-current')).toContainText('City Hall');await expect(row.locator('.provider-stops li')).toHaveCount(0);await noSevere(page,'city-queues');await page.screenshot({path:'../evidence/v6-6-city-queues.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});await row.scrollIntoViewIfNeeded();await expect(row.getByRole('button',{name:'Reassign',exact:true})).toBeVisible();expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();await page.screenshot({path:'../evidence/v6-6-city-queues-mobile.png'});
});

test('USC team queue finishes work and advances to a received campus job',async({page,request})=>{
 const campus=await(await request.get('/api/usc/operations',{headers:h()})).json(),building=campus.site.buildings.find((b:any)=>b.code==='SSC');const created=await request.post('/api/usc/reports',{headers:h(),data:{building_id:building.id,reporter:'Campus queue test',text:'A gas odor is reported. Please send lab safety.'}});expect(created.ok()).toBeTruthy();const message=(await created.json()).message_id;
 await expect.poll(async()=>(await(await request.get('/api/usc/operations',{headers:h()})).json()).tickets.some((t:any)=>t.report_ids.includes(message))).toBeTruthy();const targets=await(await request.get('/api/dispatch-queues?world=usc',{headers:h()})).json(),job=targets.targets.find((t:any)=>t.report_id===message),unit=targets.providers.find((p:any)=>p.current?.location.includes('Michelson'));
 await page.goto('/resources?world=usc');const row=page.locator('.provider-queue').filter({has:page.locator('summary strong',{hasText:unit.name})});await row.locator('summary').click();await row.getByLabel('Next stop for '+unit.name,{exact:true}).selectOption(job.id);await row.getByRole('button',{name:'Add to queue',exact:true}).click();await expect(row.locator('.provider-stops li')).toHaveCount(1);await row.getByRole('button',{name:'Finish work & take next',exact:true}).click();await page.getByRole('button',{name:'Finish and check next stop',exact:true}).click();await expect(row.locator('.provider-current')).toContainText(building.name);await expect(row.locator('.provider-stops li')).toHaveCount(0);await noSevere(page,'usc-queues');await page.screenshot({path:'../evidence/v6-6-usc-queues.png',fullPage:true});
});


test('reporting sessions stay usable beyond ten and grouped source reports share map routes',async({page,request})=>{
 for(let i=0;i<8;i++)expect((await request.post('/api/sessions',{headers:h(),data:{name:'Extra test caller '+i,world:'city'}})).ok()).toBeTruthy();
 await page.goto('/sessions?world=city');await expect(page.getByText('12 of 100 reporting sessions in this workspace',{exact:true})).toBeVisible();await expect(page.getByRole('button',{name:'Create session',exact:true})).toBeEnabled();await page.getByLabel('Reporter name',{exact:true}).fill('Thirteenth caller');await page.getByRole('button',{name:'Create session',exact:true}).click();await expect(page.getByText('13 of 100 reporting sessions in this workspace',{exact:true})).toBeVisible();
 const id=await report(request,'City Hall','Another caller reports fire at City Hall.');await page.goto('/control?world=city&report='+id);await expect(page.getByRole('heading',{name:'Fire reported',exact:true})).toBeVisible();await expect.poll(async()=>Number(await page.locator('.world-map').getAttribute('data-route-count'))).toBeGreaterThan(0);await expect(page.getByRole('list',{name:'Report to response status'})).toContainText('Route ready');
});
