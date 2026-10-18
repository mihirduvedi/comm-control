# v6.6 verification

Verified October 17, 2026 on the user's laptop.

- Backend: **241 passed**, one existing Starlette/httpx deprecation warning.
- Browser: **45 distinct checks passed** on the final build. The final broad run passed 40; the five-test dispatch group then passed after updating its assertion for the revised assignment label. Four hosted speech/model checks were intentionally skipped. This release does not claim a new hosted speech or extraction result.
- Frontend production build and both formatting tests passed.
- Accessibility: no serious or critical findings in the checked queue views and workspace flows. Static UI inspection found no errors and one heuristic warning about glass styling; rendered panels were inspected against the user's requested design.
- Visually inspected location picking, case timeline, City/USC queues and the mobile queue controls. The mobile proof is a viewport capture, avoiding full-page compositor stitching artifacts.
- The running app on port 8765 serves the verified staged build. Both world-scoped queue endpoints respond, and session metadata reports 100 per workspace. Browser reload shows the existing 10 City callers as **10 of 100**.
- A private SQLite backup preceded restart. **All 17 report IDs and 27 source objects were retained; original claim evidence and source hashes remain unchanged.** No actual run reset, report deletion or queue dispatch was performed for verification.

Queue regressions cover persistence/reload, optimistic versions, capability and world guards, paused reservations, finish/advance, blocked-head hold and supported reopening, failed reassignment retaining its original allocation, manual release reconciliation, City additional coverage and USC work completion. Incident regressions cover atomic linked removal, restoration, evidence retention and closure retention. Intake checks distinguish explicit fresh starts from refresh recovery.

Evidence is under `evidence/v6-6-*`. The operator's recordings, runtime credentials, run database and backup are private and excluded from any source package.
