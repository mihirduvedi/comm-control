import {Check,FileText,MapPin,UsersRound,Route,Mic} from 'lucide-react';
import type {Report,OperationsSnapshot,Incident} from './types';
import type {USCData} from './USCResources';

export function ResponseJourney({report,world,operations,incidents,campus}:{report:Report;world:'city'|'usc';operations:OperationsSnapshot;incidents:Incident[];campus:USCData|null}){
 const siblings=incidents.find(i=>i.id===report.incident_id)?.report_ids||[report.id];
 const assigned=operations.assignments.filter(a=>siblings.includes(a.report_id)&&a.state!=='released');
 const ticket=world==='usc'?campus?.tickets.find(t=>t.report_ids.some(id=>siblings.includes(id))&&t.state!=='resolved'):undefined;
 const finished=world==='city'?operations.plans.some(p=>p.report_id===report.id&&p.state==='unit_work_finished'):campus?.tickets.some(t=>t.report_ids.includes(report.id)&&t.state==='resolved');
 const located=world==='usc'?!!ticket||!!finished:!!report.brief?.location;
 const teams=world==='usc'?(ticket?.team_id?1:0):assigned.length;
 const routed=world==='usc'?ticket?.route?.status==='ready':assigned.length>0&&assigned.every(a=>a.route.status==='ready');
 const voice=/\bvoice\b/i.test(report.origin_label);
 const source=voice?'Voice report':/typed|text/i.test(report.origin_label)?'Text report':/manual/i.test(report.origin_label)?'Manual report':/transcript/i.test(report.origin_label)?'Reviewed transcript':/annotated|demo/i.test(report.origin_label)?'Demo report':'Received report';
 const steps=[
  {label:voice?'Voice parsed':'Details ready',detail:source,done:report.claims.length>0,icon:voice?Mic:FileText},
  {label:located?'Location mapped':'Confirm location',detail:located?'Event location':'Needs review',done:located,icon:MapPin},
  {label:teams?'Team assigned':finished?'Work finished':report.status==='resolved'?'Teams released':'Awaiting team',detail:teams?`${teams} ${teams===1?'team':'teams'}`:'No active assignment',done:teams>0,icon:UsersRound},
  {label:routed?'Route ready':finished?'Route completed':'Route pending',detail:routed?'Reported blockages avoided':'No active route',done:!!routed,icon:Route},
 ];
 return <ol className="response-journey" aria-label="Report to response status">{steps.map(({label,detail,done,icon:Icon})=><li key={label} className={done?'complete':'pending'}><span>{done?<Check size={13}/>:<Icon size={13}/>}<strong>{label}</strong></span><small>{detail}</small></li>)}</ol>;
}
