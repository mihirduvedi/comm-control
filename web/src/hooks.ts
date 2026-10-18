import { useCallback,useEffect,useRef,useState } from 'react';
import {api,token} from './api';
import type {Job} from './types';
export function useSnapshot<T>(url:string){
 const [data,setData]=useState<T|null>(null),[error,setError]=useState(''),[connected,setConnected]=useState(true);
 const refresh=useCallback(async()=>{try{const result=await api<T>(url);setData(result);setError('');setConnected(true)}catch(e){setError((e as Error).message);setConnected(false)}},[url]);
 useEffect(()=>{void refresh();const timer=setInterval(()=>void refresh(),4000);return()=>clearInterval(timer)},[refresh]);
 useEffect(()=>{
  const ws=new WebSocket((location.protocol==='https:'?'wss://':'ws://')+location.host+'/api/live');
  ws.onopen=()=>ws.send(JSON.stringify({token:token(),after:0}));ws.onmessage=e=>{const value=JSON.parse(e.data);if(value.events?.length)void refresh()};
  return()=>ws.close();
 },[refresh]);
 return {data,error,connected,refresh};
}
export function useJob(){
 const [job,setJob]=useState<Job|null>(null),[error,setError]=useState('');
 useEffect(()=>{if(!job||['ready','failed'].includes(job.state))return;const t=setInterval(()=>{api<Job>('/api/jobs/'+job.id).then(setJob).catch(e=>setError(e.message))},700);return()=>clearInterval(t)},[job]);
 return {job,setJob,error,setError};
}
export function useRecorder(onRecording:(blob:Blob)=>void,onError:(message:string)=>void){
 const [recording,setRecording]=useState(false),[seconds,setSeconds]=useState(0);
 const [maxSeconds,setMaxSeconds]=useState(60);
 useEffect(()=>{let active=true;void fetch('/api/public-demo/status').then(r=>r.ok?r.json():null).then(v=>{if(active&&v?.public_demo)setMaxSeconds(30)}).catch(()=>{});return()=>{active=false}},[]);
 const media=useRef<MediaRecorder|null>(null),stream=useRef<MediaStream|null>(null),chunks=useRef<Blob[]>([]),cancelled=useRef(false);
 const stop=useCallback(()=>{if(media.current?.state==='recording')media.current.stop()},[]);
 const cancel=()=>{cancelled.current=true;stop()};
 const start=async()=>{
  try{
   if(!navigator.mediaDevices?.getUserMedia)throw new Error('Microphone needs localhost or HTTPS. Use text or upload a recording.');
   stream.current=await navigator.mediaDevices.getUserMedia({audio:true});chunks.current=[];cancelled.current=false;
   const recorder=new MediaRecorder(stream.current);media.current=recorder;
   recorder.ondataavailable=e=>{if(e.data.size)chunks.current.push(e.data)};
   recorder.onstop=()=>{setRecording(false);stream.current?.getTracks().forEach(t=>t.stop());if(!cancelled.current)onRecording(new Blob(chunks.current,{type:recorder.mimeType}))};
   recorder.start(250);setSeconds(0);setRecording(true);
  }catch(e){onError((e as Error).name==='NotAllowedError'?'Microphone permission was denied. Allow it in browser settings, upload audio, or use text.':(e as Error).message)}
 };
 useEffect(()=>{if(!recording)return;const timer=setInterval(()=>setSeconds(x=>{if(x>=maxSeconds-1){stop();return maxSeconds}return x+1}),1000);return()=>clearInterval(timer)},[recording,stop,maxSeconds]);
 useEffect(()=>()=>{cancelled.current=true;if(media.current?.state==='recording')media.current.stop();stream.current?.getTracks().forEach(t=>t.stop())},[]);
 return {recording,seconds,maxSeconds,start,stop,cancel};
}
