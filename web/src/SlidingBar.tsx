import {useLayoutEffect,useRef,useState} from 'react';
import type {HTMLAttributes,ReactNode} from 'react';

export function SlidingBar({as:Tag='div',children,className='',...props}:HTMLAttributes<HTMLElement>&{as?:'div'|'nav';children:ReactNode}){
 const ref=useRef<HTMLElement|null>(null);
 const [box,setBox]=useState<{left:number;top:number;width:number;height:number}|null>(null);
 useLayoutEffect(()=>{
  const bar=ref.current;if(!bar)return;
  const measure=()=>{
   const selected=bar.querySelector<HTMLElement>(':scope > .active,:scope > [aria-selected="true"],:scope > [aria-current="page"]');
   if(!selected){setBox(null);return}
   const r=selected.getBoundingClientRect(),p=bar.getBoundingClientRect();
   const next={left:r.left-p.left+bar.scrollLeft-bar.clientLeft,top:r.top-p.top+bar.scrollTop-bar.clientTop,width:r.width,height:r.height};
   setBox(old=>old&&Object.keys(next).every(key=>Math.abs(old[key as keyof typeof old]-next[key as keyof typeof next])<.25)?old:next);
  };
  measure();const resize=new ResizeObserver(measure);resize.observe(bar);for(const child of bar.children)resize.observe(child);
  const change=new MutationObserver(measure);change.observe(bar,{subtree:true,childList:true,attributes:true,attributeFilter:['class','aria-selected','aria-current']});
  let active=true;void document.fonts.ready.then(()=>{if(active)measure()});
  return()=>{active=false;resize.disconnect();change.disconnect()};
 },[]);
 return <Tag {...props} ref={el=>{ref.current=el}} className={'sliding-bar '+className}>{box&&<span aria-hidden="true" className="sliding-selection" style={{transform:`translate(${box.left}px,${box.top}px)`,width:box.width,height:box.height}}/>}{children}</Tag>;
}
