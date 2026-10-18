import {useState,useRef,useEffect} from 'react';
import {Mic,Square,Upload,Keyboard,LoaderCircle,X} from 'lucide-react';
import {api,post,sourceRecording} from './api';
import {useRecorder} from './hooks';
import type {Job} from './types';
interface Props{sessionId:string;direction?:string;onJob:(j:Job)=>void;onError:(s:string)=>void;replyTo?:string;responseAction?:string;compact?:boolean;disabled?:boolean;sourceText?:string;onTextChange?:(s:string)=>void}
export function VoiceInput({sessionId,direction='inbound',onJob,onError,replyTo,responseAction,compact=false,disabled=false,sourceText,onTextChange}:Props){
 const [typing,setTyping]=useState(false),[text,setText]=useState(sourceText||''),[sending,setSending]=useState(false);const input=useRef<HTMLInputElement>(null);
 const storageKey=sessionId+':'+direction+':'+(replyTo||'report');
 const [pending,setPending]=useState<{blob:Blob;id:string}|null>(null);
 useEffect(()=>{void sourceRecording(storageKey,'get').then(value=>{if(value)setPending(value)}).catch(e=>onError(e.message));if(!onTextChange)setText(localStorage.getItem('comm-typed:'+storageKey)||'')},[storageKey]);
 useEffect(()=>{if(!onTextChange)localStorage.setItem('comm-typed:'+storageKey,text)},[text,storageKey]);
 const textValue=onTextChange?sourceText||'':text;
 const upload=async(blob:Blob,retryId?:string)=>{setSending(true);const saved={blob,id:retryId||crypto.randomUUID()};setPending(saved);
  try{if(blob.size>10*1024*1024)throw new Error('This file is too large. Choose a recording under 10 MB.');await sourceRecording(storageKey,'put',saved);const body=new FormData();body.append('audio',blob,'recording.webm');body.append('session_id',sessionId);body.append('direction',direction);if(replyTo)body.append('reply_to',replyTo);if(responseAction)body.append('response_action',responseAction);const job=await api<Job>('/api/utterances',{method:'POST',body,headers:{'Idempotency-Key':saved.id}});await sourceRecording(storageKey,'delete');setPending(null);onJob(job)}catch(e){onError((e as Error).message)}finally{setSending(false)}};
 const recorder=useRecorder(blob=>void upload(blob),onError);
 const submitText=async()=>{setSending(true);try{onJob(await post<Job>('/api/utterances/text',{session_id:sessionId,direction,text:textValue,reply_to:replyTo,response_action:responseAction}));}catch(e){onError((e as Error).message)}finally{setSending(false)}};
 return <div className={'voice-input '+(compact?'compact':'')}>{pending&&!sending&&<div className="input-recovery"><p className="hint">Your unsent recording is saved on this device.</p><button className="button secondary" disabled={disabled} onClick={()=>void upload(pending.blob,pending.id)}>Retry saved recording</button><button className="text-button" onClick={()=>sourceRecording(storageKey,'delete').then(()=>setPending(null)).catch(e=>onError(e.message))}>Discard saved recording</button></div>}
  <div className="record-row">
   <button className={recorder.recording?'button recording':'button primary'} onClick={()=>recorder.recording?recorder.stop():void recorder.start()} disabled={disabled||sending}>
    {sending?<LoaderCircle className="spin" size={18}/>:recorder.recording?<Square size={16} fill="currentColor"/>:<Mic size={18}/>}
    {sending?'Uploading…':recorder.recording?`Stop recording (0:${String(recorder.seconds).padStart(2,'0')})`:direction==='outgoing'?'Dictate response':'Record report'}
   </button>
   {recorder.recording&&<button className="icon-button" aria-label="Cancel recording" onClick={recorder.cancel}><X size={17}/></button>}
   <button className="icon-button" aria-label="Upload audio recording" onClick={()=>input.current?.click()} disabled={disabled||sending||recorder.recording}><Upload size={18}/></button>
   <button className={'icon-button '+(typing?'active':'')} aria-label="Type instead" onClick={()=>setTyping(x=>!x)} disabled={recorder.recording}><Keyboard size={19}/></button>
   <input ref={input} type="file" accept="audio/*,.webm,.mp4" className="sr-only" aria-label="Audio file" onChange={e=>{if(e.target.files?.[0])void upload(e.target.files[0]);e.target.value=''}}/>
  </div>
  {typing&&<form onSubmit={e=>{e.preventDefault();void submitText()}}><label className="field-label" htmlFor={'source-'+direction}>Type the {direction==='outgoing'?'operator response':'field report'}</label><textarea id={'source-'+direction} value={textValue} maxLength={6000} onChange={e=>onTextChange?onTextChange(e.target.value):setText(e.target.value)} rows={compact?3:5} placeholder={direction==='outgoing'?'Stay outside. Do not use the north gate.':'Describe what happened, where, and what you need.'}/><button className="button secondary" type="submit" disabled={!textValue.trim()||sending||disabled}>{sending?'Processing…':'Interpret typed text'}</button><span className="hint">AI will read the text you enter.</span></form>}
  {!typing&&!recorder.recording&&<p className="input-hint">Up to {recorder.maxSeconds} seconds. Audio is sent to Groq for transcription.</p>}
 </div>
}
