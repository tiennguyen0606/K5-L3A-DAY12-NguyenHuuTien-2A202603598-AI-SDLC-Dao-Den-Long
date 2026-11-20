# Tag map (pushed to GitHub)

| Tag | Commit | Message |
|---|---|---|
| `phase-1` | `a9afa2c` | feat: deliver deterministic Phase 1 lantern island |
| `phase-2` | `776408e` | feat: implement Phase 2 three-island contract |
| `phase-3` | `d008fe8` | feat: add Phase 3 lantern fuel and dawn survival |
| `phase-4` | `0b25828` | docs: add demo menu screenshot outside ui-*.png ignore rule |
| `v1.0.0` | `05d787b` | fix: title font overlap and add screenshot demo evidence |

Verify remotely:

```bash
git ls-remote --tags origin
```

Re-run checks at a tag:

```bash
git checkout phase-3
python -m unittest discover -s tests -v
```
