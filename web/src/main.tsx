import React,{useEffect,useState} from 'react';
import ReactDOM from 'react-dom/client';
import {Radio,LayoutPanelLeft,UsersRound,Settings2,SlidersHorizontal,FileCheck2,ArrowUpRight,Mic} from 'lucide-react';
import {SlidingBar} from './SlidingBar';
import {LiveClock} from './LiveClock';
import {WorkspaceContext,readWorld,workspaceHref} from './workspace';
import type {World} from './workspace';
import {Operator} from './Operator';
import {USCResources} from './USCResources';
import {Resources} from './Resources';
import {Admin} from './Admin';
import {Field} from './Field';
import {api,isField,token,ensureAccess,readAccessFragment} from './api';
import './styles.css';
import './dispatch.css';
import './tone.css';
import './daylight.css';
import './glass.css';
import './atlas.css';
import './workspaces.css';
import './system.css';
function App(){
 const [route,setRoute]=useState(()=>location.pathname+location.search),[world,changeWorld]=useState<World>(readWorld);
 const page=route.split('?')[0].split('/')[1]||'control';
 useEffect(()=>{if(!isField)try{localStorage.setItem('comm-workspace',world)}catch{}},[world]);
 useEffect(()=>{
  if(isField)return;
  const update=()=>{setRoute(location.pathname+location.search);changeWorld(readWorld())};
  const click=(e:MouseEvent)=>{const a=(e.target as Element).closest?.('a');if(!a||e.defaultPrevented||e.button!==0||e.metaKey||e.ctrlKey||e.shiftKey||e.altKey||a.target||a.hasAttribute('download'))return;const u=new URL(a.href);if(u.origin!==location.origin||!['/control','/resources','/sessions','/demo','/review','/setup'].includes(u.pathname)||u.hash)return;e.preventDefault();const explicit=u.searchParams.get('world')||(['usc','site'].includes(u.searchParams.get('view')||'')?'usc':null);const next=explicit==='usc'?'usc':explicit==='city'?'city':readWorld();history.pushState(null,'',workspaceHref(u.pathname+u.search,next));try{localStorage.setItem('comm-workspace',next)}catch{}update();window.scrollTo(0,0)};
  window.addEventListener('popstate',update);document.addEventListener('click',click);return()=>{window.removeEventListener('popstate',update);document.removeEventListener('click',click)};
 },[]);
 const setWorld=(next:World)=>{if(next===world)return;const u=new URL(location.href);u.searchParams.delete('report');u.searchParams.delete('live');u.searchParams.delete('view');history.pushState(null,'',workspaceHref(u.pathname+u.search,next));try{localStorage.setItem('comm-workspace',next)}catch{}changeWorld(next);setRoute(location.pathname+location.search)};
 const [access,setAccess]=useState(token()?'ready':'loading'),[accessError,setAccessError]=useState('');
 useEffect(()=>{
  const url=new URL(location.href),id=url.searchParams.get('report');let active=true;
  if(!isField&&access==='ready'&&page==='control'&&id&&!url.searchParams.has('world'))void api<{world:World}>('/api/reports/'+encodeURIComponent(id)+'/context').then(value=>{if(!active)return;history.replaceState(null,'',workspaceHref(url.pathname+url.search,value.world));changeWorld(value.world);setRoute(location.pathname+location.search)}).catch(()=>{});
  return()=>{active=false};
 },[access,route]);
 useEffect(()=>{
  let active=true;
  const check=()=>{setAccessError('');ensureAccess().then(ready=>{if(active)setAccess(ready?'ready':'needed')}).catch(error=>{if(active){setAccessError(error.message);setAccess('needed')}})};
  const followLink=()=>{if(readAccessFragment()){setAccess('loading');check()}};
  window.addEventListener('hashchange',followLink);check();
  return()=>{active=false;window.removeEventListener('hashchange',followLink)};
 },[]);
 if(access==='loading')return <main className="launch-page" aria-busy="true"><Radio size={32}/><h1>Comm Control</h1><p role="status">Opening your workspace…</p></main>;
 if(access!=='ready')return <main className="launch-page"><Radio size={32}/><h1>Comm Control</h1><p>{isField?'Open this caller’s private link from Sessions.':'This browser needs a demo access link.'}</p>{accessError&&<p role="alert">{accessError}</p>}<p className="hint">{isField?'Caller links keep each person’s reports separate.':'Open the local launcher to connect this browser. Once connected, you can reopen the demo in new tabs for eight hours.'}</p>{!isField&&<p className="hint">From the app folder, run <code>.venv/bin/python scripts/open_app.py</code>.</p>}</main>;
 if(isField)return <Field/>;
 return <WorkspaceContext.Provider value={{world,setWorld}}><div className="app"><a className="skip-link" href="#main-content">Skip to workspace</a><header className="app-header"><a className="brand" href={workspaceHref('/control',world)}><span className="brand-mark"><Radio size={19}/></span><span className="brand-wordmark"><strong>Comm Control</strong><small>Voice to coordinated response</small></span><span className="brand-divider"/></a><SlidingBar as="nav" aria-label="Main navigation">{[{id:'control',label:'Workspace',icon:LayoutPanelLeft},{id:'resources',label:'Resources',icon:Radio},{id:'sessions',label:'Sessions',icon:UsersRound},{id:'demo',label:'Simulator',icon:SlidersHorizontal},{id:'review',label:'Review',icon:FileCheck2}].map(item=><a key={item.id} href={workspaceHref('/'+item.id,world)} className={page===item.id?'active':''} aria-current={page===item.id?'page':undefined}><item.icon size={15}/>{item.label}</a>)}</SlidingBar><div className="header-quick-action"><select className="mobile-workspace-select" aria-label="Operating workspace" value={world} onChange={e=>setWorld(e.target.value as World)}><option value="city">Downtown LA</option><option value="usc">USC campus</option></select><SlidingBar className="workspace-switch" role="group" aria-label="Operating workspace"><button className={world==='city'?'active':''} onClick={()=>setWorld('city')}>Downtown LA</button><button className={world==='usc'?'active':''} onClick={()=>setWorld('usc')}>USC campus</button></SlidingBar><button className="header-live-call" aria-label="Start voice report" onClick={()=>{if(page==='control')window.dispatchEvent(new Event('comm-start-live-call'));else {history.pushState({startFreshCall:true},'',workspaceHref('/control?live=1',world));setRoute(location.pathname+location.search)}}}><Mic size={15}/><span><span className="voice-verb">Start </span>voice report</span></button></div><div className="header-right"><span className="demo-label">Demo workspace</span><LiveClock/><a href={workspaceHref('/setup',world)} className={'setup-link '+(page==='setup'?'active':'')}><Settings2 size={17}/><span>Setup</span></a><a href="/sessions" className="field-shortcut" aria-label="Open field sessions"><ArrowUpRight size={17}/></a></div></header><div id="main-content" tabIndex={-1} key={page+world}>{page==='control'?<Operator/>:page==='resources'?(world==='usc'?<USCResources/>:<Resources/>):<Admin page={page}/>}</div></div></WorkspaceContext.Provider>
}
ReactDOM.createRoot(document.getElementById('root')!).render(<React.StrictMode><App/></React.StrictMode>);
