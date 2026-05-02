#!/usr/bin/env python3
"""倒计时视频生成器 - 命令行版本"""

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

MACOS_FONTS = [
    "/System/Library/Fonts/Menlo.ttc",
    "/System/Library/Fonts/Monaco.ttf",
    "/System/Library/Fonts/SFNSMono.ttf",
    "/System/Library/Fonts/Courier.ttc",
]

LINUX_FONTS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
]

FPS = 30
WIDTH, HEIGHT = 1920, 1080
# 字体大小：调整到适合屏幕宽度（MM:SS 5 个字符）
FONT_SIZE = 500


def find_ffmpeg():
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg
    try:
        bundled = get_ffmpeg_exe()
        if os.path.isfile(bundled):
            return bundled
    except Exception:
        pass
    return None


def detect_font():
    font_list = MACOS_FONTS if sys.platform == "darwin" else LINUX_FONTS
    for path in font_list:
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

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
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

        # 显示进度
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

    # 检查依赖
    ffmpeg_path = find_ffmpeg()
    if not ffmpeg_path:
        print("错误：未找到 ffmpeg。请先安装：")
        print("  macOS: pip3 install imageio-ffmpeg")
        sys.exit(1)

    font_path = detect_font()
    if not font_path:
        print("错误：未找到等宽字体")
        sys.exit(1)

    # 输入时长
    while True:
        try:
            duration = int(input("\n请输入倒计时时长（秒）: "))
            if duration >= 1:
                break
            print("时长必须至少为 1 秒")
        except ValueError:
            print("请输入有效整数")

    # 选择颜色
    color_idx = select_color()
    color_name, color_tuple = COLORS[color_idx]

    # 输出文件名
    output = "countdown_{}s.mp4".format(duration)

    print("\n生成参数:")
    print("  时长：{}秒".format(duration))
    print("  颜色：{}".format(color_name))
    print("  分辨率：1920x1080")
    print("  输出：{}".format(output))

    # 生成视频
    print("\n开始生成视频...")
    rc = generate_video(ffmpeg_path, font_path, duration, color_tuple, output)

    if rc == 0:
        print("\n生成完成！视频已保存至：{}".format(os.path.abspath(output)))
    else:
        print("\n生成失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
