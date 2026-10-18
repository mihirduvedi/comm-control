#!/usr/bin/env python3
"""One explicit, bounded OSM data import. No tile download or background scraping."""
import asyncio,json,sys,hashlib
from datetime import datetime,timezone
from pathlib import Path
import httpx
ROOT=Path(__file__).resolve().parents[1]
BBOX=[34.035,-118.265,34.073,-118.215]
async def main():
 destination=ROOT/'data/downtown-la.osm.json'
 if destination.exists():return print('Cached OSM extract exists; no request made.')
 box=','.join(map(str,BBOX))
 query=f'''[out:json][timeout:45][maxsize:33554432];(way[highway][highway!~"^(footway|cycleway|steps|path|pedestrian|construction|proposed|track)$"]({box});relation[type=restriction]({box});nwr[name][name~"Union Station|City Hall|Little Tokyo|Grand Park|Olvera|Historic Park|Japanese American National Museum|Central Library",i]({box});node["addr:housenumber"]({box}););out body;>;out skel qt;'''
 async with httpx.AsyncClient(timeout=70,trust_env=False) as c:
  r=await c.post('https://overpass-api.de/api/interpreter',data={'data':query},headers={'User-Agent':'CommControl-LocalHackathon/0.3 (bounded Los Angeles prototype data import)'})
  r.raise_for_status();raw=r.json()
 if raw.get('remark'):raise RuntimeError(raw['remark'])
 destination.write_text(json.dumps(raw,separators=(',',':')))
 manifest={'source':'https://overpass-api.de/api/interpreter','query':query,'bounds':BBOX,'downloaded_at':datetime.now(timezone.utc).isoformat(),'osm_timestamp':raw.get('osm3s',{}).get('timestamp_osm_base'),'license':'ODbL-1.0','attribution':'© OpenStreetMap contributors','copyright_url':'https://www.openstreetmap.org/copyright','sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),'bytes':destination.stat().st_size,'elements':len(raw.get('elements',[])),'scope':'Small cached road/landmark extract; not live traffic; routing preview requires operator review'}
 (ROOT/'data/downtown-la.manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps({k:manifest[k] for k in ['bytes','elements','osm_timestamp','license']}))
if __name__=='__main__':asyncio.run(main())
