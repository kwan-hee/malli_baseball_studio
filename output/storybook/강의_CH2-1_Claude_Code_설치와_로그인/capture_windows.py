# 강의 CH2-1 — Windows 실제 화면 캡처 (W02 설정 > 시스템 > 정보 / W03·W04 시작 메뉴 검색 / W05 탐색기)
# 창을 앞으로 띄운 뒤 그 창 영역만 잘라 screens/ 에 저장. 개인정보 가림은 render_screens.py 에서 처리.
import ctypes
import os
import subprocess
import sys
import time
from ctypes import wintypes
from pathlib import Path

from PIL import ImageGrab

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ctypes.windll.shcore.SetProcessDpiAwareness(2)
U = ctypes.windll.user32
OUT = Path(__file__).parent / "screens"
OUT.mkdir(exist_ok=True)
VK_LWIN, VK_ESC = 0x5B, 0x1B


def key(vk, up=False):
    U.keybd_event(vk, 0, 2 if up else 0, 0)


def tap(vk):
    key(vk)
    time.sleep(0.05)
    key(vk, True)


def type_text(s):
    for ch in s:
        vk = U.VkKeyScanW(ord(ch)) & 0xFF
        tap(vk)
        time.sleep(0.08)


def find_window(title_part):
    found = []

    def cb(h, _):
        n = U.GetWindowTextLengthW(h)
        if n and U.IsWindowVisible(h):
            b = ctypes.create_unicode_buffer(n + 1)
            U.GetWindowTextW(h, b, n + 1)
            if title_part in b.value:
                found.append(h)
        return True

    U.EnumWindows(ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)(cb), 0)
    return found[0] if found else None


def grab_window(h, name, size=(1280, 800)):
    U.ShowWindow(h, 9)
    U.MoveWindow(h, 80, 60, *size, True)
    time.sleep(0.6)
    U.SetForegroundWindow(h)
    time.sleep(1.2)
    r = wintypes.RECT()
    ctypes.windll.dwmapi.DwmGetWindowAttribute(h, 9, ctypes.byref(r), ctypes.sizeof(r))  # 그림자 제외 영역
    ImageGrab.grab(bbox=(r.left, r.top, r.right, r.bottom), all_screens=True).save(OUT / f"{name}_raw.png")
    print("saved", name, r.right - r.left, r.bottom - r.top)


def wait_window(title_part, sec=10):
    for _ in range(sec * 4):
        h = find_window(title_part)
        if h:
            return h
        time.sleep(0.25)
    sys.exit(f"창 없음: {title_part}")


def settings_about():
    subprocess.Popen(["explorer.exe", "ms-settings:about"])
    h = wait_window("설정")
    time.sleep(2.5)
    grab_window(h, "W02")
    U.SetCursorPos(80 + 850, 60 + 500)  # 오른쪽 본문 위에서 휠 → 'Windows 사양' 까지
    for _ in range(12):
        U.mouse_event(0x0800, 0, 0, -120, 0)
        time.sleep(0.1)
    time.sleep(1.0)
    grab_window(h, "W02b")
    U.PostMessageW(h, 0x0010, 0, 0)  # WM_CLOSE


def start_menu():
    full = ImageGrab.grab(all_screens=False)
    tap(VK_LWIN)
    time.sleep(1.5)
    ImageGrab.grab(all_screens=False).save(OUT / "W03_raw.png")
    type_text("powershell")
    time.sleep(2.0)
    ImageGrab.grab(all_screens=False).save(OUT / "W04_raw.png")
    tap(VK_ESC)
    print("saved W03 W04", full.size)


def explorer_home():
    home = Path(os.environ["USERPROFILE"])
    (home / "malli-studio").mkdir(exist_ok=True)
    subprocess.Popen(f'explorer.exe /select,"{home / "malli-studio"}"')  # 폴더가 선택·스크롤된 상태로 열기
    h = wait_window(home.name)
    U.SetCursorPos(5, 5)  # 마우스 툴팁이 찍히지 않게
    time.sleep(2.0)
    grab_window(h, "W05", (1100, 700))
    U.PostMessageW(h, 0x0010, 0, 0)


if __name__ == "__main__":
    which = sys.argv[1:] or ["about", "start", "explorer"]
    if "about" in which:
        settings_about()
    if "start" in which:
        start_menu()
    if "explorer" in which:
        explorer_home()
