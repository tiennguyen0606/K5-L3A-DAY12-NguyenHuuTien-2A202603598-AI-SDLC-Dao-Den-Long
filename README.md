# Đảo Đèn Lồng

Game WebGL 3D góc nhìn thứ ba về Mây — người giữ đèn trẻ tuổi — gom đom đóm, duy trì nhiên liệu đèn tới bình minh và chống lại Bóng Mực. Repo hiện thực Phase 1–3 của Day 12 AI SDLC Lab, gồm renderer Three.js chạy offline và mô phỏng headless tất định theo Test Contract v1.2.

## Chạy trong tối đa 3 lệnh

Yêu cầu Python 3.11+ (không có dependency ngoài):

```bash
python3 -m unittest discover -s tests -v
node --test tests/test_web_controls.mjs
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

Mỗi đèn cần 10 đom đóm lần đầu và 5 khi thắp lại. Đèn sáng hao một nhiên liệu mỗi giây; hãy châm dầu và giữ ít nhất 60% số đèn sáng tới bình minh. Sức chứa tăng hai sau mỗi lần thắp thành công, tối đa 20. Điểm chi tiết được khai báo trong `game.contract.json`.

## Sáng tạo của tôi

Phần nhìn dùng các khối hình học tự tạo, phối sương xanh tím và quầng đèn vàng cam tăng dần. Không dùng asset ngoài. Renderer tách hoàn toàn khỏi core headless, nên phần trình bày không thay đổi output contract.

## Tài liệu và bằng chứng

- [Giả định/evaluation Phase 1](docs/notes/phase-1.md)
- [Bằng chứng Phase 1](docs/proof/phase-1.md)
- [Spec và evaluation Phase 2](docs/notes/phase-2.md)
- [Bằng chứng Phase 2](docs/proof/phase-2.md)
- [ADR nhiên liệu và luật bình minh](docs/adr/0001-lantern-fuel-and-dawn.md)
- [Spec/evaluation Phase 3](docs/notes/phase-3.md)
- [Bằng chứng Phase 3](docs/proof/phase-3.md)
- `AGENTS.md`: harness hướng dẫn agent và hàng rào TDD
- `game.contract.json`: contract và tuning đang dùng

Phase 3 bổ sung nhiên liệu, châm dầu/thắp lại, Bóng Mực hút dầu, sức chứa động, chế độ màu dễ phân biệt và luật thắng tại bình minh.
