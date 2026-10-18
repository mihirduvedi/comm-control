import {test,expect} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import fs from 'node:fs';
test.describe.configure({mode:'serial'});
const run=()=>JSON.parse(fs.readFileSync('../.data-browser-tests/run.json','utf8'));
const h=()=>({Authorization:'Bearer '+run().operator_token,'Idempotency-Key':crypto.randomUUID()});
async function auth(page:any){await page.addInitScript((t:string)=>sessionStorage.setItem('comm-token:operator',t),run().operator_token)}
test.beforeAll(async({request})=>{await request.post('/api/demo/reset',{headers:h(),data:{confirmation:'RESET SYNTHETIC RUN'}});await request.post('/api/demo/network',{headers:h(),data:{mode:'direct',enabled:true,loss:0,paused_endpoints:[]}})});

test('city incidents become categorized briefs, real maps, automatic assignments and review tasks',async({page})=>{
 await auth(page);await page.goto('/control');await page.getByRole('button',{name:'Load city demo',exact:true}).click();
 await expect(page.getByRole('button',{name:/Los Angeles City Hall.*Smoke/}).first()).toBeVisible({timeout:20000});await page.getByRole('button',{name:/Los Angeles City Hall.*Smoke/}).first().click();
 await expect(page.getByRole('heading',{name:'Smoke reported',exact:true})).toBeVisible();await expect(page.getByText('Assigned to this incident',{exact:true})).toBeVisible();await expect(page.locator('.travel-estimate')).toContainText(/mi/);expect(await page.locator('.travel-estimate').textContent()).not.toMatch(/\bkm\b/);await expect(page.locator('.communications-section')).not.toHaveAttribute('open','');await expect(page.getByText('Confirm occupancy',{exact:true})).toBeVisible();
 await expect(page.getByRole('region',{name:'Real-world incident map'})).toBeVisible();await expect(page.locator('.leaflet-tile-loaded').first()).toBeVisible({timeout:15000});
 await expect(page.locator('.live-clock time')).toBeVisible();const old=await page.locator('.live-clock time').textContent();await expect.poll(()=>page.locator('.live-clock time').textContent()).not.toBe(old);
 const snapshot=await(await page.request.get('/api/control/snapshot',{headers:h()})).json();expect(snapshot.operations.assignments.filter((a:any)=>a.state!=='released').length).toBeGreaterThanOrEqual(3);expect(snapshot.operations.closures[0].label).toContain('Main Street');
 if(await page.getByRole('button',{name:'Dismiss message'}).isVisible())await page.getByRole('button',{name:'Dismiss message'}).click();
 await page.screenshot({path:'../evidence/v4-operator-1440.png',fullPage:true});await page.setViewportSize({width:1280,height:800});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();await page.screenshot({path:'../evidence/v4-operator-1280.png',fullPage:true});
 await page.getByRole('tab',{name:'Evidence',exact:true}).click();await page.getByRole('button',{name:'Source',exact:true}).click();await expect(page.getByText('“There is smoke near City Hall.”',{exact:true})).toBeVisible();
});

test('reported route blockage changes actual graph path and demo announcement requires approval',async({page})=>{
 await auth(page);await page.goto('/control');await page.getByRole('button',{name:/Los Angeles City Hall.*Smoke/}).first().click();
 const before=await(await page.request.get('/api/control/snapshot',{headers:h()})).json();const report=before.reports.find((r:any)=>r.category==='fire');const assignment=before.operations.assignments.find((a:any)=>a.report_id===report.id);const option=assignment.route.routes[0],step=option.steps[0],blocked=step.edge_ids[Math.floor(step.edge_ids.length/2)];
 await page.getByText('Route & alternatives',{exact:true}).click();await page.getByRole('button',{name:'Report a blockage on this route'}).click();await page.getByLabel('Source or reason').fill('Synthetic road closure for route verification');await page.getByRole('button',{name:'Save closure & recalculate'}).click();
 await expect.poll(async()=>{const s=await(await page.request.get('/api/control/snapshot',{headers:h()})).json();return s.operations.config.closure_revision}).toBeGreaterThan(before.operations.config.closure_revision);
 const after=await(await page.request.get('/api/control/snapshot',{headers:h()})).json();const rerouted=after.operations.assignments.find((a:any)=>a.id===assignment.id);expect(rerouted.route.routes.length).toBeGreaterThan(0);expect(rerouted.route.routes.every((r:any)=>!r.edge_ids.includes(blocked))).toBeTruthy();expect(rerouted.route.routes[0].edge_ids).not.toEqual(option.edge_ids);
 await page.locator('.communications-section > summary').click();await page.getByRole('button',{name:/(Prepare|Review) announcement/,exact:false}).click();await expect(page.getByRole('button',{name:'Publish to demo board'})).not.toBeVisible();await page.getByLabel('Exact message',{exact:true}).fill('Demonstration: a reported smoke incident near City Hall is under review. This is not an official public alert.');await page.getByRole('button',{name:'Approve wording & audience'}).click();await page.getByRole('button',{name:'Publish to demo board'}).click();await expect(page.locator('.published-advisory strong').filter({hasText:'Published to Public demo board'})).toBeVisible();
 await page.screenshot({path:'../evidence/v4-rerouted-plan.png',fullPage:true});
});

