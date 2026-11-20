# Phase 3 proof

Tag: `phase-3` → commit `d008fe8`

```bash
git checkout phase-3
python -m unittest tests/test_phase3.py -v
python -m unittest discover -s tests -v
```

Focused tests cover fuel exhaustion, refuel, relight/capacity, dawn victory, Shade drain, safe-zone recoil, and v1.2 snapshots. Full suite log: `docs/proof/logs/unittest.txt`.

Design record: `docs/adr/0001-lantern-fuel-and-dawn.md`. Breaking changes: `CHANGELOG.md` Phase 3.
