"""AAFuzzyClicker - minimal auto button clicker.

Capture a button (drag a box on screen -> saved as PNG), then Start: every
few seconds the screen is scanned and every saved button found is clicked.
"""
import os
import time
import threading
import ctypes
from ctypes import wintypes
from datetime import datetime
import tkinter as tk
from tkinter import messagebox

import cv2
import numpy as np
from PIL import ImageGrab, Image, ImageTk

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BUTTONS_DIR = os.path.join(BASE_DIR, "buttons")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
LOGO_PNG = os.path.join(ASSETS_DIR, "logo.png")
LOGO_ICO = os.path.join(ASSETS_DIR, "logo.ico")
THRESHOLD = 0.85            # match sensitivity (0-1)

user32 = ctypes.windll.user32

# --- make coordinates physical pixels so multi-monitor DPI lines up ---
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)   # per-monitor aware
except Exception:
    try:
        user32.SetProcessDPIAware()
    except Exception:
        pass

# --- own taskbar identity so Windows shows our icon, not python's ---
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
        "GauthierDenjoy.AAFuzzyClicker")
except Exception:
    pass


def virtual_screen():
    """(left, top, width, height) of the whole desktop, in physical pixels."""
    return (user32.GetSystemMetrics(76), user32.GetSystemMetrics(77),
            user32.GetSystemMetrics(78), user32.GetSystemMetrics(79))


def click_at(x, y):
    user32.SetCursorPos(int(x), int(y))
    user32.mouse_event(0x0002, 0, 0, 0, 0)   # left down
    user32.mouse_event(0x0004, 0, 0, 0, 0)   # left up


def grab_gray():
    """Screenshot of all monitors as a grayscale array + its top-left offset."""
    left, top, w, h = virtual_screen()
    img = ImageGrab.grab(bbox=(left, top, left + w, top + h), all_screens=True)
    gray = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
    return gray, left, top


class CaptureOverlay:
    """Fullscreen overlay to drag a box; saves the region as a PNG."""

    def __init__(self, root):
        self.root = root
        left, top, w, h = virtual_screen()
        self.off = (left, top)
        self.win = tk.Toplevel(root)
        self.win.overrideredirect(True)
        self.win.geometry(f"{w}x{h}+{left}+{top}")
        self.win.attributes("-alpha", 0.3, "-topmost", True)
        self.win.configure(bg="black", cursor="cross")
        self.canvas = tk.Canvas(self.win, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.start = None
        self.rect = None
        self.canvas.bind("<Button-1>", self._down)
        self.canvas.bind("<B1-Motion>", self._move)
        self.canvas.bind("<ButtonRelease-1>", self._up)
        self.win.bind("<Escape>", lambda e: self.win.destroy())
        self.canvas.bind("<Button-3>", lambda e: self.win.destroy())

    def _down(self, e):
        self.start = (e.x, e.y)
        self.rect = self.canvas.create_rectangle(e.x, e.y, e.x, e.y,
                                                 outline="red", width=2)

    def _move(self, e):
        if self.rect:
            self.canvas.coords(self.rect, self.start[0], self.start[1], e.x, e.y)

    def _up(self, e):
        if not self.start:
            return
        x1, y1 = self.start
        x2, y2 = e.x, e.y
        self.win.destroy()
        left = min(x1, x2) + self.off[0]
        top = min(y1, y2) + self.off[1]
        right = max(x1, x2) + self.off[0]
        bottom = max(y1, y2) + self.off[1]
        if right - left < 4 or bottom - top < 4:
            return
        img = ImageGrab.grab(bbox=(left, top, right, bottom), all_screens=True)
        name = "button_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".png"
        img.save(os.path.join(BUTTONS_DIR, name))


class App:
    def __init__(self):
        os.makedirs(BUTTONS_DIR, exist_ok=True)
        self.running = False
        self.root = tk.Tk()
        self.root.title("AAFuzzyClicker")
        self.root.geometry("300x400")

        # window / taskbar icon
        try:
            self.root.iconbitmap(default=LOGO_ICO)
        except Exception:
            pass
        try:
            self._icon = ImageTk.PhotoImage(Image.open(LOGO_ICO))
            self.root.iconphoto(True, self._icon)
        except Exception:
            pass

        # logo banner
        try:
            img = Image.open(LOGO_PNG)
            img.thumbnail((240, 140))
            self.logo = ImageTk.PhotoImage(img)
            tk.Label(self.root, image=self.logo).pack(pady=(8, 2))
        except Exception:
            pass

        tk.Button(self.root, text="Capture button", command=self.capture
                  ).pack(fill="x", padx=8, pady=6)

        btns = tk.Frame(self.root)
        btns.pack(fill="x", padx=8)
        tk.Button(btns, text="Delete", command=self.delete).pack(side="left")
        self.toggle_btn = tk.Button(btns, text="Start", command=self.toggle)
        self.toggle_btn.pack(side="right")

        row = tk.Frame(self.root)
        row.pack(fill="x", padx=8, pady=(6, 0))
        tk.Label(row, text="Interval (s):").pack(side="left")
        self.interval = tk.Entry(row, width=6)
        self.interval.insert(0, "10")
        self.interval.pack(side="left")

        self.listbox = tk.Listbox(self.root)
        self.listbox.pack(fill="both", expand=True, padx=8, pady=6)

        self.status = tk.Label(self.root, text="Stopped", anchor="w")
        self.status.pack(fill="x", padx=8, pady=4)

        self.refresh()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # --- button list ---
    def refresh(self):
        self.listbox.delete(0, "end")
        for f in sorted(os.listdir(BUTTONS_DIR)):
            if f.lower().endswith(".png"):
                self.listbox.insert("end", f)

    def capture(self):
        self.root.withdraw()
        self.root.after(200, self._do_capture)

    def _do_capture(self):
        overlay = CaptureOverlay(self.root)
        self.root.wait_window(overlay.win)
        self.root.deiconify()
        self.refresh()

    def delete(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        name = self.listbox.get(sel[0])
        os.remove(os.path.join(BUTTONS_DIR, name))
        self.refresh()

    # --- clicking loop ---
    def toggle(self):
        if self.running:
            self.running = False
            self.toggle_btn.config(text="Start")
            self.status.config(text="Stopped")
        else:
            try:
                self.wait = max(1, int(float(self.interval.get())))
            except ValueError:
                messagebox.showerror("AAFuzzyClicker", "Invalid interval")
                return
            self.running = True
            self.toggle_btn.config(text="Stop")
            self.status.config(text="Running...")
            threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        while self.running:
            self._scan()
            for _ in range(self.wait * 10):
                if not self.running:
                    return
                time.sleep(0.1)

    def _scan(self):
        templates = []
        for f in sorted(os.listdir(BUTTONS_DIR)):
            if f.lower().endswith(".png"):
                t = cv2.imread(os.path.join(BUTTONS_DIR, f), cv2.IMREAD_GRAYSCALE)
                if t is not None:
                    templates.append(t)
        for t in templates:
            gray, off_x, off_y = grab_gray()
            if t.shape[0] > gray.shape[0] or t.shape[1] > gray.shape[1]:
                continue
            res = cv2.matchTemplate(gray, t, cv2.TM_CCOEFF_NORMED)
            _, score, _, loc = cv2.minMaxLoc(res)
            if score >= THRESHOLD:
                cx = off_x + loc[0] + t.shape[1] // 2
                cy = off_y + loc[1] + t.shape[0] // 2
                click_at(cx, cy)
                time.sleep(0.2)

    def on_close(self):
        self.running = False
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    App().run()
