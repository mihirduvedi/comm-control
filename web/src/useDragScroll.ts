import {useEffect,useRef} from 'react';

// Native drag events can pause while the pointer is held still at an edge.
// Keep scrolling on animation frames until the drag leaves, ends or drops.
export function useDragScroll(){
 const ref=useRef<HTMLDivElement>(null),pointer=useRef<number|null>(null),frame=useRef(0),last=useRef(0);
 const stop=()=>{cancelAnimationFrame(frame.current);frame.current=0;pointer.current=null;last.current=0};
 const tick=(time:number)=>{
  const el=ref.current,y=pointer.current;if(!el||y===null){stop();return}
  const bounds=el.getBoundingClientRect(),edge=Math.min(64,bounds.height/3);
  const direction=y<bounds.top+edge?-Math.min(1,(bounds.top+edge-y)/edge):y>bounds.bottom-edge?Math.min(1,(y-bounds.bottom+edge)/edge):0;
  const elapsed=last.current?Math.min(32,time-last.current):16;last.current=time;
  el.scrollTop+=direction*800*elapsed/1000;
  frame.current=requestAnimationFrame(tick);
 };
 const move=(y:number)=>{pointer.current=y;if(!frame.current)frame.current=requestAnimationFrame(tick)};
 useEffect(()=>{
  window.addEventListener('dragend',stop);window.addEventListener('drop',stop);
  return()=>{stop();window.removeEventListener('dragend',stop);window.removeEventListener('drop',stop)};
 },[]);
 return {ref,move,stop};
}
