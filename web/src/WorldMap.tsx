import {useEffect,useRef,useState} from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import {LocateFixed,Map as MapIcon,Route,AlertTriangle,Layers} from 'lucide-react';
import type {Report,OperationsSnapshot,GeoPlace} from './types';
import type {LivePreview} from './LiveIntake';
export const categoryColor:Record<string,string>={fire:'#b54735',medical:'#2460aa',access:'#9a6200',safety:'#6945a4',service:'#167265',information:'#596c82'};
const safeText=(value:string)=>{const span=document.createElement('span');span.textContent=value;return span};
export function WorldMap({reports,selected,operations,onSelect,onPick,routeChoice='recommended',compact=false,highlighted,livePreview}:{reports:Report[];selected:Report|null;operations:OperationsSnapshot;onSelect:(id:string)=>void;onPick?:((geo:GeoPlace)=>void)|null;routeChoice?:string;compact?:boolean;highlighted?:GeoPlace|null;livePreview?:LivePreview|null}){
 const el=useRef<HTMLDivElement>(null),map=useRef<L.Map|null>(null),group=useRef<L.LayerGroup|null>(null),callbacks=useRef({onSelect,onPick}),lastFocus=useRef('');callbacks.current={onSelect,onPick};const [tilesFailed,setTileFailure]=useState(false),[legend,setLegend]=useState(false);
 const related=new Set(selected?(selected.incident_id?reports.filter(r=>r.incident_id===selected.incident_id).map(r=>r.id):[selected.id]):[]);
 const assignments=operations.assignments.filter(a=>related.has(a.report_id)&&a.state!=='released');
 const fit=()=>{const points:L.LatLngExpression[]=(livePreview?.places||[]).map(p=>[p.lat,p.lon] as L.LatLngTuple);for(const a of assignments){const r=a.route.routes.find(r=>r.id===(a.selected_route||routeChoice))||a.route.routes[0];if(r)points.push(...r.coordinates.map(c=>[c[1],c[0]] as L.LatLngTuple))}if(highlighted)points.push([highlighted.lat,highlighted.lon]);const g=selected?.brief?.location;if(g)points.push([g.lat,g.lon]);if(points.length)map.current?.fitBounds(L.latLngBounds(points).pad(.2),{maxZoom:16,animate:false});else map.current?.fitBounds([[operations.atlas.bounds[0],operations.atlas.bounds[1]],[operations.atlas.bounds[2],operations.atlas.bounds[3]]],{animate:false})};
 useEffect(()=>{
  if(!el.current)return;const m=L.map(el.current,{zoomControl:false,scrollWheelZoom:true,wheelPxPerZoomLevel:100,preferCanvas:true,attributionControl:true}).setView([operations.atlas.center[1],operations.atlas.center[0]],14);map.current=m;
  L.tileLayer(operations.config.tile_url,{maxZoom:19,minZoom:3,attribution:'&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap contributors</a>'}).on('tileerror',()=>setTileFailure(true)).addTo(m);
  L.control.zoom({position:'bottomright'}).addTo(m);group.current=L.layerGroup().addTo(m);
  m.on('click',e=>{if(callbacks.current.onPick)callbacks.current.onPick({id:'operator-map-point',label:'Operator map selection',lon:e.latlng.lng,lat:e.latlng.lat,accuracy:'operator_estimated',source:'operator'})});
  const observer=new ResizeObserver(()=>m.invalidateSize());observer.observe(el.current);return()=>{observer.disconnect();m.remove();map.current=null};
 },[]);
 useEffect(()=>{
  const layer=group.current;if(!layer)return;layer.clearLayers();
  for(const c of operations.closures.filter(c=>['active','stale'].includes(c.state)))for(const line of c.coordinates)L.polyline(line.map(p=>[p[1],p[0]] as L.LatLngTuple),{color:'#b42318',weight:7,opacity:.85,dashArray:'6 5'}).bindTooltip(safeText(c.label+' — '+c.verification)).addTo(layer);
  for(const a of assignments){
   const picked=a.route.routes.find(r=>r.id===(a.selected_route||routeChoice))||a.route.routes[0];
   for(const r of [...a.route.routes].reverse())L.polyline(r.coordinates.map(c=>[c[1],c[0]] as L.LatLngTuple),{color:r.id===picked?.id?'#245fa8':'#7f91a7',weight:r.id===picked?.id?5:3,opacity:r.id===picked?.id ? .95 : .5,dashArray:r.id===picked?.id?undefined:'5 7'}).bindTooltip(safeText((operations.units.find(u=>u.id===a.unit_id)?.name||'Demo unit')+' '+(r.id===picked?.id?'selected route':'alternative'))).addTo(layer);
   if(picked?.coordinates.length&&selected?.brief?.location){const end=picked.coordinates.at(-1)!,dest=selected.brief.location;L.polyline([[end[1],end[0]],[dest.lat,dest.lon]],{color:'#718096',weight:2,dashArray:'2 6'}).bindTooltip('Arrival gap. Check the final approach.').addTo(layer)}
  }
  for(const r of reports.filter(r=>!r.superseded_by&&r.status!=='resolved')){
   const geo=r.brief?.location||r.claims.find(c=>c.location.role!=='reporter'&&c.location.geo)?.location.geo;if(!geo)continue;
   const selectedCase=r.id===selected?.id;L.circleMarker([geo.lat,geo.lon],{radius:selectedCase?12:8,color:'#fff',weight:3,fillColor:categoryColor[r.category||'service'],fillOpacity:1}).bindTooltip(safeText(geo.label+' — '+r.summary)).on('click',()=>callbacks.current.onSelect(r.id)).addTo(layer);
   if(selectedCase)L.circleMarker([geo.lat,geo.lon],{radius:19,color:categoryColor[r.category||'service'],weight:1,fillOpacity:.06,interactive:false}).addTo(layer);
  }
  for(const place of livePreview?.places||[])L.circleMarker([place.lat,place.lon],{radius:16,color:'#176e78',weight:3,dashArray:'5 4',fillColor:'#8ed6d0',fillOpacity:.3}).bindTooltip(safeText('Live call, not reviewed: '+place.label)).addTo(layer);
  if(highlighted)L.circleMarker([highlighted.lat,highlighted.lon],{radius:17,color:'#175cd3',weight:3,fillOpacity:.04}).bindTooltip(safeText('Selected source location: '+highlighted.label)).addTo(layer);
  for(const unit of operations.units){const icon=L.divIcon({className:'unit-map-marker '+unit.status,html:`<span>${unit.capabilities[0]==='fire'?'F':unit.capabilities[0]==='medical'?'M':unit.capabilities[0]==='traffic'?'A':unit.capabilities[0]==='safety'?'S':'H'}</span>`,iconSize:[24,24],iconAnchor:[12,12]});L.marker([unit.position.lat,unit.position.lon],{icon,keyboard:true,title:'Demo '+unit.name}).bindTooltip(safeText('Demo '+unit.name+' ('+unit.status.replaceAll('_',' ')+')')).addTo(layer)}
  const g=selected?.brief?.location;const focus=(selected?.id||'')+':'+(g?g.lon+','+g.lat:'')+':'+(highlighted?.id||'')+':'+(livePreview?.places.map(p=>p.id).join(',')||'');if(focus!==lastFocus.current){lastFocus.current=focus;fit()}
 },[reports,operations,selected?.id,routeChoice,highlighted,livePreview]);
 return <section className={'world-map '+(compact?'compact-world-map':'')+(onPick?' picking':'')} aria-label="Real-world incident map" data-live-place-count={livePreview?.places.length||0} data-route-count={assignments.reduce((n,a)=>n+a.route.routes.length,0)}><div className="world-map-heading"><div><MapIcon size={16}/><strong>{livePreview?.places.some(p=>p.id.startsWith('usc-'))?'USC University Park':operations.atlas.name}</strong></div><span>Real streets with demo calls</span></div><div className="world-map-canvas" ref={el} aria-label="OpenStreetMap. Incident and route details are also listed beside the map."/>{livePreview?.places.length?<div className="live-map-note"><MapIcon size={14}/>Live location preview <span>Not reviewed</span></div>:null}{onPick&&<div className="map-pick-note">Choose the event location on the map</div>}<button className="fit-world-map" onClick={fit}><LocateFixed size={16}/>Fit incident</button>{tilesFailed&&<div className="map-tile-warning"><AlertTriangle size={14}/>The basemap couldn’t load. Saved routes and locations are still shown.</div>}<div className="world-map-footer"><button className="text-button" onClick={()=>setLegend(x=>!x)} aria-expanded={legend}><Layers size={14}/>Map key</button><span><Route size={13}/>Reported blockages avoided</span></div>{legend&&<div className="world-map-legend"><span><i style={{background:'#245fa8'}}/>Selected route</span><span><i style={{background:'#8796aa'}}/>Alternative route</span><span><i style={{background:'#b42318'}}/>Reported road closure</span><span>Letters mark demo units</span><small>Check access before traveling. Live traffic isn’t included.</small></div>}</section>
}
