# Quiet shift desk

The desk helps an operator see the incident, the next decision and the map without reading every detail at once. Keep the known queue / case map / response-plan structure and all working handlers.

Chosen direction: mixed-tone work zones. A deep teal header (#173d46) anchors navigation, a mist-blue queue (#e7eff3) groups incoming work and a sage response pane (#e3eee8) holds the plan. White is reserved for source text, editable fields and selected evidence. Category colors still mean fire/coral, medical/blue, access/amber, safety/violet, assistance/teal and information/gray. Severity uses words/icons as well as color. No animated alarms or decorative effects.

Alternatives considered: a fully dark desk gives the bright street map too much contrast; a full-map overlay hides unresolved tasks. Mixed light work zones keep readable type and familiar structure while reducing glare. Creative risk: dark header plus tinted large panels; check contrast, focus and dense content rather than adding ornamental colors.

Dominant rule: spatial/color grouping for each job, with fewer nested boxes. Counter-rule: urgent review stays warm amber and source/edited text remains white. Signature: a live call appears as a clearly provisional ring on the real map, then becomes a categorized received incident after review/delivery.

Reduce visible detail: only the selected queue row expands its status line. Put prepared message tools in a Messages disclosure, keep the fixed Respond action, and show short review reasons with the full text in Review. Cut redundant uppercase labels and repeated simulation prose while keeping disclosures at actions that need them. Do not rewrite literal caller quotes, already-approved messages or source history.

Typography remains native system sans, 22–24px incident title, 13–14px main content and at least 11px metadata. No new fonts or image assets. Type sizes, padding and targets wrap at1280/800/390, with vertical scrolling rather than clipped map attribution. Keyboard/focus and existing URL/deep-link/session behavior remain.

Calculated route distance/step labels use miles, device accuracy feet; API/OSM storage stays in meters. Quoted/spoken units are preserved verbatim. Live audio uses the existing free hosted provider, no browser speech service or new downloaded model. Chunks are cumulative actual audio, throttled, never synthetic transcript fallback. Interim pins are candidates, never dispatch or confirmed facts. Final extraction and review precede the existing simulated receive/assignment flow.

Research principles: Prepared's emphasis on key call details (https://www.prepared911.com/), W3C readable contrast and redundant cues (https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html), Groq's file transcription contract (https://console.groq.com/docs/speech-to-text), and MDN's browser-dependent interim speech behavior (https://developer.mozilla.org/en-US/docs/Web/API/SpeechRecognition/interimResults). Use bounded cumulative hosted transcription to avoid relying on an additional browser speech provider. New interface copy is plain and specific.
