"""Rebuild fictional voice fixtures with natural generated voices; no human impersonation.
Run after accepting the Orpheus terms in your Groq account. Reuses generated clips.
"""
import asyncio,json,sys,subprocess,shutil,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from server.speech import render_speech,MODEL
SAMPLES={
 'city-report.aiff':('autumn','There is smoke near City Hall. Two people are outside. I do not know if anyone is still inside. Main Street is blocked at Temple Street. Please send fire support.'),
 'city-operator.aiff':('hannah','Tell the people at City Hall to stay outside. Do not use Main Street. Ask whether anyone is still inside.'),
 'warehouse.aiff':('autumn','There is smoke coming from the electrical room in the east warehouse. Two people are outside. I do not know if anyone is still inside. The north gate is blocked. Please send fire support.'),
 'operator.aiff':('hannah','Tell them to stay outside the east warehouse. Do not use the north gate. Ask whether anyone is still inside.'),
 'answer.aiff':('autumn','I cannot see inside the east warehouse. Two people are outside. I still do not know if anyone is inside.')}
async def main():
 backup=ROOT/'work/v5-original-fixtures';backup.mkdir(parents=True,exist_ok=True);manifest=[]
 for name,(voice,text) in SAMPLES.items():
  target=ROOT/'fixtures'/name
  if target.exists() and not (backup/name).exists():shutil.copyfile(target,backup/name)
  wav=await render_speech(text,ROOT/'work/v5-demo-voices',voice)
  subprocess.run(['ffmpeg','-v','error','-y','-i',str(wav),'-ar','24000','-ac','1',str(target)],check=True)
  manifest.append({'file':name,'voice':voice,'text':text,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'origin':'Generated speech, fictional demonstration. Not a human recording.','model':MODEL,'speaker':'Operator' if name in ['city-operator.aiff','operator.aiff'] else 'Alex Rivera'})
  if name in ['city-report.aiff','warehouse.aiff']:
   capture=ROOT/'fixtures'/('city-capture.wav' if name.startswith('city') else 'warehouse-capture.wav')
   if capture.exists() and not (backup/capture.name).exists():shutil.copyfile(capture,backup/capture.name)
   subprocess.run(['ffmpeg','-v','error','-y','-i',str(wav),'-af','apad=whole_dur=15','-t','15','-ar','48000','-ac','1',str(capture)],check=True)
 # Update the legacy normalized clip used in earlier demonstrations.
 source=ROOT/'fixtures/warehouse.aiff';normalized=ROOT/'fixtures/warehouse.normalized.wav'
 if normalized.exists() and not (backup/normalized.name).exists():shutil.copyfile(normalized,backup/normalized.name)
 subprocess.run(['ffmpeg','-v','error','-y','-i',str(source),'-ar','16000','-ac','1',str(normalized)],check=True)
 (ROOT/'fixtures/voice-provenance.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print('Refreshed',len(manifest),'fictional voice samples; original fixtures retained under work/.')
if __name__=='__main__':asyncio.run(main())
