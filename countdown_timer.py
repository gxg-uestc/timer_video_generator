#!/usr/bin/env python3
"""倒计时视频生成器 - 使用 Canvas 绘制界面，避免 macOS 主题问题"""

import os
import shutil
import subprocess
import sys
import threading
import tkinter as tk

from PIL import Image, ImageDraw, ImageFont
from imageio_ffmpeg import get_ffmpeg_exe

COLORS = [
    ("白色", (255, 255, 255), "#FFFFFF"),
    ("红色", (255, 0, 0), "#FF0000"),
    ("绿色", (0, 255, 0), "#00FF00"),
    ("蓝色", (0, 0, 255), "#0000FF"),
    ("黄色", (255, 255, 0), "#FFFF00"),
    ("青色", (0, 255, 255), "#00FFFF"),
    ("橙色", (255, 136, 0), "#FF8800"),
    ("粉色", (255, 105, 180), "#FF69B4"),
]
color_names = [name for name, _, _ in COLORS]

MACOS_FONTS = [
    "/System/Library/Fonts/Menlo.ttc",
    "/System/Library/Fonts/Monaco.ttf",
    "/System/Library/Fonts/SFNSMono.ttf",
    "/System/Library/Fonts/Courier.ttc",
]
LINUX_FONTS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
]

FPS = 30
WIDTH, HEIGHT = 1920, 1080
FONT_SIZE = 120


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


def detect_font(font_name=None):
    if font_name and os.path.isfile(font_name):
        return font_name
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


def generate_video(ffmpeg_path, font_path, duration, color_tuple, output, progress_callback):
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
        if progress_callback and frame_num % FPS == 0:
            proc.stdin.flush()
            progress_callback(frame_num + 1, total_frames)

    proc.stdin.close()
    proc.wait()
    if progress_callback:
        progress_callback(total_frames, total_frames)
    return proc.returncode


