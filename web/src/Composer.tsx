import {useState,useEffect,useRef} from 'react';
import {ArrowUpRight,Check,Send,LoaderCircle,ChevronDown,AlertTriangle} from 'lucide-react';
import {api,post,patch,timeLabel} from './api';
import {VoiceInput} from './VoiceInput';
import {useJob} from './hooks';
import type {Draft,Session} from './types';
export function Composer({sessions,sessionId,onClose,onSent,replacesId,initialDraft}:{sessions:Session[];sessionId:string;onClose:()=>void;onSent:()=>void;replacesId?:string;initialDraft?:Draft}){
 const [draft,setDraft]=useState<Draft|null>(initialDraft||null),[text,setText]=useState(initialDraft?.text||''),[source,setSource]=useState(initialDraft?.source_text||''),[recipientIds,setRecipients]=useState([sessionId]),[expiry,setExpiry]=useState(5),[sourceOpen,setSourceOpen]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState(''),[manual,setManual]=useState(false);
 const cacheKey='comm-response:'+sessionId+':'+(initialDraft?.id||replacesId||'new');
 const cached=useRef<{id?:string;source?:string;text?:string;recipients?:string[]}|null>(null);
 useEffect(()=>{
  if(initialDraft)return;
  try{cached.current=JSON.parse(localStorage.getItem(cacheKey)||'null')}catch{cached.current=null}
  const old=cached.current;if(!old)return;
  if(old.source)setSource(old.source);if(old.text)setText(old.text);if(old.recipients)setRecipients(old.recipients);
  if(old.id)void api<Draft>('/api/drafts/'+old.id).then(d=>{if(d.sent_ids){localStorage.removeItem(cacheKey);return}setDraft(d);setText(old.text||d.text);setSource(old.source||d.source_text);setSourceOpen(true)}).catch(()=>setError('Saved text restored. Recreate the draft to review it.'));
 },[cacheKey]);
 useEffect(()=>{if(text||source)localStorage.setItem(cacheKey,JSON.stringify({id:draft?.id,source,text,recipients:recipientIds}))},[cacheKey,draft?.id,source,text,recipientIds]);
 const {job,setJob}=useJob();
 useEffect(()=>{if(job?.draft){setDraft(job.draft);setText(job.draft.text);setSource(job.draft.source_text);setSourceOpen(true)}if(job?.state==='failed')setError(job.error||'We couldn’t process this response.')},[job]);
 const save=async()=>{if(!draft)throw new Error('Create a response first.');const result=await patch<Draft>('/api/drafts/'+draft.id,{version:draft.version,text,recipient_ids:recipientIds,expires_at:Date.now()/1000+expiry*60,replaces_message_id:replacesId||null});setDraft(result);return result};
 const approve=async()=>{setBusy(true);setError('');try{const current=await save();setDraft(await post<Draft>('/api/drafts/'+current.id+'/approve',{version:current.version}))}catch(e){setError((e as Error).message)}finally{setBusy(false)}};
 const send=async()=>{if(!draft)return;setBusy(true);try{await post('/api/drafts/'+draft.id+'/send',{version:draft.version});localStorage.removeItem(cacheKey);onSent()}catch(e){setError((e as Error).message)}finally{setBusy(false)}};
 const exact=async()=>{setBusy(true);setError('');try{const result=await post<Draft>('/api/drafts/manual',{session_id:sessionId,direction:'outgoing',text:source});setDraft(result);setText(result.text);setManual(false);setSourceOpen(true)}catch(e){setError((e as Error).message)}finally{setBusy(false)}};
 const changed=()=>setDraft(d=>d?{...d,approval:null}:null);
 return <section className="composer" aria-label="Response composer"><div className="section-heading"><h3>Respond</h3><button className="text-button" onClick={onClose}>Close</button></div>
  {replacesId&&<p className="attention-note">Replacement: the earlier instruction stays current until this revision reaches the recipient.</p>}<p className="context-note">To {sessions.filter(s=>recipientIds.includes(s.id)).map(s=>s.display_name).join(', ')||'no recipient'}</p>
  <VoiceInput sessionId={sessionId} direction="outgoing" onJob={setJob} onError={setError} compact disabled={!!job&&!['ready','failed'].includes(job.state)} sourceText={source} onTextChange={setSource}/>
  {job&&!['ready','failed'].includes(job.state)&&<p className="processing" role="status"><LoaderCircle size={15} className="spin"/>{job.state==='queued'?'Waiting to process your response':job.state==='transcribing'?'Transcribing your response':'Checking the response'}…</p>}
  {!draft&&<><button className="text-button" onClick={()=>setManual(x=>!x)}>Use an exact written instruction <ArrowUpRight size={13}/></button>{manual&&<div className="manual-instruction"><label htmlFor="exact-source" className="field-label">Operator’s exact words</label><textarea id="exact-source" rows={4} value={source} onChange={e=>setSource(e.target.value)}/><p className="hint">These words won’t be rewritten by AI. Review them before sending.</p><button className="button secondary" onClick={()=>void exact()} disabled={!source.trim()||busy}>Use these words</button></div>}</>}
  {draft&&<><div className="draft-heading"><label className="field-label" htmlFor="response-text">{draft.approval?'Approved instruction':'Instruction to review'}</label>{draft.approval&&<span className="approved-label"><Check size={13}/>Approved {timeLabel(draft.approval.at)}</span>}</div><textarea id="response-text" className="instruction-editor" rows={5} value={text} onChange={e=>{setText(e.target.value);changed()}}/>
   <button className="disclosure" onClick={()=>setSourceOpen(x=>!x)} aria-expanded={sourceOpen}>Source & protected details<ChevronDown size={15} className={sourceOpen?'rotate':''}/></button>
   {sourceOpen&&<div className="source-comparison"><p className="source-quote">{draft.source_text}</p>{draft.critical_fields.map((f,i)=><div key={i} className="critical-line"><span>{f.kind==='prohibition'?'Prohibition':f.kind==='condition'?'Condition':'Detail'}</span><strong>{f.value}</strong></div>)}<p className="hint">{draft.origin_label==='manual'?'Your exact words. Check them before sending.':draft.origin_label.startsWith('automatic')?'Prepared from this report. Check it before sending.':'AI draft. Check it before sending.'}</p></div>}
   <details className="recipient-options"><summary>Recipients & expiry</summary><div className="recipient-list">{sessions.map(s=><label key={s.id}><input type="checkbox" checked={recipientIds.includes(s.id)} onChange={e=>{setRecipients(x=>e.target.checked?[...x,s.id]:x.filter(id=>id!==s.id));changed()}}/>{s.display_name}</label>)}</div><label className="field-label" htmlFor="expiry">Instruction valid for</label><select id="expiry" value={expiry} onChange={e=>{setExpiry(Number(e.target.value));changed()}}><option value={.5}>30 seconds</option><option value={5}>5 minutes</option><option value={15}>15 minutes</option><option value={60}>1 hour</option></select></details>
   <div className="composer-action">{draft.approval?<button className="button primary full-width" onClick={()=>void send()} disabled={busy}><Send size={16}/>{busy?'Sending…':`Send to ${recipientIds.length===1?sessions.find(s=>s.id===recipientIds[0])?.display_name:recipientIds.length+' recipients'}`}</button>:<button className="button primary full-width" onClick={()=>void approve()} disabled={busy||!text.trim()||!recipientIds.length}><Check size={17}/>{busy?'Checking…':'Review & approve'}</button>}<p className="hint">Changing the words, recipients or time limit means you’ll need to approve again.</p></div>
  </>}
  {error&&<div className="inline-error" role="alert"><AlertTriangle size={16}/><span>{error}</span></div>}
 </section>
}
