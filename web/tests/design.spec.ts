import {test,expect} from '@playwright/test';
import fs from 'node:fs';
import AxeBuilder from '@axe-core/playwright';
const run=()=>JSON.parse(fs.readFileSync('../.data-browser-tests/run.json','utf8'));
const h=()=>({Authorization:'Bearer '+run().operator_token,'Idempotency-Key':crypto.randomUUID()});
test.beforeEach(async({page,request})=>{
 expect((await request.post('/api/demo/reset',{headers:h(),data:{confirmation:'RESET SYNTHETIC RUN'}})).ok()).toBeTruthy();
 await request.post('/api/demo/network',{headers:h(),data:{mode:'direct',enabled:true,loss:0,paused_endpoints:[]}});
 for(const url of ['/api/demo/city','/api/demo/usc'])expect((await request.post(url,{headers:h(),data:{}})).ok()).toBeTruthy();
 await expect.poll(async()=>(await(await request.get('/api/control/snapshot',{headers:h()})).json()).reports.length,{timeout:20000}).toBe(10);
 await page.addInitScript((t:string)=>sessionStorage.setItem('comm-token:operator',t),run().operator_token);
});
async function noSevere(page:import('@playwright/test').Page,name:string){
 const a=await new AxeBuilder({page}).analyze();fs.writeFileSync('../evidence/v6-4-'+name+'-axe.json',JSON.stringify(a.violations,null,2));expect(a.violations.filter(v=>['serious','critical'].includes(v.impact||'')).map(v=>v.id)).toEqual([]);
}
test('one type family, readable resource information, integrated selects and restored semantic categories',async({page,request})=>{
 for(const path of ['/control?world=city','/resources?world=city','/resources?world=usc','/sessions?world=usc','/demo?world=usc','/setup?world=usc']){
  await page.goto(path);await expect(page.locator(path.startsWith('/resources')?'.resources-page':path.startsWith('/control')?'.incident-visible-tags':'.admin-title')).toBeVisible();await page.evaluate(()=>document.fonts.ready);
  const fonts=await page.locator('h1,h2,.brand strong,main p,main button,main select').evaluateAll(els=>els.filter(el=>el.getClientRects().length).map(el=>getComputedStyle(el).fontFamily));expect(fonts.every(f=>f.includes('Nunito Sans'))).toBeTruthy();
  if(path.startsWith('/resources')){
   const sizes=await page.locator('.resource-area p,.resource-area small,.resource-total p,.resource-situation p,.usc-work-row p,.usc-work-row>small,.usc-asset-grid small,.campus-roster small').evaluateAll(els=>els.filter(el=>el.getClientRects().length).map(el=>parseFloat(getComputedStyle(el).fontSize)));expect(sizes.length).toBeGreaterThan(2);expect(Math.min(...sizes)).toBeGreaterThanOrEqual(13);
  }
  const selects=await page.locator('select').evaluateAll(els=>els.filter(el=>el.getClientRects().length).map(el=>({appearance:getComputedStyle(el).appearance,padding:parseFloat(getComputedStyle(el).paddingRight),image:getComputedStyle(el).backgroundImage})));for(const select of selects){expect(select.appearance).toBe('none');expect(select.padding).toBeGreaterThanOrEqual(40);expect(select.image).toContain('svg')}
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
  if(path.startsWith('/sessions'))await page.screenshot({path:'../evidence/v6-4-sessions.png',fullPage:true});
  if(path==='/resources?world=city'){await noSevere(page,'city-resources');await page.screenshot({path:'../evidence/v6-4-city-resources.png',fullPage:true})}
  if(path==='/resources?world=usc'){await noSevere(page,'usc-resources');await page.screenshot({path:'../evidence/v6-4-usc-resources.png',fullPage:true})}
 }
 await page.goto('/control?world=city');const brief=page.locator('.incident-visible-tags');await expect(brief.locator('.category-badge')).toBeVisible();
 const colors=await page.locator('.incident-row .category-badge').evaluateAll(els=>els.map(el=>getComputedStyle(el).backgroundColor));expect(new Set(colors).size).toBeGreaterThanOrEqual(3);
 await page.screenshot({path:'../evidence/v6-4-city-workspace.png'});await noSevere(page,'city-workspace');
 const usc=(await(await request.get('/api/usc/operations',{headers:h()})).json());expect(usc.tickets).toHaveLength(5);expect(usc.tickets.every((t:any)=>t.route?.distance_m>50)).toBeTruthy();
 await page.goto('/control?world=usc');await expect(page.locator('.usc-map-canvas')).toBeVisible();await expect.poll(async()=>page.locator('.usc-map-canvas svg g[aria-label$=" route"] polyline').count()).toBeGreaterThan(0);
 const contained=await page.locator('.usc-map-canvas').evaluate(el=>{const svg=el.querySelector('svg')!;const [x,y,w,h]=svg.getAttribute('viewBox')!.split(' ').map(Number);return [...el.querySelectorAll('g[aria-label$=" route"] polyline')].every(p=>p.getAttribute('points')!.split(' ').every(pair=>{const [px,py]=pair.split(',').map(Number);return px>=x&&px<=x+w&&py>=y&&py<=y+h}))});expect(contained).toBeTruthy();
 await expect(page.locator('.usc-response')).toContainText('Lab Safety');await page.screenshot({path:'../evidence/v6-4-usc-workspace.png'});await noSevere(page,'usc-workspace');
});
test('mobile resources and sessions keep readable text without overflow, with native selects and source access',async({page})=>{
 await page.setViewportSize({width:390,height:844});
 for(const path of ['/resources?world=city','/resources?world=usc','/sessions?world=usc']){
  await page.goto(path);await expect(page.locator(path.startsWith('/resources')?'.resources-page':'.admin-title')).toBeVisible();expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
  await noSevere(page,path.includes('sessions')?'mobile-sessions':path.includes('usc')?'mobile-usc-resources':'mobile-city-resources');
  await page.screenshot({path:'../evidence/v6-4-'+(path.includes('sessions')?'sessions':path.includes('usc')?'usc-resources':'city-resources')+'-mobile.png',fullPage:true});
 }
 await page.goto('/resources?world=usc');await page.getByRole('combobox',{name:'Campus building',exact:true}).selectOption('usc-sgm');
 await expect(page.locator('.usc-work-row')).toHaveCount(1);await page.locator('.usc-work-row').click();await expect(page.getByRole('dialog',{name:'Campus work item'})).toContainText('220');await expect(page.getByRole('link',{name:'Open original report'})).toHaveCount(2);
});
test('empty sessions use the same framed form and clear state, and create a working reporting session',async({page,request})=>{
 await request.post('/api/demo/reset',{headers:h(),data:{confirmation:'RESET SYNTHETIC RUN'}});
 await page.goto('/sessions?world=usc');await expect(page.locator('.table-empty')).toContainText('Add a reporter above');
 await page.getByRole('textbox',{name:'Reporter name',exact:true}).fill('Campus demo operator');await page.getByRole('button',{name:'Create session',exact:true}).click();await expect(page.locator('.session-line')).toContainText('Campus demo operator');
 await expect(page.getByRole('button',{name:'Open field view',exact:true})).toBeEnabled();
 expect((await(await request.get('/api/control/snapshot?world=usc',{headers:h()})).json()).sessions).toHaveLength(1);
 expect((await(await request.get('/api/control/snapshot?world=city',{headers:h()})).json()).sessions).toHaveLength(0);
 await page.screenshot({path:'../evidence/v6-4-session-created.png'});
});
