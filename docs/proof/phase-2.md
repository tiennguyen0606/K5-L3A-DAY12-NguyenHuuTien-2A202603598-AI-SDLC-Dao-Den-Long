# Phase 2 proof

| Requirement | Automated evidence | Result |
|---|---|---|
| Three nights and standardized maps/timers | `test_each_night_uses_standard_lantern_count_and_duration` | Pass |
| Dash | `test_dash_moves_fourteen_metres_per_second_for_twelve_ticks` | Pass |
| Pause | `test_pause_advances_tick_but_freezes_gameplay_clock` | Pass |
| Charm | `test_charm_increases_running_speed_and_removes_dash_cooldown` | Pass |
| Drifter steal/drop | `test_drifter_steals_three_then_pulse_makes_it_drop_them` | Pass |
| Contract v1.1 snapshot | `test_snapshot_contains_all_v11_fields` | Pass |
| Scheduled spawns, falling and pulse push | Three focused Phase 2 regression tests | Pass |
| Phase 1 regression | `python3 -m unittest discover -s tests -v` | 15/15 pass |

Performance command:

```bash
time python3 -m lantern_islands --seed 42 --night 3 --ticks 21600 --out night3.jsonl
```

The output is generated directly and must not be edited.
