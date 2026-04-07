# Object Detection & Tracking with YOLOv8 + DeepSORT

A real-time object detection and tracking project using YOLOv8 and DeepSORT. Detects multiple classes and tracks them across frames with unique IDs.

## How to Run
1. Install dependencies: `pip install -r requirements.txt`
2. Download YOLOv8 model (e.g. `yolov8n.pt`) from Ultralytics
3. Run: `python yolov8_deepsort_tracker.py`

## Tech Used
- YOLOv8 (Ultralytics)
- DeepSORT
- OpenCV

## Bonus: Full-Time Finance Tracker CLI
You can also run a lightweight finance tracker app from this repository.

### Features
- Add income and expense entries
- Track monthly budgets by category
- Review monthly summaries with budget over/under status

### Usage
```bash
python finance_tracker.py add income salary 4500 --date 2026-02-01 --note "Monthly salary"
python finance_tracker.py add expense groceries 210.5 --date 2026-02-02
python finance_tracker.py budget groceries 2026-02 300
python finance_tracker.py summary 2026-02
```

This creates a local SQLite database file named `finance_tracker.db` in the project root.
