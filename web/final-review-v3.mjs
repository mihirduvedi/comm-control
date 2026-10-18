import {chromium} from '@playwright/test';
import fs from 'node:fs';
const token=JSON.parse(fs.readFileSync('../.data/run.json','utf8')).operator_token;
const browser=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true});
try{
 const page=await browser.newPage({viewport:{width:1280,height:800}});await page.addInitScript(t=>sessionStorage.setItem('comm-token:operator',t),token);
 const response=await page.request.get('http://127.0.0.1:8765/api/control/snapshot',{headers:{Authorization:'Bearer '+token}});const s=await response.json();const report=s.reports.find(r=>r.category==='fire'&&r.brief?.location);
 await page.goto('http://127.0.0.1:8765/control'+(report?'?report='+report.id:''));await page.locator('.dispatch-shell').waitFor();await page.locator('.leaflet-tile-loaded').first().waitFor();await page.waitForTimeout(900);await page.screenshot({path:'../evidence/v3-actual-1280.png'});
 console.log(await page.evaluate(()=>({headers:document.querySelectorAll('.app-header').length,width:document.documentElement.scrollWidth,height:document.documentElement.scrollHeight,viewportHeight:innerHeight,attribution:!!document.querySelector('.leaflet-control-attribution')})));
 await page.setViewportSize({width:1440,height:900});await page.waitForTimeout(700);await page.screenshot({path:'../evidence/v3-actual-1440.png'});
 const launch=await(await page.request.get('http://127.0.0.1:8765/api/sessions/'+report.session_id+'/launch',{headers:{Authorization:'Bearer '+token}})).json();const field=await browser.newPage({viewport:{width:390,height:844}});await field.goto('http://127.0.0.1:8765'+launch.url);const show=field.getByRole('button',{name:'Show map',exact:false});if(await show.count()){await show.click();await field.locator('.field-real-map .leaflet-tile-loaded').first().waitFor();}await field.waitForTimeout(500);await field.screenshot({path:'../evidence/v3-actual-field-390.png',fullPage:true});await field.close();
}finally{await browser.close()}