class CountdownApp:
    def __init__(self, root):
        self.root = root
        self.root.title("倒计时视频生成器")
        self.root.resizable(False, False)

        # 界面尺寸
        self.win_w, self.win_h = 450, 400
        self.root.geometry("{}x{}".format(self.win_w, self.win_h))

        self.selected_color_idx = 0
        self.is_generating = False
        self.duration_str = "60"

        # 用 Canvas 绘制所有 UI
        self._build_canvas_ui()

        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after(300, lambda: self.root.attributes('-topmost', False))
        self.root.focus_force()

    def _build_canvas_ui(self):
        self.canvas = tk.Canvas(self.root, width=self.win_w, height=self.win_h,
                                bg='#f0f0f0', highlightthickness=0)
        self.canvas.pack()

        # 绘制所有元素
        self._draw_ui()

        # 绑定事件
        self.canvas.bind("<Button-1>", self._on_click)
        self.root.bind("<Return>", lambda e: self.on_generate())
        self.root.bind("<KeyRelease>", self._on_key)

    def _draw_ui(self):
        self.canvas.delete("all")
        c = self.canvas
        w, h = self.win_w, self.win_h

        # Title
        c.create_text(w/2, 40, text="倒计时视频生成器",
                     font=("", 20, "bold"), fill="black")

        # Duration input background
        c.create_rectangle(w/2-100, 80, w/2+100, 115,
                          fill="white", outline="#888888", width=2)
        c.create_text(w/2, 98, text="时长（秒）:", font=("", 14), fill="#333")
        c.create_text(w/2, 105, text=self.duration_str,
                     font=("", 16, "bold"), fill="black", justify="center")

        # Color dropdown background
        c.create_rectangle(w/2-80, 130, w/2+80, 165,
                          fill="white", outline="#888888", width=2)
        color_name = color_names[self.selected_color_idx]
        c.create_text(w/2, 148, text="颜色：" + color_name,
                     font=("", 14), fill="black")

        # Color preview
        c.create_rectangle(w/2+30, 135, w/2+50, 160,
                          fill=COLORS[self.selected_color_idx][2],
                          outline="#333", width=1)

        # Progress bar background
        c.create_rectangle(50, 185, w-50, 205, fill="#cccccc", outline="")
        # Progress fill (will be updated)
        self.progress_rect = c.create_rectangle(50, 185, 50, 205,
                                                 fill="#2196F3", outline="")

        # Status
        c.create_text(w/2, 230, text="", font=("", 11),
                     fill="#666", tags="status")

        # Generate button
        btn_state = "gray" if self.is_generating else "#2196F3"
        btn_text = "生成中..." if self.is_generating else "生成视频"
        self.btn_rect = c.create_rectangle(w/2-80, 260, w/2+80, 295,
                                           fill=btn_state, outline="#1976D2", width=2)
        self.btn_text = c.create_text(w/2, 278, text=btn_text,
                                      font=("", 14, "bold"), fill="white")

    def _on_click(self, event):
        x, y = event.x, event.y
        # Check color dropdown click
        if 225-80 <= x <= 225+80 and 130 <= y <= 165:
            self._cycle_color()
        # Check generate button click
        if not self.is_generating and 225-80 <= x <= 225+80 and 260 <= y <= 295:
            self.on_generate()

    def _cycle_color(self):
        self.selected_color_idx = (self.selected_color_idx + 1) % len(COLORS)
        self._draw_ui()

    def _on_key(self, event):
        # Update duration from keypress
        if event.char.isdigit():
            self.duration_str += event.char
            if len(self.duration_str) > 5:
                self.duration_str = self.duration_str[-5:]
            self._draw_ui()
        elif event.keysym == "BackSpace":
            self.duration_str = self.duration_str[:-1] or "0"
            self._draw_ui()
        elif event.keysym == "Clear" or event.keysym == "Escape":
            self.duration_str = "60"
            self._draw_ui()

    def _set_progress(self, pct):
        w = self.win_w
        fill_x = 50 + int((w - 100) * pct / 100)
        self.canvas.coords(self.progress_rect, 50, 185, fill_x, 205)
        self.canvas.itemconfig("status", text="正在生成... {}%".format(pct))

    def on_generate(self):
        if self.is_generating:
            return

        try:
            duration = int(self.duration_str)
            if duration < 1:
                self.root.after(0, lambda: tk.messagebox.showerror("错误", "时长必须至少为 1 秒"))
                return
        except ValueError:
            self.root.after(0, lambda: tk.messagebox.showerror("错误", "请输入有效整数（秒）"))
            return

        ffmpeg_path = find_ffmpeg()
        if not ffmpeg_path:
            self.root.after(0, lambda: tk.messagebox.showerror("错误", "未找到 ffmpeg"))
            return

        font_path = detect_font(None)
        if not font_path:
            self.root.after(0, lambda: tk.messagebox.showerror("错误", "未找到等宽字体"))
            return

        color_tuple = COLORS[self.selected_color_idx][1]
        output = "countdown_{}s.mp4".format(duration)

        self.is_generating = True
        self._draw_ui()
        self._set_progress(0)

        def progress_cb(current, total):
            pct = int(current / total * 100)
            self.root.after(0, lambda p=pct: self._set_progress(p))

        def do_generate():
            rc = generate_video(ffmpeg_path, font_path, duration,
                               color_tuple, output, progress_cb)
            self.root.after(0, lambda: self.on_generation_done(rc, output))

        threading.Thread(target=do_generate, daemon=True).start()

    def on_generation_done(self, returncode, output):
        self.is_generating = False
        if returncode != 0:
            tk.messagebox.showerror("错误", "FFmpeg 编码失败。")
            self._draw_ui()
            return

        self._draw_ui()
        self.canvas.itemconfig("status", text="生成完成！")
        tk.messagebox.showinfo("完成", "视频已保存至：{}".format(os.path.abspath(output)))


def main():
    root = tk.Tk()
    app = CountdownApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
