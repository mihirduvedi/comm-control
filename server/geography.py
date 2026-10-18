"""Small cached OpenStreetMap atlas and directed, closure-aware route previews.

No public geocoder, traffic feed, map-tile download or emergency navigation claim.
"""
import heapq,json,math,re,time
from pathlib import Path
from collections import defaultdict
from functools import lru_cache
ROOT=Path(__file__).resolve().parents[1]

def norm(text):
 s=re.sub(r'[^a-z0-9 ]',' ',text.lower())
 for short,long in [('st','street'),('rd','road'),('ave','avenue'),('blvd','boulevard'),('n','north'),('s','south'),('e','east'),('w','west')]:s=re.sub(r'\b'+short+r'\b',long,s)
 return ' '.join(s.split())

def distance(a,b):
 lat=math.radians((a[1]+b[1])/2);return math.hypot((a[0]-b[0])*111320*math.cos(lat),(a[1]-b[1])*111320)

def point(value):return [float(value['lon']),float(value['lat'])] if isinstance(value,dict) else value

class Atlas:
 def __init__(self,raw=None):
  raw=raw or json.loads((ROOT/'data/downtown-la.osm.json').read_text());elements=raw['elements'];self.elements={(e['type'],e['id']):e for e in elements};self.nodes={e['id']:[e['lon'],e['lat']] for e in elements if e['type']=='node'}
  self.graph=defaultdict(list);self.edges={};self.way_edges=defaultdict(list);self.streets=defaultdict(set);self.at_node=defaultdict(set);self.restrictions=defaultdict(list);self.unmodeled_restrictions=0;self.places=[]
  for e in elements:
   t=e.get('tags',{})
   if e['type']!='way' or 'highway' not in t:continue
   if t['highway'] in ['footway','cycleway','steps','path','pedestrian','construction','proposed','track'] or t.get('access') in ['private','no'] or t.get('motor_vehicle') in ['no','private'] or t.get('motorcar')=='no':continue
   name=t.get('name',t.get('ref','Unnamed road'));speed={'motorway':80,'trunk':65,'primary':45,'secondary':40,'tertiary':35,'residential':30,'service':15}.get(t['highway'],30)
   maximum=re.search(r'\d+',t.get('maxspeed',''))
   if maximum:speed=min(100,int(maximum[0])*(1.609344 if 'mph' in t.get('maxspeed','') else 1))
   one=t.get('oneway:motor_vehicle',t.get('oneway','yes' if t.get('junction')=='roundabout' else 'no'))
   for a,b in zip(e['nodes'],e['nodes'][1:]):
    if a not in self.nodes or b not in self.nodes:continue
    length=distance(self.nodes[a],self.nodes[b])
    if length<.1:continue
    key=f"{e['id']}:{min(a,b)}:{max(a,b)}";edge={'id':key,'way_id':e['id'],'a':a,'b':b,'name':name,'length_m':round(length,2),'seconds':length/(max(5,speed)/3.6),'coordinates':[self.nodes[a],self.nodes[b]],'oneway':one}
    self.edges[key]=edge;self.way_edges[e['id']].append(key);self.streets[norm(name)].add(key);self.at_node[a].add(norm(name));self.at_node[b].add(norm(name))
    if one!='-1':self.graph[a].append((b,key))
    if one not in ['yes','1','true']:self.graph[b].append((a,key))
  for e in elements:
   t=e.get('tags',{})
   if t.get('type')=='restriction':
    members=e.get('members',[]);via=next((m for m in members if m['role']=='via' and m['type']=='node'),None);frm=next((m for m in members if m['role']=='from'),None);to=next((m for m in members if m['role']=='to'),None);rule=t.get('restriction:motorcar',t.get('restriction',''))
    if via and frm and to and rule and not t.get('restriction:conditional'):self.restrictions[via['ref']].append((frm['ref'],to['ref'],rule))
    else:self.unmodeled_restrictions+=1
  # Prefer identifiable public features, not every rail-platform duplicate.
  for e in elements:
   t=e.get('tags',{});name=t.get('name')
   if not name or t.get('highway') or t.get('route') or t.get('type')=='restriction':continue
   if e['type']=='node' and (t.get('railway') in ['stop','platform','subway_entrance'] or t.get('public_transport') in ['stop_position','platform']):continue
   coords=self.centroid(e)
   if not coords:continue
   score=3 if t.get('amenity') in ['townhall','library'] or t.get('building')=='train_station' else 2 if t.get('leisure')=='park' or t.get('tourism')=='museum' else 1
   self.places.append({'id':f"osm:{e['type']}:{e['id']}",'label':name,'lon':coords[0],'lat':coords[1],'accuracy':'landmark','source':'OpenStreetMap','score':score,'aliases':[name]})
  # Aliases refer to actual OSM features, never invented coordinates.
  aliases={'Los Angeles City Hall':['City Hall','LA City Hall'],'Gloria Molina Grand Park':['Grand Park'],'Union Station':['LA Union Station','Los Angeles Union Station'],'Los Angeles State Historic Park':['LA State Historic Park','State Historic Park'],'Japanese American National Museum':['JANM']}
  for p in self.places:p['aliases']+=aliases.get(p['label'],[])
  self.places.sort(key=lambda p:-p['score'])
  # Exact address nodes and named road intersections form a local geocoder.
  for e in elements:
   t=e.get('tags',{})
   if e['type']=='node' and t.get('addr:housenumber') and t.get('addr:street'):
    self.places.append({'id':f"osm:node:{e['id']}",'label':t['addr:housenumber']+' '+t['addr:street'],'lon':e['lon'],'lat':e['lat'],'accuracy':'address','source':'OpenStreetMap','score':2,'aliases':[]})
  all_nodes=set(self.graph)|{n for row in self.graph.values() for n,_ in row};parent={n:n for n in all_nodes}
  def root(n):
   while parent[n]!=n:parent[n]=parent[parent[n]];n=parent[n]
   return n
  for e in self.edges.values():
   ra,rb=root(e['a']),root(e['b'])
   if ra!=rb:parent[ra]=rb
  sizes=defaultdict(int)
  for n in all_nodes:sizes[root(n)]+=1
  largest=max(sizes,key=sizes.get) if sizes else None
  self.routable_nodes=[n for n in all_nodes if root(n)==largest]
  self.bounds=[34.035,-118.265,34.073,-118.215];self.timestamp=raw.get('osm3s',{}).get('timestamp_osm_base','unknown')

 def centroid(self,e,seen=None):
  if e['type']=='node':return self.nodes.get(e['id'])
  coords=[self.nodes[n] for n in e.get('nodes',[]) if n in self.nodes]
  if not coords:
   for m in e.get('members',[]):
    if m['type']=='way':
     w=self.elements.get(('way',m['ref']),{});coords.extend(self.nodes[n] for n in w.get('nodes',[]) if n in self.nodes)
  if not coords:return None
  return [sum(p[0] for p in coords)/len(coords),sum(p[1] for p in coords)/len(coords)]

 def street_matches(self,text):
  key=norm(text);short=re.sub(r'^(north|south|east|west) ','',key)
  return [name for name in self.streets if key==name or short==re.sub(r'^(north|south|east|west) ','',name)]

 def search(self,query,limit=8):
  key=norm(query)
  if len(key)<2:return []
  # Intersections are supported only when both named roads truly share a node.
  parts=re.split(r'\s+(?:and|at)\s+|\s*[&@/]\s*',query,flags=re.I)
  if len(parts)==2:
   aa=set(self.street_matches(parts[0]));bb=set(self.street_matches(parts[1]));candidates=[]
   for node,names in self.at_node.items():
    if names&aa and names&bb:
     c=self.nodes[node]
     if not any(distance(c,point(x))<40 for x in candidates):candidates.append({'id':'osm:intersection:'+str(node),'label':parts[0].strip()+' & '+parts[1].strip(),'lon':c[0],'lat':c[1],'accuracy':'intersection','source':'OpenStreetMap','score':3})
   if candidates:return candidates[:limit]
  ranked=[]
  for p in self.places:
   names=[norm(p['label'])]+[norm(a) for a in p.get('aliases',[])];score=max([100 if key==n else 70 if key in n else 45 if all(w in n.split() for w in key.split()) else 0 for n in names])+p['score']
   if score>40:ranked.append((score,p))
  result=[]
  for _,p in sorted(ranked,key=lambda x:-x[0]):
   if any(distance(point(p),point(old))<220 and (norm(p['label'])==norm(old['label']) or 'union station' in key) for old in result):continue
   result.append({k:v for k,v in p.items() if k not in ['score','aliases']})
   if len(result)>=limit:break
  return result

 def resolve(self,raw,context=''):
  # Search only source-supported place words, scoped to this atlas.
  matches=self.search(raw)
  exact=[p for p in matches if norm(raw)==norm(p['label']) or any(norm(raw)==norm(a) for x in self.places if x['id']==p['id'] for a in x.get('aliases',[])) or p['accuracy']=='intersection']
  if exact and all(distance(point(exact[0]),point(p))<250 for p in exact):return {'status':'proposed_match','geo':exact[0],'candidate_places':[]}
  if len(matches)==1:return {'status':'proposed_match','geo':matches[0],'candidate_places':[]}
  if matches:return {'status':'ambiguous','geo':None,'candidate_places':matches}
  # Match unique named landmarks inside a longer literal phrase.
  contained=[];whole=norm(raw)
  for p in self.places:
   if any(len(norm(a))>=7 and re.search(r'\b'+re.escape(norm(a))+r'\b',whole) for a in p['aliases']):
    if not any(distance(point(p),point(x))<220 for x in contained):contained.append(p)
  if len(contained)==1:return {'status':'proposed_match','geo':{k:v for k,v in contained[0].items() if k not in ['score','aliases']},'candidate_places':[]}
  return {'status':'ambiguous' if contained else 'unlocated','geo':None,'candidate_places':[{k:v for k,v in p.items() if k not in ['score','aliases']} for p in contained[:8]]}

 def nearest(self,coords,max_distance=350):
  if not self.routable_nodes:raise ValueError('No road graph available')
  node=min(self.routable_nodes,key=lambda n:distance(coords,self.nodes[n]));gap=distance(coords,self.nodes[node])
  if gap>max_distance:raise ValueError('Location is outside the loaded routing area or too far from a supported road. Load an area or confirm another access point.')
  return node,gap

 def allowed(self,node,previous,to_way,previous_node=None,next_node=None):
  for frm,to,rule in self.restrictions.get(node,[]):
   if rule=='no_u_turn' and previous==frm and to_way==to:
    if next_node==previous_node:return False
    continue
   if previous==frm and (rule.startswith('no_') and to_way==to or rule.startswith('only_') and to_way!=to):return False
  return True

 def _path(self,start,end,excluded,penalized=None):
  queue=[(0.,0.,start,0,0)];best={(start,0,0):0.};came={};goal=None;penalized=penalized or set()
  while queue:
   _,cost,node,previous,previous_node=heapq.heappop(queue);state=(node,previous,previous_node)
   if cost!=best.get(state):continue
   if node==end:goal=state;break
   for nxt,key in self.graph.get(node,[]):
    if key in excluded:continue
    edge=self.edges[key];way=edge['way_id']
    if previous and not self.allowed(node,previous,way,previous_node,nxt):continue
    step=edge['seconds']*(3 if key in penalized else 1)+(3 if previous and previous!=way else 0);total=cost+step;new=(nxt,way,node)
    if total<best.get(new,float('inf')):
     best[new]=total;came[new]=(state,key);heuristic=distance(self.nodes[nxt],self.nodes[end])/36.;heapq.heappush(queue,(total+heuristic,total,nxt,way,node))
  if goal is None:return None
  nodes=[end];keys=[]
  while goal!=(start,0,0):old,key=came[goal];keys.append(key);nodes.append(old[0]);goal=old
  return list(reversed(nodes)),list(reversed(keys))

 def route(self,origin,destination,excluded=None,alternatives=True):
  excluded=set(excluded or []);start,sgap=self.nearest(point(origin));end,egap=self.nearest(point(destination));path=self._path(start,end,excluded)
  if not path:return {'status':'no_route','reason':'No supported road route avoids the active reported closures. Review access before assigning another route.','routes':[]}
  paths=[path]
  if alternatives and path[1]:
   alt=self._path(start,end,excluded,set(path[1]));
   if alt and alt[1]!=path[1] and len(set(alt[1])-set(path[1]))>=1:paths.append(alt)
  routes=[]
  for index,(nodes,keys) in enumerate(paths):
   steps=[];meters=0.;seconds=0.
   for key in keys:
    edge=self.edges[key];meters+=edge['length_m'];seconds+=edge['seconds']
    if steps and steps[-1]['road']==edge['name']:steps[-1]['distance_m']+=round(edge['length_m']);steps[-1]['edge_ids'].append(key)
    else:steps.append({'road':edge['name'],'distance_m':round(edge['length_m']),'edge_ids':[key]})
   routes.append({'id':('recommended' if index==0 else 'alternative'),'coordinates':[self.nodes[n] for n in nodes],'edge_ids':keys,'distance_m':round(meters),'travel_seconds':round(seconds),'steps':steps,'start_gap_m':round(sgap),'end_gap_m':round(egap)})
  return {'status':'ready','routes':routes,'generated_at':time.time(),'excluded_edge_count':len(excluded),'source':'OpenStreetMap road extract','data_timestamp':self.timestamp,'limitations':['Preview only; verify road access. No live traffic or emergency vehicle restrictions.','Conditional and via-way turn restrictions are not fully modeled.','Dotted endpoint gaps are not driving directions.']}

 def closure_edges(self,raw,near=None):
  text=norm(raw);names=[]
  for name in self.streets:
   short=re.sub(r'^(north|south|east|west) ','',name)
   if len(short)>5 and (re.search(r'\b'+re.escape(name)+r'\b',text) or re.search(r'\b'+re.escape(short)+r'\b',text)):names.append(name)
  subjects=[name for name in names if re.search(r'\b'+re.escape(re.sub(r'^(north|south|east|west) ','',name))+r'\s+(?:is|was|has been)\s+(?:blocked|closed|obstructed|impassable|clear|cleared|open|reopened|passable)\b',text)]
  if subjects:names=subjects
  elif len({re.sub(r'^(north|south|east|west) ','',n) for n in names})>1:return []
  keys=set(k for name in names for k in self.streets[name])
  if near and keys:
   best=min(keys,key=lambda k:min(distance(point(near),c) for c in self.edges[k]['coordinates']));e=self.edges[best]
   # Both directed halves share one segment ID. Adjacent carriageway within 25 m is excluded too.
   midpoint=[sum(c[0] for c in e['coordinates'])/2,sum(c[1] for c in e['coordinates'])/2]
   nearby=[k for k in keys if min(distance(midpoint,c) for c in self.edges[k]['coordinates'])<25]
   return nearby[:8]
  return []

 @lru_cache(maxsize=1)
 def public(self):return {'name':'Downtown Los Angeles','bounds':self.bounds,'center':[-118.2437,34.0543],'source':'OpenStreetMap','copyright_url':'https://www.openstreetmap.org/copyright','license':'ODbL-1.0','data_timestamp':self.timestamp,'nodes':len(self.routable_nodes),'segments':len(self.edges),'turn_restrictions':sum(map(len,self.restrictions.values())),'unmodeled_restrictions':self.unmodeled_restrictions,'places':self.search('City Hall',3)+self.search('Union Station',3)+self.search('Grand Park',3),'routing_scope':'Cached Downtown LA road network. Map browsing is worldwide; routing requires loaded road coverage.'}

@lru_cache(maxsize=1)
def atlas():return Atlas()
