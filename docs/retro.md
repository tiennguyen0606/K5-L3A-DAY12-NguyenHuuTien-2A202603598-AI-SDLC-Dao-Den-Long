# Retro — Đảo Đèn Lồng (4 phase)

## Evaluation tổng hợp

- Phase 1–3: core headless và contract ổn định nhờ TDD + `AGENTS.md` (sim là nguồn sự thật).
- Phase 4: bench/soak/leaderboard/a11y đẩy bài từ “chạy được” sang “phát hành được”.

## AI hiệu quả / không hiệu quả

- Hiệu quả: viết test đỏ trước, rồi implement tối thiểu theo ticket; giữ Python stdlib.
- Không hiệu quả: để AI tự mở rộng renderer song song với contract — dễ lệch luật. Giảm bằng cách cấm renderer ảnh hưởng headless output.

## Lần AI sai và cách phát hiện

- Mouse look bị khóa khi giữ WASD → phát hiện bằng chơi tay + test `nextMouseYaw`.
- Bench `avg_fps` dưới 60 → phát hiện bằng `bench.json` tự chạy, không tin lời agent.

## Harness giúp nhiều nhất

- `AGENTS.md` (tick order, fuel sixtieths, không restore `all_lit`).
- Suite `tests/test_phase1.py`…`test_phase4.py` làm hàng rào regression.
- `scripts/verify.py` + GitHub Actions CI: agent/CI không được kết thúc khi test đỏ.
- `docs/proof/TAGS.md` + logs trong `docs/proof/logs/` gắn bằng chứng với tag thật trên remote.

## Token / chi phí ước tính

- ~18k (P1) + ~22k (P2) + ~14k (P3) + ~20k (P4 polish/release) ≈ **74k tokens**.
- Tiết kiệm: không engine ngoài, không asset pack, tái sử dụng simulation, sửa có mục tiêu thay vì regenerate toàn bộ.

## Nếu làm lại

- Gắn renderer mỏng với cùng snapshot API sớm hơn.
- Chạy bench từ ngày đầu Phase 4 trước khi thêm hiệu ứng.
- Tách commit polish UI khỏi contract ngay từ Phase 2.
