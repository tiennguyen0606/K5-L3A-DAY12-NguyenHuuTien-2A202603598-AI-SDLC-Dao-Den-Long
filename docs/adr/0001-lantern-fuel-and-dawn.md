# ADR 0001: Lantern fuel and dawn-based outcomes

## Status

Accepted for Phase 3.

## Context

Ticket-03 replaces permanent lit lanterns and immediate `all_lit` victory. Lit lanterns now decay, can be refuelled, can go out, and only contribute to victory at dawn.

## Decision

- Store fuel as integer `fuel_units`, where 60 units equal one displayed fuel point. Passive decay subtracts one unit per gameplay tick; each draining shade subtracts five more. This avoids cumulative floating-point drift.
- Keep `lit`, `ever_lit`, `relit_count`, `deposited`, and fuel separate. `ever_lit` selects the 5-mote relight cost; `deposited` remains partial progress for the current lighting attempt.
- Put fuel decay immediately after counter updates and before movement/interactions. A refuel later in the same tick therefore cannot retroactively prevent a lantern that already reached zero from emitting `lantern_out`.
- Remove early victory. At dawn, evaluate `no_flames` first, then compare lit lantern count to `ceil(0.6 × total)` and award dawn score only on success.
- Derive capacity from `successful_lights` rather than storing a second mutable value: `min(20, 10 + 2 × successful_lights)`.

## Consequences

Phase 1–2 scoring and duration assertions are intentionally updated with comments. Old behavior remains reproducible at their Git tags. Contract v1.2 snapshots gain fuel and capacity fields.

