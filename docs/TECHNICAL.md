# Technical walkthrough

Comm Control separates interpreting a report from deciding what to do about it. Hosted models produce a transcript and proposed claims. Local checks, map data and operator review determine whether those claims can support a response plan.

## From audio to a received incident

The browser captures microphone audio. The backend sends it to the configured speech model, then uses a structured extraction model to propose observations, requests and locations. Claims retain source excerpts and uncertainty. The operator can correct an interpretation before sending the reviewed report.

A report must reach the control center before it can create a received incident and reserve a resource. The delivery simulator makes this boundary observable: an unsent report isn't silently available at the destination. The desk's live-call preview is an explicit operator intake path, with provisional locations marked as unreviewed.

## Location and routes

The caller's position and the incident's position have different meanings. Places resolve against the loaded city/site catalog. Missing, ambiguous and unsupported places remain review states rather than becoming precise pins.

The city uses a cached road graph; campus work uses cached outdoor paths and building geometry. The route search excludes supported reported blockages. It doesn't invent an indoor route or use live traffic. A closure remains active until supported clearance or an explicit operator decision reopens it.

## Resource coordination

The planning engine checks required capabilities, availability and route support. A persistent queue reserves future work and rechecks the route when a resource becomes available. Held or paused stops remain visible. If reassignment fails, the original allocation is retained.

SQLite transactions keep related changes together. Version checks detect stale edits, and idempotency protects against a repeated request producing duplicate work. City and USC records stay scoped to their own workspace.

## Communication and evidence

An operator approves the exact outgoing text. Attempted delivery, device receipt, human acknowledgment and reply remain separate states. Evidence records preserve source excerpts, corrections and earlier instructions so a later reviewer can understand a decision.

The transport simulator exercises compact packets, retries and receipt behavior. It demonstrates software state transitions, not RF range, bandwidth in the field or a deployed radio system.

## Read the code

| Area | Starting points |
| --- | --- |
| Backend application and access boundaries | `server/main.py`, `server/browser_access.py` |
| Reports, sources and domain state | `server/domain.py`, `server/store.py` |
| Hosted speech and extraction | `server/models.py`, `server/intake.py` |
| Location and interpretation checks | `server/geography.py`, `server/site.py`, `server/threats.py` |
| Response planning and provider queues | `server/operations.py`, `server/dispatch_queue.py` |
| Case history and recovery | `server/cases.py` |
| Operator, intake and maps | `web/src/Operator.tsx`, `web/src/LiveIntake.tsx`, `web/src/WorldMap.tsx` |
| Resource and field interfaces | `web/src/ProviderQueues.tsx`, `web/src/Resources.tsx`, `web/src/Field.tsx` |
| Behavioral checks | `tests/`, `web/tests/` |

Model credentials are configured privately on the server. This guide intentionally omits credential values, private launch links and internal request examples. No runtime database or operator recording is included in the source repository.
