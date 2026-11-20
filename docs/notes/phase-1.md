# Phase 1 — PRD-0

## Assumptions and acceptance criteria

- Mây runs at 6 m/s and carries at most 10 motes; one lantern requires 10. These initially ambiguous values are declared in `game.contract.json`.
- Movement, pickup, deposit, pulse, shade damage, win/loss, scoring, and replay are renderer-independent.
- The browser view is a lightweight third-person perspective scene; the headless core is the source of truth for rules.
- The five lanterns use the positions later standardized for Đảo Bến, avoiding needless migration.
- Acceptance: identical seed/scenario/input yields byte-identical JSONL; invalid scenario/input exits 2; snapshots begin at tick 0; the playable view provides the core Phase 1 loop.

## AI log and evaluation

- Used Codex to convert PRD-0 into focused unit/integration tests, then implement the minimum deterministic core.
- Estimated usage: about 18k input/output tokens for requirement reading, implementation, and review.
- Token-saving choices: Python standard library only; shared pure simulation; no engine dependency or generated assets.
- AI risk found: a renderer could accidentally duplicate rules. Mitigation: `AGENTS.md` makes the simulation authoritative and tests do not import the renderer.

## Result

- Automated core and CLI criteria: achieved; see `docs/proof/phase-1.md`.
- Browser core loop: achieved. Visual jump/camera orbit and complete shade damage feedback remain deliberately simple.

