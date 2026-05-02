#!/usr/bin/env python3
"""倒计时视频生成器 - Windows 版本"""

import os
import shutil
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont
from imageio_ffmpeg import get_ffmpeg_exe

COLORS = [
    ("白色", (255, 255, 255)),
    ("红色", (255, 0, 0)),
    ("绿色", (0, 255, 0)),
    ("蓝色", (0, 0, 255)),
    ("黄色", (255, 255, 0)),
    ("青色", (0, 255, 255)),
    ("橙色", (255, 136, 0)),
    ("粉色", (255, 105, 180)),
]

WINDOWS_FONTS = [
    "C:/Windows/Fonts/consola.ttf",
    "C:/Windows/Fonts/cour.ttf",
    "C:/Windows/Fonts/lucon.ttf",
]

MACOS_FONTS = [
    "/System/Library/Fonts/Menlo.ttc",
    "/System/Library/Fonts/Monaco.ttf",
]

LINUX_FONTS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
]

FPS = 30
WIDTH, HEIGHT = 1920, 1080
FONT_SIZE = 500


def find_ffmpeg():
    # 先检查系统 ffmpeg
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg
    # 检查 bundled ffmpeg
    try:
        bundled = get_ffmpeg_exe()
        if os.path.isfile(bundled):
            return bundled
    except Exception:
        pass
    # Windows 下检查常见路径
    win_paths = [
        "ffmpeg.exe",
        "./ffmpeg.exe",
        os.path.join(os.path.dirname(sys.executable), "ffmpeg.exe"),
    ]
    for path in win_paths:
        if os.path.isfile(path):
            return path
    return None


def detect_font():
    if sys.platform == "win32":
        for path in WINDOWS_FONTS:
            if os.path.exists(path):
                return path
    elif sys.platform == "darwin":
        for path in MACOS_FONTS:
            if os.path.exists(path):
                return path
    else:
        for path in LINUX_FONTS:
            if os.path.exists(path):
                return path
    return None


def format_time(seconds):
    seconds = max(0, int(seconds))
    if seconds >= 3600:
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return "{:02d}:{:02d}:{:02d}".format(h, m, s)
    m = seconds // 60
    s = seconds % 60
    return "{:02d}:{:02d}".format(m, s)


def select_color():
    print("\n请选择颜色（输入数字 1-8）:")
    for i, (name, _) in enumerate(COLORS, 1):
        print("  {}. {}".format(i, name))
    while True:
        try:
            choice = input("\n选择 [1-8]: ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(COLORS):
                return idx
            print("请输入 1-8 之间的数字")
        except ValueError:
            print("请输入有效数字")


def generate_video(ffmpeg_path, font_path, duration, color_tuple, output):
    font = ImageFont.truetype(font_path, FONT_SIZE)
    total_frames = duration * FPS

    cmd = [
        ffmpeg_path, "-y",
        "-f", "rawvideo", "-vcodec", "rawvideo",
        "-s", "{}x{}".format(WIDTH, HEIGHT),
        "-pix_fmt", "rgb24", "-r", str(FPS),
        "-i", "-",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-preset", "medium", "-t", str(duration),
        output,
    ]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
    for frame_num in range(total_frames):
        remaining = duration - frame_num / FPS
        text = format_time(remaining)
        img = Image.new("RGB", (WIDTH, HEIGHT), "black")
        draw = ImageDraw.Draw(img)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x = (WIDTH - text_w) // 2
        y = (HEIGHT - text_h) // 2
        draw.text((x, y), text, fill=color_tuple, font=font)
        proc.stdin.write(img.tobytes())

        if frame_num % 30 == 0:
            pct = int(frame_num / total_frames * 100)
            print("\r正在生成... {}%".format(pct), end="", flush=True)

    proc.stdin.close()
    proc.wait()
    print("\r正在生成... 100%")
    return proc.returncode


def main():
    print("=" * 40)
    print("     倒计时视频生成器")
    print("=" * 40)

    ffmpeg_path = find_ffmpeg()
    if not ffmpeg_path:
        print("错误：未找到 ffmpeg。请将 ffmpeg.exe 放在程序同目录。")
        input("按 Enter 退出...")
        sys.exit(1)

    font_path = detect_font()
    if not font_path:
        print("错误：未找到可用字体")
        input("按 Enter 退出...")
        sys.exit(1)

    while True:
        try:
            duration = int(input("\n请输入倒计时时长（秒）: "))
            if duration >= 1:
                break
            print("时长必须至少为 1 秒")
        except ValueError:
            print("请输入有效整数")

    color_idx = select_color()
    color_name, color_tuple = COLORS[color_idx]

    output = "countdown_{}s.mp4".format(duration)

    print("\n生成参数:")
    print("  时长：{}秒".format(duration))
    print("  颜色：{}".format(color_name))
    print("  分辨率：1920x1080")
    print("  输出：{}".format(output))

    print("\n开始生成视频...")
    rc = generate_video(ffmpeg_path, font_path, duration, color_tuple, output)

    if rc == 0:
        print("\n生成完成！视频已保存至：{}".format(os.path.abspath(output)))
    else:
        print("\n生成失败")
        input("按 Enter 退出...")
        sys.exit(1)
    
    input("\n按 Enter 退出...")


if __name__ == "__main__":
    main()
