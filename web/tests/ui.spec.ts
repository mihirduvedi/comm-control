import {test,expect} from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';
import AxeBuilder from '@axe-core/playwright';
test.describe.configure({mode:'serial'});
const run=()=>JSON.parse(fs.readFileSync(path.resolve('../.data-browser-tests/run.json'),'utf-8'));
async function auth(page:any){await page.addInitScript((token:string)=>sessionStorage.setItem('comm-token:operator',token),run().operator_token)}

test.beforeAll(async({request})=>{
 const headers={Authorization:'Bearer '+run().operator_token,'Idempotency-Key':crypto.randomUUID()};
 await request.post('/api/demo/reset',{headers,data:{confirmation:'RESET SYNTHETIC RUN'}});
 await request.post('/api/demo/network',{headers,data:{mode:'direct',enabled:true,loss:0,paused_endpoints:[]}});
});

test('populated workspace source-to-map and responsive layout',async({page})=>{
 await auth(page);await page.goto('/control');
 await page.request.post('/api/demo/seed',{headers:{Authorization:'Bearer '+run().operator_token,'Idempotency-Key':crypto.randomUUID()},data:{}});
 await expect(page.getByRole('button',{name:/(East Warehouse|Seeley G. Mudd Building).*(Smoke|smoke)/}).first()).toBeVisible({timeout:15000});
 await page.getByRole('button',{name:/(East Warehouse|Seeley G. Mudd Building).*(Smoke|smoke)/}).first().click();
 await page.locator('.incident-context summary').click();await expect(page.locator('.incident-brief').getByText(/Room position unknown|Occupancy inside unknown/)).toBeVisible();
 await page.getByRole('tab',{name:'Evidence',exact:true}).click();await page.getByRole('button',{name:'Source',exact:true}).click();
 await page.getByRole('button',{name:'“The north gate is blocked.” Access. sender-supplied excerpt',exact:true}).click();
 await expect(page.getByRole('region',{name:'Real-world incident map'})).toBeVisible();await expect(page.getByRole('button',{name:'Fictional site',exact:true})).toHaveCount(0);await expect(page.getByRole('button',{name:'“The north gate is blocked.” Access. sender-supplied excerpt',exact:true})).toBeVisible();
 if(await page.getByRole('button',{name:'Dismiss message'}).isVisible())await page.getByRole('button',{name:'Dismiss message'}).click();await page.locator('.inspector').evaluate(el=>el.scrollTop=0);await page.screenshot({path:'../evidence/operator-1440.png',fullPage:true});
 await page.setViewportSize({width:1280,height:800});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
 await page.screenshot({path:'../evidence/operator-1280.png',fullPage:true});
 await page.setViewportSize({width:800,height:900});
 await expect(page.getByRole('tab',{name:'Map',exact:true})).toBeVisible();
 await page.getByRole('tab',{name:'Details',exact:true}).click();
 await expect(page.locator('.inspector').getByText('Room position unknown',{exact:true})).toBeVisible();
});

