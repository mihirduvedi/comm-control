const path=location.pathname;
const scope=path.startsWith('/field/')?path.split('/')[2]:'operator';
let launch:string|null=null;
let accessRequest:Promise<boolean>|undefined;
export function readAccessFragment():boolean{
 const params=new URLSearchParams(location.hash.slice(1)),incoming=params.get('token'),ticket=params.get('launch');
 if(!incoming&&!ticket)return false;
 if(incoming)sessionStorage.setItem('comm-token:'+scope,incoming);
 launch=ticket;accessRequest=undefined;
 history.replaceState(null,'',location.pathname+location.search);
 return true;
}
readAccessFragment();
export const token=()=>sessionStorage.getItem('comm-token:'+scope)||'';
export const isField=scope!=='operator';
export function ensureAccess():Promise<boolean>{
 if(token())return Promise.resolve(true);
 if(isField)return Promise.resolve(false);
 if(!accessRequest)accessRequest=(async()=>{
  // A launch fragment is exchanged once, even with React Strict Mode enabled.
  // The server keeps the browser session in an HttpOnly cookie, across tabs.
  if(launch){
   const response=await fetch('/api/operator/launch/exchange',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ticket:launch})});
   const result=await response.json();
   if(!response.ok){
    // A previously used link still works in an already connected browser.
    const session=await fetch('/api/operator/session');
    if(session.ok)return true;
    throw new Error(result.message||'Could not open this demo link. Try the local launcher.');
   }
   return true;
  }
  const response=await fetch('/api/operator/session');
  if(response.status===403)return false;
  if(!response.ok)throw new Error('Could not reach the demo. Check that the local server is running, then try again.');
  return true;
 })().catch(error=>{accessRequest=undefined;throw error});
 return accessRequest;
}
export async function api<T>(url:string,init:RequestInit={}):Promise<T>{
 const headers:Record<string,string>=token()?{'Authorization':'Bearer '+token()}:{};
 if(init.body && !(init.body instanceof FormData))headers['Content-Type']='application/json';
 if(init.method&&init.method!=='GET')headers['Idempotency-Key']=crypto.randomUUID();
 const response=await fetch(url,{...init,headers:{...headers,...init.headers}});
 const value=await response.json();
 if(!response.ok)throw new Error(value.message||value.detail||'Request failed. Try again.');
 return value as T;
}
export const post=<T>(url:string,body:unknown={})=>api<T>(url,{method:'POST',body:JSON.stringify(body)});
export const patch=<T>(url:string,body:unknown)=>api<T>(url,{method:'PATCH',body:JSON.stringify(body)});
export async function persistInstruction(id:string,value:unknown){
 return new Promise<void>((resolve,reject)=>{
  const open=indexedDB.open('comm-control:'+scope,1);
  open.onupgradeneeded=()=>open.result.createObjectStore('instructions');
  open.onerror=()=>reject(new Error('Device storage unavailable. Receipt has not been sent.'));
  open.onsuccess=()=>{
   const db=open.result;const tx=db.transaction('instructions','readwrite');tx.objectStore('instructions').put(value,id);
   tx.oncomplete=()=>{db.close();resolve()};tx.onerror=()=>{db.close();reject(new Error('Device storage failed. Receipt has not been sent.'))};
  }
 });
}
export const timeLabel=(stamp:string|number)=>new Date(typeof stamp==='number'?stamp*1000:stamp).toLocaleTimeString('en-US',{hour:'numeric',minute:'2-digit',timeZone:'America/Los_Angeles'});
export const stateLabel=(state:string)=>({queued:'Queued',transmitting:'Transmitting',awaiting_receipt:'Waiting for receipt',received:'Received by device',expired_unconfirmed:'Expired without confirmation',delivery_unconfirmed:'Delivery unconfirmed'}[state]||state.replaceAll('_',' '));
export function downloadJson(value:unknown,name:string){const url=URL.createObjectURL(new Blob([JSON.stringify(value,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download=name;a.click();URL.revokeObjectURL(url)}
// Separate local source store. Pending audio survives a failed upload or tab refresh.
export async function sourceRecording(key:string,operation:'get'|'put'|'delete',value?:unknown):Promise<any>{
 return new Promise((resolve,reject)=>{
  const open=indexedDB.open('comm-source:'+scope,1);open.onupgradeneeded=()=>open.result.createObjectStore('pending');open.onerror=()=>reject(new Error('Device source storage unavailable. Keep this tab open and retry.'));
  open.onsuccess=()=>{const db=open.result,tx=db.transaction('pending',operation==='get'?'readonly':'readwrite'),store=tx.objectStore('pending');let result:unknown;
   const req=operation==='get'?store.get(key):operation==='put'?store.put(value,key):store.delete(key);req.onsuccess=()=>{result=req.result};tx.oncomplete=()=>{db.close();resolve(result)};tx.onerror=()=>{db.close();reject(new Error('Device source storage failed. Recording has not been discarded.'))};
  };
 });
}
