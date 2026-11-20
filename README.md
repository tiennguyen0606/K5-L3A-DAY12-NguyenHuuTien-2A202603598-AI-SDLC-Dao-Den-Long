# Đảo Đèn Lồng

Game WebGL 3D góc nhìn thứ ba về Mây — người giữ đèn trẻ tuổi — gom đom đóm, duy trì nhiên liệu đèn tới bình minh và chống lại Bóng Mực. Repo hiện thực Phase 1–4 (Contract v1.3) của Day 12 AI SDLC Lab: renderer Three.js offline + mô phỏng headless tất định.

![Menu Đảo Đèn Lồng](docs/demo/ui-menu.png)

## Chạy trong tối đa 3 lệnh

Yêu cầu Python 3.11+ (không dependency ngoài) và trình duyệt có WebGL:

```bash
python3 -m unittest discover -s tests -v
node --test tests/test_web_controls.mjs
python3 -m lantern_islands.webapp
```

Mở <http://127.0.0.1:8000>. Trên Windows có thể thay `python3` bằng `python`.

## Điều khiển

- `WASD`: di chuyển · `Space`: nhảy · `Shift`: Lướt · `E`: nạp/châm dầu · `Q`: Tỏa Sáng
- `P` / `Esc`: tạm dừng · `R`: chơi lại Đêm
- Chuột: xoay camera (độ nhạy chỉnh trong Cài đặt)

## Luật và điểm (v1.2+)

Đèn hao dầu khi sáng; thắp lần đầu 10 đom đóm, thắp lại 5, châm dầu khi đang sáng. Thắng khi còn sống lúc bình minh và ≥ 60% đèn đang sáng. Điểm khai báo trong `game.contract.json`.

## Headless / bench / soak

```bash
python3 -m lantern_islands --seed 42 --night 2 --ticks 600 --out run.jsonl
python3 -m lantern_islands.benchmark --seed 42 --duration 30 --out bench.json
python3 -m lantern_islands.soak --seed 7 --nights 10 --out soak.json
python3 -m lantern_islands.webapp --export-leaderboard leaderboard-export.json
```

- Scenario/inputs sai → mã thoát 2.
- Benchmark cần Chrome/Chromium (`CHROME_BIN` nếu không tìm thấy). `peak_mem_mb` là `null` vì đo trong trang web headless; giải thích trong README này.
- Vsync tắt qua flag Chrome `--disable-gpu-vsync` và renderer không chờ vsync trong trang bench.

## Sáng tạo của tôi

Hình học tự tạo, sương xanh tím, quầng đèn vàng cam tăng theo tiến độ. Âm thanh procedural (Web Audio), không asset ngoài. Renderer tách khỏi core headless.

## Tài liệu và bằng chứng

- [Giả định/evaluation Phase 1–3](docs/notes/) · [Proof](docs/proof/)
- [ADR nhiên liệu & bình minh](docs/adr/0001-lantern-fuel-and-dawn.md)
- [Retro 4 phase](docs/retro.md) · [Demo notes](docs/demo/README.md)
- `AGENTS.md`, `CHANGELOG.md`, `CREDITS.md`, `LICENSE`, `game.contract.json`
- Evidence đã chạy: `bench.json`, `soak.json`

## Hệ thống

- OS: macOS / Linux / Windows
- Python 3.11+, Node 18+ (chỉ để chạy `node --test`)
- Trình duyệt Chromium/Firefox mới có WebGL; Chrome cho benchmark
