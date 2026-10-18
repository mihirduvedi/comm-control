# Incident desk design and behavior contract

Thesis: show a dispatcher what happened, what automation handled and which decisions still need attention.

Chosen structure: category-grouped queue on the left, a concise location/needs/time brief above a real-world map, and a distinct Response plan / Evidence panel. Keep the existing source inspector in Evidence. Alternatives considered: floating cards on a full map hide obligations; equal category columns shrink geography and the selected case. This structure preserves the useful queue/map/inspector relationship.

Semantic color: fire coral (#B54735 on #FFF0EB), medical blue (#2460AA on #EEF5FF), access amber (#9A6200 on #FFF6DF), safety violet (#6945A4 on #F4F0FC), service teal (#167265 on #EAF7F3). Category is separate from severity. Critical has a red word/icon, review amber, completed green, selected controls navy. Every color has a text/icon equivalent. No alarm animation or automatic sound.

White queue/map, pale gray canvas, lightly tinted plan panel, 12px gaps and 6–10px corners. One selected incident and response plan dominate. An amber unresolved location/route/resource item may interrupt. Signature: Handled automatically / Needs review ledger with reasons. Avoid identical cards around every fact.

Native system sans; 22px title, 14px body, 12–13px metadata; tabular clock. New copy uses sentence case without decorative phrase separators. Literal source quotes stay exact. Header shows live local date, seconds and named timezone.

≥1280px: queue280 / flexible center / plan360. 1024–1279px:250 / flexible /340. Below1024 use explicit Queue / Map / Plan tabs. At390px one column, wrapped controls and no horizontal page overflow; primary targets44px. Enlarged CSS-space retains a visible primary action. Keyboard list alternatives accompany map markers/routes.

Preserve routes, deep links, capabilities, source privacy, immutable origins, received-only evidence, optimistic versions, approvals, indexed-device receipts, recipient reactions/replies, retry/expiry and legacy fictional site mode. Never replace the working backend with decorative data.

Behavior contracts:
- Received located report: categorize and summarize; choose capable available demo units; compute road routes; persist plan/assignment/action reasons. Unresolved location means review, never a fake pin.
- Reported blocked road: match named segment near a supported location; retain source/expiry; recompute routes. Vague road means review. Exclude active reported closures and label them unverified reports.
- Map/place selection: local OSM place, address and intersection catalog; confirmation with provenance/reason. No public generic geocoder and no confidential-call forwarding.
- Close/reopen road: recompute alternatives against closure version. No path means blocked/review, never a straight-line driving route.
- Unit actions: versioned demo assignment/status, no double assignment.
- Caller update: prefill existing reviewed composer; preserve exact approval/audience/transport.
- Escalation: idempotent internal supervisor task, no external service contacted.
- Contact/public announcement: editable audience/text, approve to local demo board; no SMS/call/public channel configured.

Research principles: Prepared assistive dispatch highlights call details; Zello separates map from conversation/unit status; accessibility uses labels/focus/reflow/color alternatives. These are principles, not copied screens or interoperability claims. OpenStreetMap attribution stays visible. Cached local road extract is small and not live traffic. Public tiles are online and have no availability guarantee.

QA covers receive → categorized brief → route/action ledger → evidence → reviewed return. Check directed roads/turn restrictions, closures/detour/no path, duplicate delivery, exhausted units, correction/restart/stale versions, audience-bound approvals, actual map tiles/routes and1440/1280/800/390 renders plus keyboard/reflow.
