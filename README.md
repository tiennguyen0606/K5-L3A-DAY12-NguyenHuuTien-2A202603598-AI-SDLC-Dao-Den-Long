# Đảo Đèn Lồng

Game phiêu lưu góc nhìn thứ ba về Mây — người giữ đèn trẻ tuổi — gom đom đóm, thắp sáng các đảo và chống lại Bóng Mực. Repo hiện thực Phase 1–2 của Day 12 AI SDLC Lab, gồm chế độ chơi trình duyệt và mô phỏng headless tất định theo Test Contract.

## Chạy trong tối đa 3 lệnh

Yêu cầu Python 3.11+ (không có dependency ngoài):

```bash
python3 -m unittest discover -s tests -v
python3 -m http.server 8000 -d web
```

Mở <http://localhost:8000>. Trên Windows có thể thay `python3` bằng `python`.

Headless:

```bash
python3 -m lantern_islands --seed 42 --night 2 --ticks 600 --out run.jsonl
```

Có thể thêm `--scenario file.json --inputs file.json --snapshot-every 10`. Scenario/inputs sai trả mã 2; output là JSONL và luôn kết thúc bằng dòng `end`.

## Điều khiển

- `WASD`: di chuyển
- `E`: nạp đom đóm vào đèn gần nhất
- `Q`: Tỏa Sáng
- `Shift`: Lướt
- `P` hoặc `Esc`: tạm dừng
- `R`: chơi lại

## Luật và điểm

Mây mang tối đa 10 đom đóm; mỗi đèn cần 10. Điểm: +10 cho mỗi đom đóm nạp, +100 cho mỗi đèn thắp, +5 cho mỗi Bóng Mực trúng pulse; khi thắng cộng `floor(giây còn lại) × 2 + 50 × Ngọn Lửa còn lại`.

## Sáng tạo của tôi

Phần nhìn dùng các khối hình học tự tạo, phối sương xanh tím và quầng đèn vàng cam tăng dần. Không dùng asset ngoài. Renderer tách hoàn toàn khỏi core headless, nên phần trình bày không thay đổi output contract.

## Tài liệu và bằng chứng

- [Giả định/evaluation Phase 1](docs/notes/phase-1.md)
- [Bằng chứng Phase 1](docs/proof/phase-1.md)
- [Spec và evaluation Phase 2](docs/notes/phase-2.md)
- [Bằng chứng Phase 2](docs/proof/phase-2.md)
- `AGENTS.md`: harness hướng dẫn agent và hàng rào TDD
- `game.contract.json`: contract và tuning đang dùng

Phase 2 bổ sung ba đêm, dash, pause, Gió Lạc, Bùa Gió và contract v1.1; xem tài liệu Phase 2 trong `docs/` tại tag `phase-2`.
