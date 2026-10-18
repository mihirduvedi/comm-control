"""Natural exact-text speech using the existing Free-tier provider. No local weights."""
import asyncio
import hashlib
import io
import re
import wave
from pathlib import Path
import httpx
from . import models

MODEL='canopylabs/orpheus-v1-english'
VOICES=('hannah','troy','autumn','diana','austin','daniel')
_locks={}


def chunks(text,limit=200):
 if not text.strip() or len(text)>4000:raise ValueError('Speech needs between 1 and 4,000 characters.')
 if '[' in text or ']' in text:raise ValueError('Natural speech treats brackets as voice directions. Use the local voice to read this instruction literally.')
 result=[]
 while len(text)>limit:
  prefix=text[:limit];breaks=list(re.finditer(r'[.!?](?=\s)|\s+',prefix))
  end=breaks[-1].end() if breaks else limit
  result.append(text[:end]);text=text[end:]
 if text:result.append(text)
 return result


async def render_speech(text,folder,voice='hannah'):
 if voice not in VOICES:raise ValueError('Choose an available voice.')
 parts=chunks(text)
 if not models.provider_key():raise ValueError('Natural voice needs the saved Groq key. Read the text or retry later.')
 folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
 key=hashlib.sha256((MODEL+'\0'+voice+'\0'+text).encode()).hexdigest();path=folder/(key+'.wav')
 lock=_locks.setdefault(str(path),asyncio.Lock())
 async with lock:
  if path.exists():return path
  clips=[]
  async with httpx.AsyncClient(timeout=45) as client:
   for part in parts:
    try:models.reserve_request()
    except RuntimeError as e:raise ValueError(str(e))
    try:r=await client.post(models.PROVIDER_URL+'/audio/speech',headers={'Authorization':'Bearer '+models.provider_key()},json={'model':MODEL,'input':part,'voice':voice,'response_format':'wav'})
    except httpx.HTTPError:raise ValueError('Natural voice could not connect. Read the text or retry.')
    if r.status_code==400 and 'terms' in r.text.lower():raise ValueError('Groq needs your Orpheus model terms acceptance. Open the Orpheus playground in your Groq account, then retry. The exact text is available meanwhile.')
    if r.status_code!=200:raise ValueError('Natural voice unavailable (provider '+str(r.status_code)+'). Read the text or retry later.')
    try:
     with wave.open(io.BytesIO(r.content),'rb') as w:
      fmt=(w.getnchannels(),w.getsampwidth(),w.getframerate());frames=w.readframes(w.getnframes())
      if not frames or w.getcomptype()!='NONE' or clips and fmt!=clips[0][0]:raise ValueError()
      clips.append((fmt,frames))
    except (wave.Error,EOFError,ValueError):raise ValueError('Natural voice returned invalid audio. Read the text or retry.')
  temporary=path.with_suffix('.tmp')
  with wave.open(str(temporary),'wb') as out:
   out.setnchannels(clips[0][0][0]);out.setsampwidth(clips[0][0][1]);out.setframerate(clips[0][0][2])
   for _,frames in clips:out.writeframes(frames)
  temporary.replace(path)
 return path
