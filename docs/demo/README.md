# Demo

Ticket-04 ưu tiên video `.mp4` dưới 5 phút. Máy nộp bài chưa có app quay video nên dùng **bộ ảnh chụp** làm bằng chứng chơi được. Có thể bổ sung `demo.mp4` sau bằng Xbox Game Bar có sẵn Windows: `Win + G` hoặc `Win + Alt + R` (không cần cài thêm).

## Ảnh demo hiện có

### 1. Menu chính
![Menu Đảo Đèn Lồng](menu.png)

### 2. Đang chơi Đêm 1
![Gameplay Đêm 1](play.png)

## Checklist bằng chứng kèm ảnh

```bash
python -m unittest discover -s tests -v
python -m lantern_islands --seed 1 --night 2 --ticks 600 --out run.jsonl
python -m lantern_islands.benchmark --seed 42 --duration 30 --out bench.json
python -m lantern_islands.soak --seed 7 --nights 10 --out soak.json
```

- `bench.json`, `soak.json` đã commit ở gốc repo.
- Release: https://github.com/tiennguyen0606/K5-L3A-DAY12-NguyenHuuTien-2A202603598-AI-SDLC-Dao-Den-Long/releases/tag/v1.0.0
