# Validation and scope

The recorded project verification reports **241 backend tests** and **45 distinct browser checks** passed, plus the frontend production build and two formatting tests. Four hosted speech/model checks were skipped in that release.

The publication check built the source copy and reran the browser-access regression group and formatting tests successfully. Before the build, one access test correctly failed because the frontend assets weren't present; the setup guide now makes the build prerequisite explicit.

## What the checks cover

- Source and correction retention, including recovery after removal of an incident.
- Separate City and USC reports, resources, sessions and queues.
- Missing locations and unsupported routes holding allocation for review.
- Capability checks, queue persistence, stale-edit rejection and failed reassignment retaining its original assignment.
- Current closure checks at the next queued stop, with stale closures remaining excluded.
- Fresh voice-intake starts versus recovery after a browser refresh.
- Delivery and acknowledgment as separate states.

Earlier connected tests used fictional/generated speech with the actual hosted provider. The public demo now supports a bounded, explicitly enabled Free-tier voice path. Regression tests cover persistent caps, concurrent reservations, expiry, visitor attribution through queued extraction, alternate-entry-point denial and upload limits. Mocked provider responses in these budget tests exercise enforcement without consuming real quota. Synthetic transcript evaluations and regression tests aren't a representative speech benchmark.

## What still needs evaluation

There has been no supervised facilities pilot, operational emergency trial, live GPS validation, live-traffic validation or physical radio test. Spanish-language support and the Mexico City pilot are proposed work. The hosted model needs internet; transport simulation does not make speech processing work offline.

A useful first pilot would measure operator review time, critical interpretation and location corrections, assignment suitability, and recovery from blocked routes or failed delivery. Those outcomes need observation with users rather than being inferred from a passing test suite.

## Public voice access check

After adding the limits, all 249 backend checks passed, including eight public-demo budget and access regressions. The final frontend production build passed. A real upload of the existing fictional City Hall speech fixture through the public browser interface used two hosted calls: transcription and structured extraction. The reviewed facts and mapped City Hall candidate appeared in the interface, and the network allowance fell from 15 to 13. This is one connected integration check, not a representative accuracy benchmark. The provider billing page showed Free as the current $0 plan before enabling access.
