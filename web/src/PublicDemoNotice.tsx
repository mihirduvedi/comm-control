import {useEffect,useState} from 'react';
interface Status {public_demo:boolean;voice_enabled:boolean;message:string;visitor_hour_remaining:number}
export function PublicDemoNotice(){
 const [status,setStatus]=useState<Status|null>(null);
 useEffect(()=>{let active=true;const load=()=>void fetch('/api/public-demo/status').then(r=>r.ok?r.json():null).then(v=>{if(active)setStatus(v)}).catch(()=>{});load();const timer=setInterval(load,15000);return()=>{active=false;clearInterval(timer)}},[]);
 if(!status?.public_demo)return null;
 return <aside className="public-demo-notice" aria-label="Public demo voice allowance" aria-live="polite"><strong>Shared demo</strong><span>Use fictional reports. {status.voice_enabled?`Voice AI: ${status.visitor_hour_remaining} model calls left for your network this hour. A report uses several calls. Audio is processed by Groq.`:status.message}</span><a href="/" target="_blank" rel="noreferrer">Demo limits</a></aside>;
}
