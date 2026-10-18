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
 await page.goto('/control?world=city');
});

test('switching worlds isolates the queue, counts, map, resources and sessions across reload and history',async({page,request})=>{
 const queue=page.getByRole('complementary',{name:'Incident queue'});await expect(queue.getByRole('button',{name:/Union Station/})).toBeVisible();
 await expect(queue).not.toContainText('Michelson');
 await page.getByRole('group',{name:'Operating workspace',exact:true}).getByRole('button',{name:'USC campus',exact:true}).click();
 await expect(queue).toContainText('Michelson');await expect(queue).not.toContainText('Union Station');await expect(queue).not.toContainText('City Hall');
 await expect(page.getByRole('region',{name:'Dispatch status'})).toContainText(/5\s*open incidents/);
 await expect(page.getByRole('region',{name:'USC campus map'})).toBeVisible();
 await page.reload();await expect(queue).toContainText('Michelson');await expect(queue).not.toContainText('Union Station');
 await page.getByRole('navigation',{name:'Main navigation'}).getByRole('link',{name:'Resources',exact:true}).click();
 await expect(page.getByRole('heading',{name:'USC facilities',exact:true})).toBeVisible();
 await page.getByRole('navigation',{name:'Main navigation'}).getByRole('link',{name:'Sessions',exact:true}).click();
 await expect(page.locator('.session-line')).toHaveCount(6);await expect(page.locator('.session-table')).not.toContainText('Alex Rivera');
 await page.goBack();await expect(page.getByRole('heading',{name:'USC facilities',exact:true})).toBeVisible();
 await page.getByRole('group',{name:'Operating workspace',exact:true}).getByRole('button',{name:'Downtown LA',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Resources',exact:true})).toBeVisible();
 await page.getByRole('navigation',{name:'Main navigation'}).getByRole('link',{name:'Workspace',exact:true}).click();
 await expect(queue.getByRole('button',{name:/Union Station/})).toBeVisible();await expect(queue).not.toContainText('Michelson');
 const usc=(await(await request.get('/api/control/snapshot?world=usc',{headers:h()})).json()).reports[0];await page.goto('/control?report='+usc.id);await expect(page).toHaveURL(/world=usc/);await expect(queue).toContainText('Michelson');await expect(queue).not.toContainText('Union Station');
});

test('city and USC maps are generous near-square canvases and wheel zoom without scrolling the panel',async({page})=>{
 for(const world of ['city','usc']){
  await page.goto('/control?world='+world);await page.getByRole('button',{name:world==='city'?/Union Station.*One injured/:/Michelson.*Possible gas/}).click();
  const canvas=page.locator(world==='city'?'.world-map-canvas':'.usc-map-canvas');await expect(canvas).toBeVisible();
  const box=(await canvas.boundingBox())!;expect(box.height).toBeGreaterThan(530);expect(box.width/box.height).toBeLessThan(1.38);expect(box.width/box.height).toBeGreaterThan(.7);
  const panel=page.getByRole('main',{name:'Selected incident overview'}),scroll=await panel.evaluate(el=>el.scrollTop);
  const before=world==='usc'?await canvas.locator(':scope > svg').getAttribute('viewBox'):await canvas.locator('.leaflet-tile-container').last().getAttribute('style');
  await page.mouse.move(box.x+box.width*.6,Math.min(box.y+box.height*.45,850));await page.mouse.wheel(0,-180);
  await expect.poll(async()=>world==='usc'?await canvas.locator(':scope > svg').getAttribute('viewBox'):await canvas.locator('.leaflet-tile-container').last().getAttribute('style')).not.toBe(before);
  expect(await panel.evaluate(el=>el.scrollTop)).toBe(scroll);
  if(world==='usc'){
   const zoomed=(await canvas.locator(':scope > svg').getAttribute('viewBox'))!.split(' ').map(Number);await page.mouse.wheel(0,100);await expect.poll(async()=>Number((await canvas.locator(':scope > svg').getAttribute('viewBox'))!.split(' ')[2])).toBeGreaterThan(zoomed[2]);
  }
  await page.getByRole('button',{name:'Expand map',exact:true}).click();await expect(page.getByRole('button',{name:'Restore workspace',exact:true})).toBeVisible();await page.screenshot({path:'../evidence/v6-3-expanded-check.png'});const expanded=(await canvas.boundingBox())!;expect(expanded.width*expanded.height).toBeGreaterThan(box.width*box.height);await page.getByRole('button',{name:'Restore workspace',exact:true}).click();
  if(world==='usc')await expect.poll(async()=>(await canvas.locator('.usc-building-caption rect').first().boundingBox())!.width).toBeGreaterThan(50);
  await page.screenshot({path:'../evidence/v6-3-'+world+'-workspace.png'});
 }
 const a=await new AxeBuilder({page}).analyze();expect(a.violations.filter(v=>['serious','critical'].includes(v.impact||'')).map(v=>v.id)).toEqual([]);
});

test('top navigation keeps one shared outline that slides across real pages, with keyboard and reduced motion',async({page})=>{
 const nav=page.getByRole('navigation',{name:'Main navigation'}),indicator=nav.locator('.sliding-selection');await expect(indicator).toBeVisible();
 await indicator.evaluate(el=>{el.setAttribute('data-continuity-check','same-node')});const before=(await indicator.boundingBox())!;
 await nav.getByRole('link',{name:'Resources',exact:true}).click();await expect(page.getByRole('heading',{name:'Resources',exact:true})).toBeVisible();await expect(indicator).toHaveAttribute('data-continuity-check','same-node');
 await expect.poll(async()=>Math.round((await indicator.boundingBox())!.x)).not.toBe(Math.round(before.x));
 await expect.poll(async()=>{const a=(await indicator.boundingBox())!,b=(await nav.getByRole('link',{name:'Resources',exact:true}).boundingBox())!;return Math.abs(a.x-b.x)+Math.abs(a.width-b.width)}).toBeLessThan(2);
 await page.emulateMedia({reducedMotion:'reduce'});await expect.poll(()=>indicator.evaluate(el=>getComputedStyle(el).transitionDuration)).toBe('0s');
 await nav.getByRole('link',{name:'Sessions',exact:true}).focus();await page.keyboard.press('Enter');await expect(page.getByRole('heading',{name:'Field sessions',exact:true})).toBeVisible();
 await page.goBack();await expect(page.getByRole('heading',{name:'Resources',exact:true})).toBeVisible();
});

test('warmer body type loads locally and the mobile map, workspace picker and live call remain usable',async({page})=>{
 await page.goto('/control?world=usc');await page.setViewportSize({width:390,height:844});
 await expect(page.getByRole('combobox',{name:'Operating workspace',exact:true})).toBeVisible();
 await page.evaluate(()=>document.fonts.ready);const font=await page.locator('body').evaluate(el=>({family:getComputedStyle(el).fontFamily,ready:document.fonts.check('14px "Nunito Sans"')}));expect(font.family).toContain('Nunito Sans');expect(font.ready).toBeTruthy();
 await page.getByRole('tab',{name:'Map',exact:true}).click();const canvas=page.locator('.usc-map-canvas');const b=(await canvas.boundingBox())!;expect(Math.abs(b.width/b.height-1)).toBeLessThan(.05);
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
 await page.screenshot({path:'../evidence/v6-3-usc-mobile.png'});
 const a=await new AxeBuilder({page}).analyze();fs.writeFileSync('../evidence/v6-3-mobile-axe.json',JSON.stringify(a.violations,null,2));expect(a.violations.filter(v=>['serious','critical'].includes(v.impact||'')).map(v=>v.id)).toEqual([]);
 await page.getByRole('button',{name:'Start voice report',exact:true}).click();await expect(page.getByRole('region',{name:'Live call intake'})).toBeVisible();await page.getByRole('button',{name:'Close live call',exact:true}).click();
 await page.getByRole('combobox',{name:'Operating workspace',exact:true}).selectOption('city');await page.getByRole('tab',{name:'Queue',exact:true}).click();await expect(page.getByRole('complementary',{name:'Incident queue'})).toContainText('Union Station');await expect(page.getByRole('complementary',{name:'Incident queue'})).not.toContainText('Michelson');
});
