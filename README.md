# Timer Video Generator

倒计时视频生成器 - 生成 1080p MP4 倒计时视频，黑色背景，中央显示倒计时数字。

## 功能

- 自定义时长（秒）
- 8 种颜色可选
- 1920x1080 分辨率
- 跨平台（macOS / Windows / Linux）

## 依赖

- Python 3.6+
- FFmpeg
- 依赖库：`pip install -r requirements.txt`

## 使用

### macOS / Linux

```bash
python3 countdown_timer_cli.py
```

### Windows

使用 `countdown_timer_win.py`，或编译为 .exe：

```bash
pip install pyinstaller
pyinstaller --onefile --console countdown_timer_win.py
```
