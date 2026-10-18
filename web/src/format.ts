/** Display units only. Stored routing and device values remain meters. */
export function miles(meters:number,detail=false):string {
 if(!Number.isFinite(meters)||meters<0)return 'Unavailable';
 const value=meters/1609.344,precision=detail ? 2 : 1,smallest=detail ? .01 : .1;
 if(value>0&&value<smallest)return `<${smallest} mi`;
 return `${value.toLocaleString('en-US',{minimumFractionDigits:precision,maximumFractionDigits:precision})} mi`;
}
export function feet(meters:number):string {
 if(!Number.isFinite(meters)||meters<0)return 'unknown';
 return `${Math.ceil(meters/0.3048).toLocaleString('en-US')} ft`;
}
export const assertionLabel=(value:string)=>({asserted:'Reported',negated:'Denied',uncertain:'Not sure',hearsay:'Secondhand',hypothetical:'Hypothetical'}[value]||value);

export const unitStatus=(value:string)=>({available:'Available',assigned:'Assigned',en_route:'En route',on_scene:'On scene',holding:'On hold',unavailable:'Unavailable'}[value]||value);