test('manual reviewed instruction reaches recipient, persists before receipt and Cannot follow returns',async({page,context})=>{
 await auth(page);await page.goto('/control');
 await page.getByRole('button',{name:/(East Warehouse|Seeley G. Mudd Building).*(Smoke|smoke)/}).first().click();
 await page.getByRole('button',{name:'Respond to Alex',exact:true}).click();
 await page.getByRole('button',{name:'Use an exact written instruction'}).click();
 await page.getByLabel('Operator’s exact words').fill('Stay outside. Do not use the north gate. Is anyone still inside?');
 await page.getByRole('button',{name:'Use these words'}).click();
 await page.getByRole('button',{name:'Review & approve',exact:true}).click();
 await page.getByRole('button',{name:'Send to Alex Rivera',exact:true}).click();
 const snapshot=await (await page.request.get('/api/control/snapshot',{headers:{Authorization:'Bearer '+run().operator_token}})).json();
 const latestMessage=snapshot.messages.at(-1);
 const alex=snapshot.sessions.find((s:any)=>s.display_name==='Alex Rivera');
 const link=await (await page.request.get('/api/sessions/'+alex.id+'/launch',{headers:{Authorization:'Bearer '+run().operator_token}})).json();
 const field=await context.newPage();await field.setViewportSize({width:390,height:844});await field.goto(link.url);
 await expect.poll(async()=>{if(await field.getByRole('button',{name:/New instruction available/}).isVisible())await field.getByRole('button',{name:/New instruction available/}).click();return field.locator('[data-message-id="'+latestMessage.id+'"]').isVisible()}).toBeTruthy();
 await expect(field.getByText('Stay outside. Do not use the north gate. Is anyone still inside?',{exact:true})).toBeVisible({timeout:15000});
 await expect(field.getByText('Saved on this device',{exact:true})).toBeVisible({timeout:15000});
 await field.getByRole('button',{name:'Cannot follow',exact:true}).click();await field.getByLabel('What makes this hard to follow? (optional)').fill('Smoke is reaching us.');await field.getByRole('button',{name:'Send Cannot follow'}).click();
 await expect(field.getByRole('status').filter({hasText:'Response queued'})).toBeVisible();
 await field.screenshot({path:'../evidence/recipient-390.png',fullPage:true});
 expect(await field.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
 if(await page.getByRole('button',{name:/Messages & history/}).getAttribute('aria-expanded')==='false')await page.getByRole('button',{name:/Messages & history/}).click();
 await expect(page.getByText('Smoke is reaching us.',{exact:true})).toBeVisible({timeout:15000});
 await field.close();
});

test('core controls are keyboard reachable and no serious accessibility violations',async({page})=>{
 await auth(page);await page.goto('/control');
 await page.keyboard.press('Tab');await expect(page.getByRole('link',{name:'Skip to workspace'})).toBeFocused();
 await expect(page.getByRole('complementary',{name:'Incident queue',exact:true})).toBeVisible();
 const result=await new AxeBuilder({page}).analyze();
 fs.writeFileSync('../evidence/accessibility.json',JSON.stringify(result.violations,null,2));
 expect(result.violations.filter(v=>['critical','serious'].includes(v.impact||'')).map(v=>({id:v.id,targets:v.nodes.map(n=>n.target)}))).toEqual([]);
});

test('operator count correction and approximate location retain source evidence',async({page})=>{
 await auth(page);await page.goto('/control');await page.getByRole('button',{name:/(East Warehouse|Seeley G. Mudd Building).*(Smoke|smoke)/}).first().click();
 await page.getByRole('tab',{name:'Evidence',exact:true}).click();await page.getByRole('button',{name:'Correct people outside',exact:true}).click();await page.getByLabel('Interpretation',{exact:true}).fill('3 people outside');await page.getByLabel('Count (blank = unknown)',{exact:true}).fill('3');await page.getByLabel('Reason',{exact:true}).fill('Synthetic operator count correction');await page.getByRole('button',{name:'Save correction',exact:true}).click();await expect(page.locator('.inspector').getByText('3 people outside',{exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Correct smoke',exact:true}).click();await page.getByRole('button',{name:'Locate at a USC building',exact:true}).click();await page.getByLabel('USC building',{exact:true}).selectOption('usc-sgm');await page.getByLabel('Basis for the location',{exact:true}).fill('Synthetic operator relocation; original warehouse source retained.');await page.getByRole('button',{name:'Confirm campus location',exact:true}).click();await expect(page.locator('.incident-key-facts')).toContainText('Seeley G. Mudd');
 await page.getByRole('tab',{name:'Evidence',exact:true}).click();if(await page.getByRole('button',{name:'Source',exact:true}).getAttribute('aria-expanded')==='false')await page.getByRole('button',{name:'Source',exact:true}).click();await expect(page.getByText('“There\'s smoke coming out of the electrical room.”',{exact:true})).toBeVisible();await page.screenshot({path:'../evidence/operator-estimate.png',fullPage:true});
});

test('service failure disables sends, retains snapshot and reconnects',async({page})=>{
 await auth(page);await page.goto('/control?world=usc');await page.getByRole('button',{name:/(East Warehouse|Seeley G. Mudd Building).*(Smoke|smoke)/}).first().click();await expect(page.getByRole('button',{name:'Respond to Alex',exact:true})).toBeVisible();await page.route('**/api/**',route=>route.abort('internetdisconnected'));
 await expect(page.getByRole('alert').filter({hasText:'Local service unavailable'})).toBeVisible({timeout:8000});await expect(page.getByRole('button',{name:'Respond to Alex',exact:true})).toBeDisabled();await page.getByRole('tab',{name:'Evidence',exact:true}).click();await expect(page.getByRole('heading',{name:'Reported facts'})).toBeVisible();
 await page.unroute('**/api/**');await page.getByRole('button',{name:'Reconnect',exact:true}).click();await expect(page.getByRole('button',{name:'Respond to Alex',exact:true})).toBeEnabled();
 await page.setViewportSize({width:720,height:500});await page.getByRole('tab',{name:'Details',exact:true}).click();await expect(page.getByRole('button',{name:'Respond to Alex',exact:true})).toBeVisible();expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();await page.getByRole('button',{name:'Respond to Alex',exact:true}).click();await expect(page.getByRole('dialog')).toBeVisible();await page.keyboard.press('Escape');await expect(page.getByRole('dialog')).not.toBeVisible();
});

test('microphone denial and pending audio survive refresh with explicit recovery',async({page})=>{
 const h={Authorization:'Bearer '+run().operator_token,'Idempotency-Key':crypto.randomUUID()};const s=await(await page.request.post('/api/sessions',{headers:h,data:{name:'Recovery verification'}})).json();const launch=await(await page.request.get('/api/sessions/'+s.id+'/launch',{headers:h})).json();
 await page.addInitScript(()=>{navigator.mediaDevices.getUserMedia=()=>Promise.reject(new DOMException('Denied','NotAllowedError'))});await page.goto(launch.url);await page.getByRole('button',{name:'Record report',exact:true}).click();await expect(page.getByRole('alert').filter({hasText:'Microphone permission was denied'})).toBeVisible();
 await page.route('**/api/utterances',route=>route.abort());await page.getByLabel('Audio file').setInputFiles('../fixtures/warehouse.aiff');await expect(page.getByRole('button',{name:'Retry saved recording',exact:true})).toBeVisible();await page.reload();await expect(page.getByRole('button',{name:'Retry saved recording',exact:true})).toBeVisible();await page.getByRole('button',{name:'Discard saved recording',exact:true}).click();await expect(page.getByRole('button',{name:'Retry saved recording',exact:true})).not.toBeVisible();
});

test('reviewed replacement takes effect after destination delivery and keeps original history',async({page,context,request})=>{
 await auth(page);await page.goto('/control?world=usc');await page.getByRole('button',{name:/(East Warehouse|Seeley G. Mudd Building).*(Smoke|smoke)/}).first().click();await page.getByRole('button',{name:/Messages & history/}).click();await page.getByRole('button',{name:'Replace this instruction',exact:true}).last().click();await expect(page.getByText('Replacement: the earlier instruction stays current until this revision reaches the recipient.')).toBeVisible();
 await page.getByRole('button',{name:'Use an exact written instruction'}).click();const text='Stay outside. Use the south gate only when the supervisor confirms.';await page.getByLabel('Operator’s exact words').fill(text);await page.getByRole('button',{name:'Use these words'}).click();
 const h={Authorization:'Bearer '+run().operator_token,'Idempotency-Key':crypto.randomUUID()};let snap=await(await request.get('/api/control/snapshot',{headers:h})).json();const alex=snap.sessions.find((s:any)=>s.display_name==='Alex Rivera');const launch=await(await request.get('/api/sessions/'+alex.id+'/launch',{headers:h})).json();const field=await context.newPage();await field.goto(launch.url);await expect(field.getByText('Saved on this device',{exact:true})).toBeVisible();
 await request.post('/api/demo/network',{headers:h,data:{enabled:false}});await page.getByRole('button',{name:'Review & approve',exact:true}).click();await page.getByRole('button',{name:'Send to Alex Rivera',exact:true}).click();await expect(field.getByText(text,{exact:true})).not.toBeVisible();
 await request.post('/api/demo/network',{headers:h,data:{enabled:true}});await expect(field.getByRole('button',{name:/New instruction available/})).toBeVisible({timeout:15000});await field.getByRole('button',{name:/New instruction available/}).click();await expect(field.getByText(text,{exact:true})).toBeVisible();
 await field.getByRole('button',{name:'Sent reports & earlier instructions'}).click();await expect(field.getByText('Stay outside. Do not use the north gate. Is anyone still inside?',{exact:true})).toBeVisible();await field.close();
});

test('session, simulator, review and setup entry points render and drive real state',async({page})=>{
 await auth(page);await page.goto('/sessions');await page.getByLabel('Reporter name').fill('UI session check');await page.getByRole('button',{name:'Create session',exact:true}).click();await expect(page.getByText('UI session check',{exact:true})).toBeVisible();await page.screenshot({path:'../evidence/sessions.png',fullPage:true});
 await page.getByRole('link',{name:'Simulator',exact:true}).click();await page.getByRole('button',{name:'Pause link',exact:true}).click();await expect(page.getByRole('button',{name:'Restore link',exact:true})).toBeVisible();await page.getByRole('button',{name:'Restore link',exact:true}).click();await page.getByRole('button',{name:'Show delivery log',exact:true}).click();await expect(page.locator('.trace-table')).toBeVisible();await page.screenshot({path:'../evidence/simulator.png',fullPage:true});
 await page.getByRole('link',{name:'Review',exact:true}).click();const download=page.waitForEvent('download');await page.getByRole('button',{name:'Export received evidence'}).click();expect((await download).suggestedFilename()).toBe('Comm_Control_Evidence.json');await page.getByRole('button',{name:'New test',exact:true}).click();await expect(page.getByRole('button',{name:'Start new test',exact:true})).toBeDisabled();await page.keyboard.press('Escape');await page.screenshot({path:'../evidence/review.png',fullPage:true});
 await page.getByRole('link',{name:'Setup',exact:true}).click();await expect(page.getByText('Groq key saved',{exact:true})).toBeVisible();await page.screenshot({path:'../evidence/setup.png',fullPage:true});
});
