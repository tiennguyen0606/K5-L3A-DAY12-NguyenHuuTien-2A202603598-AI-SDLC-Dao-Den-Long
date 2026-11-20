# Phase 1 proof

Tag: `phase-1` → commit `a9afa2c`

| Requirement | Verification | Result |
|---|---|---|
| Fixed movement, pickup, deposit, pulse | `python -m unittest tests/test_phase1.py -v` | Pass — log `docs/proof/logs/unittest.txt` |
| Contract JSONL and error code 2 | `python -m unittest tests/test_cli.py -v` | Pass |
| Determinism | `test_same_seed_and_actions_are_deterministic` | Pass |
| Playable core loop | `python -m lantern_islands.webapp` + screenshot `docs/demo/menu.png` | Manual pass |

Reproduce on the tag:

```bash
git checkout phase-1
python -m unittest discover -s tests -v
```

Evidence files under `docs/proof/logs/` are regenerated from commands, not hand-edited.
