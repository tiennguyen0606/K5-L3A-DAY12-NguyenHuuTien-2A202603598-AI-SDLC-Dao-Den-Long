# Phase 1 proof

| Requirement | Verification | Result |
|---|---|---|
| Fixed movement, pickup, deposit, pulse | `python3 -m unittest tests/test_phase1.py -v` | Pass |
| Contract JSONL and error code 2 | `python3 -m unittest tests/test_cli.py -v` | Pass |
| Determinism | `test_same_seed_and_actions_are_deterministic` | Pass |
| Playable core loop | `python3 -m http.server 8000 -d web`, open `http://localhost:8000` | Manual pass |

Evidence is reproducible from source and is not hand-edited program output.

