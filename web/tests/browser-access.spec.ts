import {test,expect} from '@playwright/test';
import fs from 'node:fs';
import AxeBuilder from '@axe-core/playwright';

const run=()=>JSON.parse(fs.readFileSync('../.data-browser-tests/run.json','utf8'));
const h=()=>({Authorization:'Bearer '+run().operator_token,'Idempotency-Key':crypto.randomUUID()});
async function link(request:any){const response=await request.post('/api/operator/launch',{headers:h()});expect(response.ok()).toBeTruthy();return(await response.json()).url}

test('fresh browser launch stays connected across reload, new tabs, navigation and mutations',async({page,context,request})=>{
 const errors:string[]=[];page.on('pageerror',error=>errors.push(error.message));
 await page.goto('/control?live=1');
 await expect(page.getByText('This browser needs a demo access link.',{exact:true})).toBeVisible();
 const launch=await link(request);await page.goto(launch);
 await expect(page.getByRole('region',{name:'Live call intake'})).toBeVisible();
 await expect(page.getByRole('button',{name:'Start microphone',exact:true})).toBeVisible();
 expect(new URL(page.url()).hash).toBe('');
 expect(await page.evaluate(()=>sessionStorage.getItem('comm-token:operator'))).toBeNull();
 expect(await page.evaluate(()=>document.cookie)).not.toContain('comm_operator_session');
 await page.reload();await expect(page.getByRole('region',{name:'Live call intake'})).toBeVisible();
 const other=await context.newPage();await other.goto('/control?live=1');
 await expect(other.getByRole('button',{name:'Start microphone',exact:true})).toBeVisible();
 await other.getByRole('link',{name:'Sessions',exact:true}).click();
 const name='Browser session '+Date.now();await other.getByLabel('Reporter name').fill(name);await other.getByRole('button',{name:'Create session',exact:true}).click();
 await expect(other.getByText(name,{exact:true})).toBeVisible();await other.reload();await expect(other.getByText(name,{exact:true})).toBeVisible();
 await other.goto(launch);await expect(other.getByRole('region',{name:'Live call intake'})).toBeVisible();
 const violations=(await new AxeBuilder({page}).analyze()).violations.filter(v=>['critical','serious'].includes(v.impact||''));
 expect(violations.map(v=>v.id)).toEqual([]);expect(errors).toEqual([]);
 await page.screenshot({path:'../evidence/browser-access-desktop.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});await page.getByRole('tab',{name:'Details',exact:true}).click();
 await expect(page.getByRole('button',{name:'Start microphone',exact:true})).toBeVisible();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
 await page.screenshot({path:'../evidence/browser-access-mobile.png',fullPage:true});
});

test('one-use link cannot authorize a second browser and reports a useful error',async({page,browser,request})=>{
 const launch=await link(request);await page.goto(launch);await expect(page.getByRole('region',{name:'Live call intake'})).toBeVisible();
 const isolated=await browser.newContext();const fresh=await isolated.newPage();await fresh.goto(launch);
 await expect(fresh.getByRole('alert')).toHaveText('This demo link expired or was already used. Open a fresh link with the local launcher.');
 await expect(fresh.getByRole('region',{name:'Live call intake'})).not.toBeVisible();await isolated.close();
});

test('caller pages still require their private link with an operator cookie present',async({page,request})=>{
 await page.goto(await link(request));await expect(page.getByRole('region',{name:'Live call intake'})).toBeVisible();
 const session=await(await request.post('/api/sessions',{headers:h(),data:{name:'Private access check'}})).json();
 await page.goto('/field/'+session.id);await expect(page.getByText('Open this caller’s private link from Sessions.',{exact:true})).toBeVisible();
 const launch=await(await request.get('/api/sessions/'+session.id+'/launch',{headers:h()})).json();await page.goto(launch.url);
 await expect(page.getByRole('button',{name:'Record report',exact:true})).toBeVisible();
 const forbidden=await page.evaluate(async()=>{const key=Object.keys(sessionStorage).find(k=>k.startsWith('comm-token:')&&!k.endsWith('operator'))!;return(await fetch('/api/control/snapshot',{headers:{Authorization:'Bearer '+sessionStorage.getItem(key)}})).status});
 expect(forbidden).toBe(403);
});
