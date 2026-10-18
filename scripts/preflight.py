#!/usr/bin/env python3
import json,shutil,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from server.models import provider_status,free_tier_confirmed
ROOT=Path(__file__).resolve().parents[1]
checks={'frontend_built':(ROOT/'web/dist/index.html').exists(),'ffmpeg_installed':bool(shutil.which('ffmpeg')),'provider_key_configured':provider_status()['configured'],'free_tier_confirmed':free_tier_confirmed(),'no_local_weights':not any((ROOT/'models').glob('*.gguf')) and not any((ROOT/'models').glob('*.bin')),'space_gib':round(shutil.disk_usage(ROOT).free/1024**3,1),'local_speech_helper':bool(shutil.which('say')),'requires_internet_for_ai':True}
print(json.dumps(checks,indent=2))
if not all(checks[k] for k in ['frontend_built','ffmpeg_installed','provider_key_configured','free_tier_confirmed','no_local_weights']):raise SystemExit(1)
