# White glass desk

The user asked to remove the full-width line below dispatch status, lighten the overly blue background, contrast panels with blue borders, remove the colored vertical queue strips, assign each person one voice and modernize the interface with rounded glass panels and glass blobs, referencing Apple and the Dickman Mini Analyzer.

The current design uses a near-white #f7f9fc canvas. Broad, stationary blue/cyan light shapes sit behind translucent white panels. Blue outlines distinguish the queue, map and response areas. The floating navigation is a light glass capsule. Panel corners are 18px; assigned-unit surfaces are 13px; buttons/inputs use 10–12px. The street map and evidence remain sharp, with blur only behind reading surfaces. No ambient animation was added. Reduced-transparency and unsupported-filter fallbacks use solid white surfaces.

Dominant rule: calm white reading surfaces framed in blue. Counter-rule: semantic warning and category accents remain in icons, text and necessary review areas. Signature: a floating glass header above the working map and three rounded panes. Creative risk: visible glass without sacrificing the operational data hierarchy. The background shapes have the single job of making transparency legible, and stay fixed and low contrast.

The Dickman source theme was inspected directly at src/dickman_mini_analyzer/ui/theme.py. Its neutral white/gray palette and practical, restrained hierarchy informed this revision. Its old Qt rectangular geometry was not copied; rounded glass geometry comes from the user's current instruction. This is not a claim of an exact visual clone of an uninspected running analyzer.

Hard behavior constraints: preserve report/source/transport/case semantics, all original recordings, actual data and private browser access. Voice identity belongs to the speaker, not the recipient or message. The picker is removed. Caller assignments are saved on sessions, operator playback uses one server-enforced constant, and fictional audio fixtures use the matching speaker identity. No call recording is re-voiced.

Verify desktop/tablet/mobile reflow, contrast/keyboard, absence of status border and queue pseudo-element strips, stable voice identity across reload/restart, server prevention of voice overrides, actual natural playback/cache and existing case/dispatch/intake/auth flows. Capture and inspect the exact built app before delivery.
