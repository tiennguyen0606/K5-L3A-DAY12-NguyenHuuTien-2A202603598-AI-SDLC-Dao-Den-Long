# Phase 3 proof

Run:

```bash
python3 -m unittest tests/test_phase3.py -v
python3 -m unittest discover -s tests -v
```

The seven focused tests cover fuel exhaustion, refuelling, relighting/capacity, dawn victory, Shade drain events, safe-zone recoil, and v1.2 snapshots. The 22-test full suite verifies retained Phase 1–2 behavior except rules explicitly replaced by Ticket-03.
