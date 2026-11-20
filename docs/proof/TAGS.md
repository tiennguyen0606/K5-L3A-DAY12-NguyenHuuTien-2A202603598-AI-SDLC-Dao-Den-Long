# Tag map (pushed to GitHub)

| Tag | Commit | Message |
|---|---|---|
| `phase-1` | `a9afa2c` | feat: deliver deterministic Phase 1 lantern island |
| `phase-2` | `776408e` | feat: implement Phase 2 three-island contract |
| `phase-3` | `d008fe8` | feat: add Phase 3 lantern fuel and dawn survival |
| `phase-4` | `0b25828` | docs: add demo menu screenshot outside ui-*.png ignore rule |
| `v1.0.0` | follows `main` at release time | Release “Bình minh” (may be newer than `phase-4`) |

## Note for graders (do not retag)

- Tag `phase-4` is frozen at `0b25828` (submission checkpoint).
- Later packaging/CI/demo/proof-log improvements live on `main` after that commit (e.g. `dfd94d0`: Actions workflow, `scripts/verify.py`, `docs/demo/demo.mp4`, regenerated `docs/proof/logs/`).
- Rubric forbids rewriting tagged history after the deadline; therefore `phase-4` was **not** moved. Evaluate Phase 4 core at the tag; evaluate release polish on `main` / Release `v1.0.0`.

Verify remotely:

```bash
git ls-remote --tags origin
```

Re-run checks at a tag:

```bash
git checkout phase-3
python -m unittest discover -s tests -v
```
