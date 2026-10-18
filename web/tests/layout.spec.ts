import {test,expect} from '@playwright/test';
import fs from 'node:fs';
import AxeBuilder from '@axe-core/playwright';
const run=()=>JSON.parse(fs.readFileSync('../.data-browser-tests/run.json','utf8'));
const h=()=>({Authorization:'Bearer '+run().operator_token,'Idempotency-Key':crypto.randomUUID()});
test.beforeEach(async({page,request})=>{
 await request.post('/api/demo/reset',{headers:h(),data:{confirmation:'RESET SYNTHETIC RUN'}});
 await request.post('/api/demo/network',{headers:h(),data:{mode:'direct',enabled:true,loss:0,paused_endpoints:[]}});
 for(const url of ['/api/demo/city','/api/demo/usc'])expect((await request.post(url,{headers:h(),data:{}})).ok()).toBeTruthy();
 await expect.poll(async()=>(await(await request.get('/api/control/snapshot',{headers:h()})).json()).reports.length,{timeout:20000}).toBe(10);
 await page.addInitScript((t:string)=>sessionStorage.setItem('comm-token:operator',t),run().operator_token);
});
test('wider queue, inset borderless tabs and document scrolling move the entire workspace in both worlds',async({page})=>{
 for(const world of ['city','usc']){
  await page.goto('/control?world='+world);await expect(page.locator('.incident-visible-tags')).toBeVisible();await expect(page.getByRole('list',{name:'Report to response status'})).toContainText(world==='city'?'Demo report':'Manual report');await page.evaluate(()=>document.fonts.ready);
  expect((await page.locator('.incident-sidebar').boundingBox())!.width).toBeGreaterThanOrEqual(290);
  expect((await page.locator('.world-map-canvas,.usc-map-canvas').boundingBox())!.width).toBeGreaterThan(680);
  const tabs=await page.locator('.detail-tabs').evaluate(el=>({top:parseFloat(getComputedStyle(el).paddingTop),line:getComputedStyle(el).borderBottomWidth}));expect(tabs.top).toBeGreaterThanOrEqual(14);expect(tabs.line).toBe('0px');
  await expect(page.locator('.queue-order-copy')).toContainText('Drag to arrange');await expect(page.locator('.queue-order-copy')).not.toContainText('·');await expect(page.locator('.incident-row-heading time')).toHaveCount(0);await expect(page.locator('.incident-row-caller time').first()).toBeVisible();
  const columns=page.locator('.incident-sidebar,.incident-main,.dispatch-detail'),before=await columns.evaluateAll(els=>els.map(el=>el.getBoundingClientRect().top));
  const tabBox=(await page.locator('.detail-tabs').boundingBox())!;await page.mouse.move(tabBox.x+tabBox.width/2,tabBox.y+15);await page.mouse.wheel(0,350);await expect.poll(()=>page.evaluate(()=>scrollY)).toBeGreaterThan(30);
  const after=await columns.evaluateAll(els=>els.map(el=>el.getBoundingClientRect().top)),delta=after.map((n,i)=>before[i]-n);expect(Math.max(...delta)-Math.min(...delta)).toBeLessThan(2);
  expect(await page.locator('.incident-main').evaluate(el=>el.scrollTop)).toBe(0);
  await page.keyboard.press('Meta+ArrowUp');await expect.poll(()=>page.evaluate(()=>scrollY)).toBe(0);
  const a=await new AxeBuilder({page}).analyze();fs.writeFileSync('../evidence/v6-5-'+world+'-axe.json',JSON.stringify(a.violations,null,2));expect(a.violations.filter(v=>['serious','critical'].includes(v.impact||'')).map(v=>v.id)).toEqual([]);
  await page.screenshot({path:'../evidence/v6-5-'+world+'-workspace.png',fullPage:true});
 }
 await page.goto('/review?world=usc');await expect(page.locator('.review-row').first()).toBeVisible();
 const border=await page.locator('.review-row').first().evaluate(el=>{const s=getComputedStyle(el);return [s.borderTopWidth,s.borderRightWidth,s.borderBottomWidth,s.borderLeftWidth]});expect(border).toEqual(['1px','1px','1px','1px']);await page.screenshot({path:'../evidence/v6-5-review.png',fullPage:true});
});
test('voice report is the primary entry and the automation trail reflects real assignment and location state',async({page,request})=>{
 await page.goto('/control?world=usc');const journey=page.getByRole('list',{name:'Report to response status'});await expect(journey).toContainText('Location mapped');await expect(journey).toContainText('Team assigned');await expect(journey).toContainText('Route ready');await expect(journey).toContainText('Manual report');await expect(journey).not.toContainText('Voice parsed');
 const session=await(await request.post('/api/sessions',{headers:h(),data:{name:'Unknown location caller',world:'city'}})).json();const headers={Authorization:'Bearer '+session.token,'Idempotency-Key':crypto.randomUUID()};
 const draft=await(await request.post('/api/drafts/manual',{headers,data:{session_id:session.id,text:'Someone needs medical help. I do not know the address.',claims:[{kind:'observation',value:'Medical help, address unknown',excerpt:'Someone needs medical help.',location_text:'',location_role:'event',assertion:'asserted',count:1}]}})).json();
 const sent=await request.post('/api/drafts/'+draft.id+'/send',{headers:{...headers,'Idempotency-Key':crypto.randomUUID()},data:{version:draft.version,reviewed:true}});expect(sent.ok()).toBeTruthy();const id=(await sent.json()).messages[0].id;
 await expect.poll(async()=>(await(await request.get('/api/control/snapshot?world=city',{headers:h()})).json()).reports.some((r:any)=>r.id===id)).toBeTruthy();
 await page.goto('/control?world=city&report='+id);await expect(journey).toContainText('Manual report');await expect(journey).toContainText('Confirm location');await expect(journey).toContainText('Awaiting team');await expect(journey).toContainText('Route pending');await expect(journey).not.toContainText('Team assigned');
 await page.goto('/sessions?world=usc');await page.getByRole('button',{name:'Start voice report',exact:true}).click();await expect(page.getByRole('region',{name:'Live call intake'})).toBeVisible();await expect(page.getByRole('heading',{name:'One call starts the response',exact:true})).toBeVisible();await expect(page.locator('.usc-map-preview')).toHaveCount(1);await expect(page.locator('.usc-map-preview g[role=img]')).toHaveCount(0);await expect(page.locator('.usc-map-preview .live-map-note')).toContainText('Not reviewed');await expect(page.locator('.live-demo-example')).toContainText('SGM');await expect(page.locator('.live-demo-example')).not.toContainText('City Hall');await expect(page.locator('.live-intake-intro')).toContainText('team assignment');await page.screenshot({path:'../evidence/v6-5-voice-entry.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});await expect(page.getByRole('region',{name:'Live call intake'})).toBeVisible();await expect(page.getByRole('tab',{name:'Details',exact:true})).toHaveAttribute('aria-selected','true');await expect.poll(async()=>{const a=(await page.locator('.dispatch-mobile-tabs .sliding-selection').boundingBox())!,b=(await page.getByRole('tab',{name:'Details',exact:true}).boundingBox())!;return Math.abs(a.x-b.x)+Math.abs(a.y-b.y)+Math.abs(a.width-b.width)}).toBeLessThan(2);expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();await expect(page.getByRole('button',{name:'Start voice report',exact:true})).toBeVisible();await page.screenshot({path:'../evidence/v6-5-voice-mobile.png',fullPage:true});await page.getByRole('tab',{name:'Map',exact:true}).click();await expect(page.getByRole('region',{name:'Live call intake'})).not.toBeVisible();await page.getByRole('button',{name:'Start voice report',exact:true}).click();await expect(page.getByRole('region',{name:'Live call intake'})).toBeVisible();
});
