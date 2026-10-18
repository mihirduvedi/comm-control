"""Stable fictional speaker identities. Actual source recordings are never re-voiced."""
import hashlib
OPERATOR_VOICE='hannah'
CALLER_VOICES=('autumn','troy','austin','daniel','diana')
KNOWN_VOICES={'alex rivera':'autumn','jamie chen':'troy','jordan chen':'diana','sam okafor':'austin','taylor brooks':'daniel'}

def caller_voice(name):
 identity=' '.join(name.casefold().split())
 return KNOWN_VOICES.get(identity) or CALLER_VOICES[int.from_bytes(hashlib.sha256(identity.encode()).digest()[:4],'big')%len(CALLER_VOICES)]
