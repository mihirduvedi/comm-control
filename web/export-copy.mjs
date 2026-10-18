import fs from 'node:fs';
import {parse} from '@babel/parser';
const copy=new Set();
function add(value){const s=value.replace(/\s+/g,' ').trim();if(s&&/[A-Za-z]/.test(s)&&!s.includes('className')&&!s.startsWith('/api/')&&!s.startsWith('http'))copy.add(s)}
function visit(node,parent){
 if(!node||typeof node!=='object')return;
 if(node.type==='JSXText')add(node.value);
 if(node.type==='StringLiteral'){
  const attr=parent?.type==='JSXAttribute'?parent.name?.name:null;
  if(['aria-label','title','placeholder','alt'].includes(attr))add(node.value);
  else if(/^[A-Z][a-zA-Z ’'?,.:;()&!-]*(?:\s|\?)/.test(node.value)&&!/[{}<>/]/.test(node.value)&&node.value.length<650)add(node.value);
 }
 for(const [key,value]of Object.entries(node)){if(['loc','start','end','extra','comments','tokens'].includes(key))continue;if(Array.isArray(value))value.forEach(child=>visit(child,node));else if(value&&typeof value==='object')visit(value,node)}
}
for(const name of fs.readdirSync('src').filter(name=>/\.tsx?$/.test(name))){const ast=parse(fs.readFileSync('src/'+name,'utf8'),{sourceType:'module',plugins:['typescript','jsx']});visit(ast,null)}
fs.writeFileSync('../../../outputs/Comm_Control_UI_Copy.md',[...copy].join('\n\n')+'\n');console.log('Saved current product copy. Literal runtime reports and approved messages were not rewritten.');
