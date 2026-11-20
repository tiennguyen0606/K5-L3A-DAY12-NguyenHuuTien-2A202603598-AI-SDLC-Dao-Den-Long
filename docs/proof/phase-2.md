# Phase 2 proof

Tag: `phase-2` → commit `776408e`

| Requirement | Automated evidence | Result |
|---|---|---|
| Three nights / standard maps | `test_each_night_uses_standard_lantern_count_and_duration` | Pass |
| Dash | `test_dash_moves_fourteen_metres_per_second_for_twelve_ticks` | Pass |
| Pause | `test_pause_advances_tick_but_freezes_gameplay_clock` | Pass |
| Charm | `test_charm_increases_running_speed_and_removes_dash_cooldown` | Pass |
| Drifter steal/drop | `test_drifter_steals_three_then_pulse_makes_it_drop_them` | Pass |
| Contract v1.1 snapshot | `test_snapshot_contains_all_v11_fields` | Pass |
| Phase 1 regression | full suite in `docs/proof/logs/unittest.txt` | Pass |

```bash
git checkout phase-2
python -m unittest discover -s tests -v
python -m lantern_islands --seed 42 --night 3 --ticks 1200 --out night3.jsonl
```
