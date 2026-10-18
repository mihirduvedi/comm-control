"""Cached USC pedestrian geometry. Public map data, never certified indoor egress."""
import json,math,heapq,re,hashlib
from pathlib import Path
from functools import lru_cache
ROOT=Path(__file__).resolve().parents[1]
def distance(a,b):
 x=(a[0]-b[0])*math.cos(math.radians((a[1]+b[1])/2));y=a[1]-b[1];return math.hypot(x,y)*111195
CATALOG=[('sgm',406923936,'Seeley G. Mudd Building','SGM',['seeley g mudd','seeley mudd','sgm']),('michelson',555848401,'Michelson Center for Convergent Biosciences','MCB',['michelson center','michelson','mcb']),('seaver',406923894,'Frank R. Seaver Science Center','SSC',['seaver science center','seaver science','ssc']),('kaprielian',406923906,'Kaprielian Hall','KAP',['kaprielian hall','kaprielian','kap']),('leavey',406923908,'Leavey Library','LVL',['leavey library','leavey','lvl']),('tutor',154906751,'Ronald Tutor Campus Center','TCC',['tutor campus center','ronald tutor campus center','tcc']),('bovard',406923885,'Bovard Administration Building','ADM',['bovard administration','bovard','adm']),('hughes',406923899,'Hughes Aircraft Electrical Engineering Center','EEB',['hughes aircraft electrical engineering','hughes center','eeb'])]
@lru_cache(maxsize=1)
def atlas():
 raw=json.loads((ROOT/'data/usc-campus.osm.json').read_text());nodes={str(e['id']):[e['lon'],e['lat']] for e in raw['elements'] if e['type']=='node'};ways={e['id']:e for e in raw['elements'] if e['type']=='way'};buildings=[]
 for slug,oid,name,code,aliases in CATALOG:
  way=ways[oid];coords=[nodes[str(n)] for n in way['nodes'] if str(n) in nodes];center=[sum(p[0] for p in coords[:-1])/len(coords[:-1]),sum(p[1] for p in coords[:-1])/len(coords[:-1])]
  buildings.append({'id':'usc-'+slug,'name':name,'code':code,'aliases':aliases,'center':center,'footprint':coords,'osm_id':oid,'source':'https://www.openstreetmap.org/way/'+str(oid)})
 graph={};edges=[]
 for way in ways.values():
  tags=way.get('tags',{})
  if tags.get('highway') not in ['footway','path','pedestrian','service','residential','living_street','steps'] or tags.get('foot')=='no' or tags.get('access')=='no':continue
  for a,b in zip(way['nodes'],way['nodes'][1:]):
   a,b=str(a),str(b)
   if a not in nodes or b not in nodes:continue
   length=distance(nodes[a],nodes[b]);id=str(way['id'])+':'+a+':'+b;edge={'id':id,'a':a,'b':b,'coordinates':[nodes[a],nodes[b]],'name':tags.get('name') or ('Steps' if tags['highway']=='steps' else 'Mapped campus path'),'distance_m':length}
   edges.append(edge);graph.setdefault(a,[]).append((b,length,id));graph.setdefault(b,[]).append((a,length,id))
 access=[]
 for e in raw['elements']:
  tags=e.get('tags',{})
  if e['type']=='node' and tags.get('entrance'):
   p=nodes[str(e['id'])];near=min(buildings,key=lambda b:distance(p,b['center']))
   if distance(p,near['center'])<=100:access.append({'id':'osm-entry-'+str(e['id']),'name':near['code']+' · mapped '+('main entrance' if tags['entrance']=='main' else 'access point'),'kind':'entrance','position':p,'building_id':near['id'],'evidence':'OSM entrance tag; access and exit suitability unverified','source':'https://www.openstreetmap.org/node/'+str(e['id'])})
 # Official named perimeter access points. Positions are approximate road intersections.
 gates=[('mccarthy','McCarthy Way Entrance',[-118.28122,34.02136]),('mcclintock','McClintock Avenue Entrance',[-118.28723,34.02508]),('watt','Watt Way Entrance',[-118.28734,34.01846]),('downey','Downey Way Entrance',[-118.29125,34.02213])]
 for slug,name,p in gates:access.append({'id':'usc-gate-'+slug,'name':name,'kind':'campus_access','position':p,'building_id':None,'evidence':'USC named entrance; approximate map position, current access unverified','source':'https://transnet.usc.edu/index.php/about-us/entrance-hours/'})
 return {'buildings':buildings,'nodes':nodes,'edges':edges,'graph':graph,'access_points':access}
def resolve(raw):
 text=re.sub(r'[^a-z0-9 ]',' ',raw.lower());matches=[b for b in atlas()['buildings'] if any(re.search(r'\b'+re.escape(a)+r'\b',text) for a in b['aliases'])]
 return matches

def nearest(p):return min(atlas()['graph'],key=lambda n:distance(p,atlas()['nodes'][n]))
def route(origin,destination,blocked):
 a=atlas();start=nearest(origin);finish=nearest(destination);queue=[(0,start)];prev={};best={start:0};blocked=set(blocked)
 while queue:
  cost,node=heapq.heappop(queue)
  if cost!=best[node]:continue
  if node==finish:break
  for other,length,eid in a['graph'][node]:
   if eid in blocked:continue
   total=cost+length
   if total<best.get(other,float('inf')):best[other]=total;prev[other]=(node,eid);heapq.heappush(queue,(total,other))
 if finish not in best:return {'status':'no_route','coordinates':[],'edge_ids':[],'distance_m':0,'arrival_gap_m':None,'note':'No connected open path in the cached campus graph.'}
 ns=[finish];ids=[]
 while ns[-1]!=start:
  parent,eid=prev[ns[-1]];ids.append(eid);ns.append(parent)
 coords=[a['nodes'][n] for n in reversed(ns)];gap=distance(coords[-1],destination)
 if gap>100 or distance(coords[0],origin)>100:return {'status':'no_route','coordinates':[],'edge_ids':[],'distance_m':0,'arrival_gap_m':round(gap),'note':'Mapped path is too far from the reported building or team position.'}
 return {'status':'ready','coordinates':coords,'edge_ids':list(reversed(ids)),'distance_m':round(best[finish]),'arrival_gap_m':round(gap),'note':'Outdoor pedestrian preview on cached OSM paths. Dotted arrival gap is unmapped. No indoor egress, accessibility or vehicle access certification.'}

def public():
 a=atlas();return {'context_buildings':[[a['nodes'][str(n)] for n in e['nodes'] if str(n) in a['nodes']] for e in json.loads((ROOT/'data/usc-campus.osm.json').read_text())['elements'] if e['type']=='way' and e.get('tags',{}).get('building')], 'name':'USC · University Park','buildings':a['buildings'],'access_points':a['access_points'],'paths':a['edges'],'bounds':[[-118.292,34.015],[-118.278,34.026]],'center':[-118.285,34.021],'sources':[{'title':'USC Facilities campus map','url':'https://fpm.usc.edu/wp-content/uploads/2022/09/UPC_BaseMapGrid_36x48_20220906.pdf'},{'title':'USC entrance information','url':'https://transnet.usc.edu/index.php/about-us/entrance-hours/'},{'title':'OpenStreetMap contributors','url':'https://www.openstreetmap.org/copyright'}],'note':'Real building names and mapped geometry. Reports, readings, assets and teams are simulated. Indoor exits have not been surveyed.'}
