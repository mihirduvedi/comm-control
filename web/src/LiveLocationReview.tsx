import {useEffect,useState} from 'react';
import {MapPin,Search} from 'lucide-react';
import {useSnapshot} from './hooks';
import type {USCData} from './USCResources';
import {api} from './api';
import type {Draft,GeoPlace} from './types';
import {useWorkspace} from './workspace';
export function LiveLocationReview({draft,places,disabled,onChange}:{draft:Draft;places:GeoPlace[];disabled:boolean;onChange:(p:GeoPlace|null)=>void}){
 const {world}=useWorkspace();
 const {data:usc}=useSnapshot<USCData>('/api/usc/operations');
 const campus=draft.claims.find(c=>c.location.role!=='reporter'&&c.location.feature_id?.startsWith('usc-'))?.location.feature_id;
 const building=usc?.site.buildings.find(b=>b.id===campus);
 const campusPlace:GeoPlace|null=building?{id:building.id,label:building.name,lon:building.center[0],lat:building.center[1],accuracy:'building',source:'USC campus / OpenStreetMap'}:null;
 const proposed=world==='usc'?campusPlace:draft.claims.find(c=>c.location.role!=='reporter'&&c.location.geo)?.location.geo||null;
 const [selected,setSelected]=useState<GeoPlace|null>(proposed),[query,setQuery]=useState(''),[results,setResults]=useState<GeoPlace[]>([]),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 useEffect(()=>{if(world==='usc'&&campusPlace&&!selected){setSelected(campusPlace);onChange(campusPlace)}},[building?.id]);
 useEffect(()=>{onChange(proposed)},[]);
 const options=[...places,...results,...(campusPlace?[campusPlace]:[]),...(proposed?[proposed]:[])].filter(p=>world==='usc'?p.id.startsWith('usc-'):!p.id.startsWith('usc-')).filter((p,i,all)=>all.findIndex(x=>x.id===p.id)===i);
 const find=async()=>{setBusy(true);setError('');try{const found=world==='usc'?(usc?.site.buildings.filter(b=>(b.code+' '+b.name).toLowerCase().includes(query.toLowerCase())).map(b=>({id:b.id,label:b.name,lon:b.center[0],lat:b.center[1],accuracy:'building',source:'USC campus / OpenStreetMap'}))||[]):(await api<{places:GeoPlace[]}>('/api/geo/search?q='+encodeURIComponent(query))).places;setResults(found);if(!found.length)setError(world==='usc'?'No supported USC building matches. Try a building name or code.':'No local match. Try a Downtown LA address, landmark or intersection.')}catch(e){setError((e as Error).message)}finally{setBusy(false)}};
 return <section className="live-location-review" aria-label="Live call event location"><h3><MapPin size={15}/>Event location</h3><p>{selected?'Review the event pin before adding the incident. Available demo units will be assigned after delivery.':'Choose where the event is happening. A caller’s position alone won’t send units there.'}</p><div className="call-location-options">{options.map(p=><label key={p.id}><input type="radio" name={'event-location-'+draft.id} disabled={disabled} checked={selected?.id===p.id} onChange={()=>{setSelected(p);onChange(p)}}/><span>{p.label}<small>{p.accuracy.replaceAll('_',' ')}</small></span></label>)}</div><div className="call-location-search"><input aria-label="Find live event location" value={query} onChange={e=>setQuery(e.target.value)} placeholder="Address, landmark or intersection" maxLength={180}/><button className="button secondary" disabled={disabled||busy||query.trim().length<2} onClick={()=>void find()}><Search size={14}/>{busy?'Finding…':'Find'}</button></div>{selected&&<button className="text-button" disabled={disabled} onClick={()=>{setSelected(null);onChange(null)}}>Keep location unconfirmed</button>}{!selected&&<p className="hint">You can still add the report. Location review will stay open and no unit will be sent to an unconfirmed place.</p>}{error&&<p className="inline-error" role="alert">{error}</p>}</section>
}
