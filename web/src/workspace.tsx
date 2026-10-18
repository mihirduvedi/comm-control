import {createContext,useContext} from 'react';
export type World='city'|'usc';
export const WorkspaceContext=createContext<{world:World;setWorld:(world:World)=>void}>({world:'city',setWorld:()=>{}});
export const useWorkspace=()=>useContext(WorkspaceContext);
export function readWorld():World{
 const q=new URLSearchParams(location.search);
 if(q.get('world')==='city')return 'city';
 if(q.get('world')==='usc'||['usc','site'].includes(q.get('view')||''))return 'usc';
 try{return localStorage.getItem('comm-workspace')==='usc'?'usc':'city'}catch{return 'city'}
}
export function workspaceHref(path:string,world:World){
 const u=new URL(path,location.origin);u.searchParams.set('world',world);
 if(u.pathname==='/resources'){u.searchParams.delete('view');if(world==='usc')u.searchParams.set('view','usc')}
 return u.pathname+u.search+u.hash;
}