test('categorized workspace reflows, exposes keyboard controls and passes serious axe checks',async({page})=>{
 await auth(page);await page.goto('/control');await page.keyboard.press('Tab');await expect(page.getByRole('link',{name:'Skip to workspace'})).toBeFocused();await page.getByRole('button',{name:/Los Angeles City Hall.*Smoke/}).first().click();
 const result=await new AxeBuilder({page}).analyze();fs.writeFileSync('../evidence/v4-accessibility.json',JSON.stringify(result.violations,null,2));expect(result.violations.filter(v=>['critical','serious'].includes(v.impact||'')).map(v=>({id:v.id,targets:v.nodes.map(n=>n.target)}))).toEqual([]);
 await page.setViewportSize({width:800,height:900});await page.getByRole('tab',{name:'Details',exact:true}).click();await expect(page.getByRole('button',{name:'Respond to Alex',exact:true})).toBeVisible();await page.getByRole('button',{name:'Respond to Alex',exact:true}).click();await expect(page.getByRole('dialog')).toBeVisible();await page.keyboard.press('Escape');
 await page.setViewportSize({width:390,height:844});await page.getByRole('tab',{name:'Map',exact:true}).click();expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();await page.getByRole('button',{name:'Fit incident',exact:true}).click();await page.locator('.world-map-footer').scrollIntoViewIfNeeded();await expect(page.locator('.leaflet-control-attribution')).toBeInViewport();await page.waitForTimeout(500);await page.screenshot({path:'../evidence/v4-mobile-map.png',fullPage:true});
});


test('automation switches persist and remain independent of the transport',async({page})=>{
 await auth(page);await page.goto('/setup');const setting=page.getByRole('switch',{name:'Automatic resource assignment'});await expect(setting).toBeChecked();await setting.click();await expect(setting).not.toBeChecked();await page.reload();await expect(setting).not.toBeChecked();await setting.click();await expect(setting).toBeChecked();await page.getByRole('link',{name:'Simulator',exact:true}).click();await page.getByRole('button',{name:'Queue city demo',exact:true}).click();await expect(page.getByRole('status')).toBeVisible();
});


test('field device accuracy uses feet without changing the reported event location',async({page,context,request})=>{
 const state=await(await request.get('/api/control/snapshot',{headers:h()})).json();const report=state.reports.find((r:any)=>r.category==='fire');const launch=await(await request.get('/api/sessions/'+report.session_id+'/launch',{headers:h()})).json();await context.grantPermissions(['geolocation']);await context.setGeolocation({latitude:34.05,longitude:-118.24,accuracy:10});await page.setViewportSize({width:390,height:844});await page.goto(launch.url);await page.getByRole('button',{name:'Show map',exact:false}).click();await page.getByRole('button',{name:'Show my device location',exact:true}).click();await expect(page.getByText('Your device location is accurate to about 33 ft. Your reported location stays the same.',{exact:true})).toBeVisible();await expect(page.getByText('Los Angeles City Hall',{exact:true})).toBeVisible();await expect(page.locator('.field-real-map .leaflet-tile-loaded').first()).toBeVisible({timeout:15000});await page.waitForTimeout(500);await page.screenshot({path:'../evidence/v4-field-feet.png',fullPage:true});
});
