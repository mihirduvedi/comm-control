import {test,expect} from '@playwright/test';
import fs from 'node:fs';
import AxeBuilder from '@axe-core/playwright';
const run=()=>JSON.parse(fs.readFileSync('../.data-browser-tests/run.json','utf8'));
const h=()=>({Authorization:'Bearer '+run().operator_token,'Idempotency-Key':crypto.randomUUID()});
test.beforeEach(async({page,request})=>{
 await request.post('/api/demo/reset',{headers:h(),data:{confirmation:'RESET SYNTHETIC RUN'}});
 await request.post('/api/demo/network',{headers:h(),data:{mode:'direct',enabled:true,loss:0,paused_endpoints:[]}});
 for(const endpoint of ['/api/demo/city','/api/demo/seed'])expect((await request.post(endpoint,{headers:h(),data:{}})).ok()).toBeTruthy();
 await expect.poll(async()=>(await(await request.get('/api/control/snapshot',{headers:h()})).json()).reports.length,{timeout:20000}).toBe(8);
 await page.addInitScript((t:string)=>sessionStorage.setItem('comm-token:operator',t),run().operator_token);
 await page.setViewportSize({width:1135,height:720});await page.goto('/control');
});

test('the whole workspace scrolls together outside the map and all map controls stay reachable',async({page,request})=>{
 await request.post('/api/demo/usc',{headers:h(),data:{}});
 await expect.poll(async()=>(await(await request.get('/api/control/snapshot?world=usc',{headers:h()})).json()).reports.length,{timeout:20000}).toBe(6);
 const panel=page.getByRole('main',{name:'Selected incident overview'});
 for(const world of ['city','usc']){
  await page.goto('/control?world='+world);await expect(page.locator('.incident-context')).toBeVisible();await page.locator('.incident-context summary').click();
  await expect.poll(()=>panel.evaluate(el=>getComputedStyle(el).overflowY)).toBe('clip');
  const columns=page.locator('.incident-sidebar,.incident-main,.dispatch-detail');const before=await columns.evaluateAll(els=>els.map(el=>el.getBoundingClientRect().top));
  const toolbar=(await page.locator('.map-mode-bar').boundingBox())!;await page.mouse.move(toolbar.x+15,toolbar.y+15);await page.mouse.wheel(0,450);
  await expect.poll(()=>page.evaluate(()=>window.scrollY)).toBeGreaterThan(30);
  const after=await columns.evaluateAll(els=>els.map(el=>el.getBoundingClientRect().top));const deltas=after.map((n,i)=>before[i]-n);expect(Math.max(...deltas)-Math.min(...deltas)).toBeLessThan(2);expect(await panel.evaluate(el=>el.scrollTop)).toBe(0);
  const footer=page.locator(world==='city'?'.world-map-footer':'.usc-map-foot');await footer.scrollIntoViewIfNeeded();await expect(footer).toBeInViewport();
  await panel.focus();await page.keyboard.press('Meta+ArrowUp');await expect(panel.getByRole('heading',{level:1})).toBeInViewport();
  await page.keyboard.press('Meta+ArrowDown');await expect(footer).toBeInViewport();
 }
 const axe=await new AxeBuilder({page}).analyze();expect(axe.violations.filter(v=>['serious','critical'].includes(v.impact||'')).map(v=>({id:v.id,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))}))).toEqual([]);
 await page.setViewportSize({width:390,height:844});await page.getByRole('tab',{name:'Map',exact:true}).click();await page.locator('.usc-map-foot').scrollIntoViewIfNeeded();await expect(page.locator('.usc-map-foot')).toBeInViewport();expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
});

test('native queue drag auto-scrolls both edges, saves drop order and stops after dropping',async({page,request})=>{
 const list=page.locator('.incident-list'),rows=list.locator('.incident-row-container');await expect(rows).toHaveCount(8);
 await rows.last().scrollIntoViewIfNeeded();expect(await list.evaluate(el=>el.scrollTop)).toBeGreaterThan(100);
 const moved=await rows.last().getAttribute('data-report-id');
 const start=await rows.last().boundingBox(),bounds=await list.boundingBox();
 await page.mouse.move(start!.x+25,start!.y+25);await page.mouse.down();await page.mouse.move(start!.x+30,start!.y+15,{steps:4});await page.mouse.move(bounds!.x+70,bounds!.y+7,{steps:15});
 await expect.poll(()=>list.evaluate(el=>el.scrollTop),{timeout:10000}).toBe(0);
 const top=await rows.first().boundingBox();await page.mouse.move(top!.x+70,top!.y+18);await page.mouse.up();
 await expect.poll(async()=>(await(await request.get('/api/queue?world=city',{headers:h()})).json()).order[0]).toBe(moved);
 await expect(rows.first()).toHaveAttribute('data-report-id',moved!);
 const first=await rows.first().boundingBox();await page.mouse.move(first!.x+25,first!.y+25);await page.mouse.down();await page.mouse.move(first!.x+30,first!.y+35,{steps:4});await page.mouse.move(bounds!.x+70,bounds!.y+bounds!.height-8,{steps:15});
 await expect.poll(()=>list.evaluate(el=>Math.round(el.scrollHeight-el.clientHeight-el.scrollTop)),{timeout:10000}).toBeLessThanOrEqual(1);
 const bottom=await rows.last().boundingBox();await page.mouse.move(bottom!.x+70,Math.min(bottom!.y+30,bounds!.y+bounds!.height-10));await page.mouse.up();
 await expect.poll(async()=>(await(await request.get('/api/queue?world=city',{headers:h()})).json()).order.at(-1)).toBe(moved);
 const scroll=await list.evaluate(el=>el.scrollTop);await page.waitForTimeout(250);expect(await list.evaluate(el=>el.scrollTop)).toBe(scroll);
 await page.reload();await expect(rows.last()).toHaveAttribute('data-report-id',moved!);
});

test('selection outlines move with tabs, align after resize and respect reduced motion',async({page})=>{
 const bar=page.locator('.detail-tabs'),indicator=bar.locator('.sliding-selection');await expect(indicator).toBeVisible();const before=await indicator.boundingBox();await page.getByRole('tab',{name:'Evidence',exact:true}).click();await expect.poll(async()=>Math.round((await indicator.boundingBox())!.x)).not.toBe(Math.round(before!.x));await expect.poll(async()=>{const a=(await indicator.boundingBox())!,b=(await page.getByRole('tab',{name:'Evidence',exact:true}).boundingBox())!;return Math.abs(a.x-b.x)+Math.abs(a.width-b.width)}).toBeLessThan(2);
 expect(await indicator.evaluate(el=>getComputedStyle(el).transitionDuration)).toContain('0.24s');await page.emulateMedia({reducedMotion:'reduce'});await expect.poll(()=>indicator.evaluate(el=>getComputedStyle(el).transitionDuration)).toBe('0s');await page.getByRole('tab',{name:'Case history',exact:true}).click();await expect.poll(async()=>{const a=(await indicator.boundingBox())!,b=(await page.getByRole('tab',{name:'Case history',exact:true}).boundingBox())!;return Math.abs(a.x-b.x)}).toBeLessThan(1);
 await page.setViewportSize({width:1440,height:900});await expect.poll(async()=>{const a=(await indicator.boundingBox())!,b=(await page.getByRole('tab',{name:'Case history',exact:true}).boundingBox())!;return Math.abs(a.x-b.x)+Math.abs(a.width-b.width)}).toBeLessThan(2);
});
