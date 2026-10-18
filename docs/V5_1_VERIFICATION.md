# Comm Control v5.1 verification

October 17, 2026, on the user's Mac. Mutating tests used the dedicated 8766/.data-browser-tests environment; the actual app's eight reports were retained.

- Python backend: 147 passed in 24.26 seconds. One existing Starlette/httpx deprecation warning.
- Main Chrome suite: 22 passed in 48.2 seconds. Includes fixed natural operator playback through Groq, private cached replay and Stop; no voice picker; stable saved caller identities; native compatibility; auth/access-link behavior; case lifecycle; source/dispatch/intake/recovery flows; responsive and serious/critical axe checks.
- Final desktop/tablet/mobile polish scenario: 1 passed in 7.2 seconds after the root layout fix. Verified exact desktop viewport fit, no horizontal status border, no queue pseudo-element strips, no selected colored inset shadow, rounded panes, near-white canvas and persistent speaker metadata.
- TypeScript/Vite build: pass, largest JS chunk about 360 kB; no large-chunk advisory.
- Static heuristic: 25 files, 0 errors. One aesthetic warning for repeated backdrop blur is intentional under the explicit user glass request. Surfaces were visually inspected, contrast checked and reduced-transparency/unsupported-filter fallbacks supplied.
- Actual runtime: restarted locally with voice metadata migration and preserved records; authorized workspace reopened in the user's in-app browser.
- Release: clean source boot, built assets, required OSM data, archive integrity/per-file hashes and exact-known-secret scan verified during packaging. No private env/runtime/dependency caches included.

The whiter background initially exposed routine queue text at 4.3:1 contrast. That text was darkened and final axe checks passed. The floating header's collapsed outer margin initially added page height; flow-root now prevents this and the desktop-height assertion passes.

Current speaker rule: operator Hannah; Alex Autumn; Jamie Troy; Jordan Diana; Sam Austin; Taylor Daniel. Other names use a stable deterministic assignment saved on the session. Existing source recordings remain untouched. Demo fixtures record their synthetic speaker/voice, exact script/model and audio hash. The server ignores client voice override parameters for instruction playback.

Screenshots of exact final desktop/tablet/mobile glass and fixed-voice recipient states were inspected. No claim of real-device, VoiceOver, physical-radio, human listening/usability or emergency deployment validation. New spoken generations still need human review; visible exact text stays authoritative. The actual source audio is retained separately from generated demo speech.
