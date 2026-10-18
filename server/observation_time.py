"""Conservative source-relative time normalization. Receipt is never observation."""
import re
from datetime import datetime

def epoch(value):
 if isinstance(value,(int,float)):return float(value)
 return datetime.fromisoformat(value.replace('Z','+00:00')).timestamp()

def observation_time(claims,captured_at):
 # Only explicit source time claims are normalized. No guessed date/timezone.
 for c in claims:
  if c['kind']!='event_time' or c['assertion']!='asserted':continue
  raw=c['excerpt'];text=raw.lower()
  match=re.search(r'\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+(minutes?|hours?)\s+ago\b',text)
  if match:
   numbers={'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,'seven':7,'eight':8,'nine':9,'ten':10}
   n=int(match[1]) if match[1].isdigit() else numbers[match[1]]
   return {'observed_at':captured_at-n*(3600 if match[2].startswith('hour') else 60),'observation_time_status':'relative_source','observation_time_raw':raw}
  if re.search(r'\b(?:right now|just now|currently|now)\b',text):
   return {'observed_at':captured_at,'observation_time_status':'source_current','observation_time_raw':raw}
 return {'observed_at':None,'observation_time_status':'unknown','observation_time_raw':next((c['excerpt'] for c in claims if c['kind']=='event_time'),'')}
