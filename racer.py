# PsyRacer V1.0 by DiamondHand.Dev
# Arcade pseudo-3D racer. Arrows/WASD to drive. Esc: menu.

import ctypes
import math
import os
import random
import re
import shutil
import sys
import tempfile
import threading
import time
from ctypes import wintypes

TARGET_WIDTH = 158
TARGET_HEIGHT = 48
WIDTH = TARGET_WIDTH
HEIGHT = TARGET_HEIGHT
HORIZON = 14
FPS = 20
MIRROR_WIDTH = 32
MIRROR_HEIGHT = 14
MIRROR_HORIZON = 4
MIRROR_GAP = 2
MIRROR_BOX_W = MIRROR_WIDTH + 2
FRAME_WIDTH = WIDTH + MIRROR_GAP + MIRROR_BOX_W
GAME_DIR = os.path.dirname(os.path.abspath(__file__))
HIGH_SCORES_FILE = os.path.join(GAME_DIR, "racer_scores.txt")
MUSIC_FILE = os.path.join(GAME_DIR, "Assets", "Background Music.mp3")
GAME_NAME = "PsyRacer"
GAME_VERSION = "V1.0"
GAME_TITLE = "PsyRacer V1.0"
GAME_BYLINE = "by Diamond Hand Dev"
RESET = "\033[0m"
MENU_INNER = 76
MENU_ROWS = HEIGHT + 2
ENABLE_WRAP_AT_EOL_OUTPUT = 0x0002

DIFFICULTY = {
    "easy": {"max_speed": 1.35, "accel": 0.018, "finish": 10000, "ai_speed": 0.88},
    "medium": {"max_speed": 1.65, "accel": 0.022, "finish": 20000, "ai_speed": 0.96},
    "hard": {"max_speed": 1.95, "accel": 0.026, "finish": 30000, "ai_speed": 1.05},
}

AI_FIELD = [
    {"number": 2, "name": "Nova", "hue": 0, "x": -0.58, "z": 7, "pace": 0.92},
    {"number": 7, "name": "Volt", "hue": 210, "x": 0.58, "z": 7, "pace": 0.95},
    {"number": 11, "name": "Apex", "hue": 45, "x": -0.30, "z": 13, "pace": 1.00},
    {"number": 18, "name": "Blaze", "hue": 25, "x": 0.30, "z": 13, "pace": 0.97},
    {"number": 24, "name": "Ion", "hue": 180, "x": 0.0, "z": 19, "pace": 1.03},
]

VK_W = 0x57
VK_A = 0x41
VK_S = 0x53
VK_D = 0x44
VK_UP = 0x26
VK_DOWN = 0x28
VK_LEFT = 0x25
VK_RIGHT = 0x27
VK_ESCAPE = 0x1B
VK_Q = 0x51

STD_INPUT_HANDLE = -10
STD_OUTPUT_HANDLE = -11
KEY_EVENT = 0x0001
ENABLE_PROCESSED_INPUT = 0x0001
ENABLE_EXTENDED_FLAGS = 0x0080
ENABLE_PROCESSED_OUTPUT = 0x0001
ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
SW_RESTORE = 9
SW_MAXIMIZE = 3
GA_ROOT = 2
GA_ROOTOWNER = 3
WM_SYSCOMMAND = 0x0112
SC_MAXIMIZE = 0xF030
SC_RESTORE = 0xF120
TH32CS_SNAPPROCESS = 0x00000002

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
user32 = ctypes.WinDLL("user32", use_last_error=True)
winmm = ctypes.WinDLL("winmm", use_last_error=True)

kernel32.GetStdHandle.argtypes = [wintypes.DWORD]
kernel32.GetStdHandle.restype = wintypes.HANDLE
kernel32.GetConsoleMode.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
kernel32.GetConsoleMode.restype = wintypes.BOOL
kernel32.SetConsoleMode.argtypes = [wintypes.HANDLE, wintypes.DWORD]
kernel32.SetConsoleMode.restype = wintypes.BOOL
kernel32.GetNumberOfConsoleInputEvents.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
kernel32.GetNumberOfConsoleInputEvents.restype = wintypes.BOOL
kernel32.ReadConsoleInputW.argtypes = [
    wintypes.HANDLE,
    ctypes.c_void_p,
    wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD),
]
kernel32.ReadConsoleInputW.restype = wintypes.BOOL
kernel32.FlushConsoleInputBuffer.argtypes = [wintypes.HANDLE]
kernel32.FlushConsoleInputBuffer.restype = wintypes.BOOL
user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
user32.GetAsyncKeyState.restype = wintypes.SHORT
winmm.mciSendStringW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.UINT, wintypes.HANDLE]
winmm.mciSendStringW.restype = wintypes.DWORD


class _KEY_EVENT_RECORD(ctypes.Structure):
    _fields_ = [
        ("bKeyDown", wintypes.BOOL),
        ("wRepeatCount", wintypes.WORD),
        ("wVirtualKeyCode", wintypes.WORD),
        ("wVirtualScanCode", wintypes.WORD),
        ("UnicodeChar", wintypes.WCHAR),
        ("dwControlKeyState", wintypes.DWORD),
    ]


class _INPUT_RECORD_EVENT(ctypes.Union):
    _fields_ = [("KeyEvent", _KEY_EVENT_RECORD), ("pad", ctypes.c_byte * 16)]


class INPUT_RECORD(ctypes.Structure):
    _fields_ = [("EventType", wintypes.WORD), ("Event", _INPUT_RECORD_EVENT)]


class COORD(ctypes.Structure):
    _fields_ = [("X", wintypes.SHORT), ("Y", wintypes.SHORT)]


class SMALL_RECT(ctypes.Structure):
    _fields_ = [
        ("Left", wintypes.SHORT),
        ("Top", wintypes.SHORT),
        ("Right", wintypes.SHORT),
        ("Bottom", wintypes.SHORT),
    ]


class CONSOLE_SCREEN_BUFFER_INFO(ctypes.Structure):
    _fields_ = [
        ("dwSize", COORD),
        ("dwCursorPosition", COORD),
        ("wAttributes", wintypes.WORD),
        ("srWindow", SMALL_RECT),
        ("dwMaximumWindowSize", COORD),
    ]


kernel32.SetConsoleScreenBufferSize.argtypes = [wintypes.HANDLE, COORD]
kernel32.SetConsoleScreenBufferSize.restype = wintypes.BOOL
kernel32.SetConsoleWindowInfo.argtypes = [wintypes.HANDLE, wintypes.BOOL, ctypes.POINTER(SMALL_RECT)]
kernel32.SetConsoleWindowInfo.restype = wintypes.BOOL
kernel32.GetLargestConsoleWindowSize.argtypes = [wintypes.HANDLE]
kernel32.GetLargestConsoleWindowSize.restype = COORD
kernel32.GetConsoleScreenBufferInfo.argtypes = [
    wintypes.HANDLE,
    ctypes.POINTER(CONSOLE_SCREEN_BUFFER_INFO),
]
kernel32.GetConsoleScreenBufferInfo.restype = wintypes.BOOL
kernel32.GetConsoleWindow.argtypes = []
kernel32.GetConsoleWindow.restype = wintypes.HWND
kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.CloseHandle.restype = wintypes.BOOL
kernel32.FreeConsole.argtypes = []
kernel32.FreeConsole.restype = wintypes.BOOL
user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
user32.GetAncestor.restype = wintypes.HWND
user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
user32.ShowWindow.restype = wintypes.BOOL
user32.SetForegroundWindow.argtypes = [wintypes.HWND]
user32.SetForegroundWindow.restype = wintypes.BOOL
user32.GetForegroundWindow.argtypes = []
user32.GetForegroundWindow.restype = wintypes.HWND
user32.IsWindowVisible.argtypes = [wintypes.HWND]
user32.IsWindowVisible.restype = wintypes.BOOL
user32.IsZoomed.argtypes = [wintypes.HWND]
user32.IsZoomed.restype = wintypes.BOOL
user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.PostMessageW.restype = wintypes.BOOL
user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetClassNameW.restype = ctypes.c_int
user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user32.GetWindowThreadProcessId.restype = wintypes.DWORD
WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
user32.EnumWindows.argtypes = [WNDENUMPROC, wintypes.LPARAM]
user32.EnumWindows.restype = wintypes.BOOL
user32.BringWindowToTop.argtypes = [wintypes.HWND]
user32.BringWindowToTop.restype = wintypes.BOOL
user32.SetActiveWindow.argtypes = [wintypes.HWND]
user32.SetActiveWindow.restype = wintypes.HWND
user32.AttachThreadInput.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.BOOL]
user32.AttachThreadInput.restype = wintypes.BOOL
user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
user32.GetWindowRect.restype = wintypes.BOOL
user32.SetWindowPos.argtypes = [
    wintypes.HWND,
    wintypes.HWND,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    wintypes.UINT,
]
user32.SetWindowPos.restype = wintypes.BOOL
user32.MonitorFromWindow.argtypes = [wintypes.HWND, wintypes.DWORD]
user32.MonitorFromWindow.restype = wintypes.HMONITOR
user32.GetWindowPlacement.argtypes = [wintypes.HWND, ctypes.c_void_p]
user32.GetWindowPlacement.restype = wintypes.BOOL
user32.SetWindowPlacement.argtypes = [wintypes.HWND, ctypes.c_void_p]
user32.SetWindowPlacement.restype = wintypes.BOOL
user32.SendMessageTimeoutW.argtypes = [
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
    wintypes.UINT,
    wintypes.UINT,
    ctypes.POINTER(wintypes.DWORD),
]
user32.SendMessageTimeoutW.restype = wintypes.LPARAM
kernel32.GetCurrentThreadId.argtypes = []
kernel32.GetCurrentThreadId.restype = wintypes.DWORD

HWND_TOP = wintypes.HWND(0)
SWP_SHOWWINDOW = 0x0040
SWP_FRAMECHANGED = 0x0020
MONITOR_DEFAULTTONEAREST = 2
SMTO_ABORTIFHUNG = 0x0002


class MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", wintypes.RECT),
        ("rcWork", wintypes.RECT),
        ("dwFlags", wintypes.DWORD),
    ]


class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


class WINDOWPLACEMENT(ctypes.Structure):
    _fields_ = [
        ("length", wintypes.UINT),
        ("flags", wintypes.UINT),
        ("showCmd", wintypes.UINT),
        ("ptMinPosition", POINT),
        ("ptMaxPosition", POINT),
        ("rcNormalPosition", wintypes.RECT),
    ]


user32.GetMonitorInfoW.argtypes = [wintypes.HMONITOR, ctypes.POINTER(MONITORINFO)]
user32.GetMonitorInfoW.restype = wintypes.BOOL


class PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("th32DefaultHeapID", ctypes.c_size_t),
        ("th32ModuleID", wintypes.DWORD),
        ("cntThreads", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD),
        ("pcPriClassBase", ctypes.c_long),
        ("dwFlags", wintypes.DWORD),
        ("szExeFile", wintypes.WCHAR * 260),
    ]


kernel32.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
kernel32.Process32FirstW.restype = wintypes.BOOL
kernel32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
kernel32.Process32NextW.restype = wintypes.BOOL


def _handle_from_std(kind):
    return kernel32.GetStdHandle(ctypes.c_ulong(kind).value)


def get_window_size():
    info = CONSOLE_SCREEN_BUFFER_INFO()
    handle = _handle_from_std(STD_OUTPUT_HANDLE)
    if kernel32.GetConsoleScreenBufferInfo(handle, ctypes.byref(info)):
        cols = int(info.srWindow.Right - info.srWindow.Left + 1)
        rows = int(info.srWindow.Bottom - info.srWindow.Top + 1)
        if cols >= 40 and rows >= 12:
            return cols, rows
    return 80, 25


def apply_layout(cols=None, rows=None, tight=False):
    """Fit the playfield to the visible window so frames cannot wrap/scroll."""
    global WIDTH, HEIGHT, HORIZON, FRAME_WIDTH, MENU_ROWS, MENU_INNER
    global MIRROR_WIDTH, MIRROR_HEIGHT, MIRROR_HORIZON, MIRROR_BOX_W, MIRROR_GAP
    if cols is None or rows is None:
        if "VIDEO" in globals() and VIDEO.active:
            return
        cols, rows = get_window_size()
    cols = max(60, cols if tight else cols - 1)
    rows = max(16, rows)

    HEIGHT = min(TARGET_HEIGHT, max(18, rows - 2))
    HORIZON = max(5, int(round(HEIGHT * 14 / float(TARGET_HEIGHT))))
    MIRROR_GAP = 2 if cols >= 120 else 1
    if cols >= 150:
        MIRROR_WIDTH = 32
    elif cols >= 110:
        MIRROR_WIDTH = 26
    else:
        MIRROR_WIDTH = 20
    MIRROR_BOX_W = MIRROR_WIDTH + 2
    MIRROR_HEIGHT = min(16, max(8, HEIGHT // 3))
    MIRROR_HORIZON = max(3, MIRROR_HEIGHT * 4 // 14)
    mirror_span = MIRROR_GAP + MIRROR_BOX_W
    WIDTH = min(TARGET_WIDTH, max(52, cols - mirror_span))
    FRAME_WIDTH = min(cols, WIDTH + mirror_span)
    if FRAME_WIDTH > cols:
        WIDTH = max(52, cols - mirror_span)
        FRAME_WIDTH = min(cols, WIDTH + mirror_span)
    MENU_ROWS = min(rows, HEIGHT + 2)
    MENU_INNER = min(76, max(40, WIDTH - 6))
    if MENU_INNER % 2:
        MENU_INNER -= 1


_host_hwnd = None
_host_was_zoomed = False
_host_rect = None


def _window_class(hwnd):
    if not hwnd:
        return ""
    buf = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buf, 256)
    return buf.value


def _window_pid(hwnd):
    pid = wintypes.DWORD(0)
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return pid.value


def _ancestor_pids():
    pids = {os.getpid()}
    snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if not snapshot or snapshot == ctypes.c_void_p(-1).value:
        return pids
    try:
        entry = PROCESSENTRY32W()
        entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
        parents = {}
        if kernel32.Process32FirstW(snapshot, ctypes.byref(entry)):
            while True:
                parents[entry.th32ProcessID] = entry.th32ParentProcessID
                if not kernel32.Process32NextW(snapshot, ctypes.byref(entry)):
                    break
        pid = os.getpid()
        seen = set()
        while pid and pid not in seen:
            seen.add(pid)
            pids.add(pid)
            pid = parents.get(pid, 0)
    finally:
        kernel32.CloseHandle(snapshot)
    return pids


def _visible_root(hwnd):
    if not hwnd:
        return None
    root = user32.GetAncestor(hwnd, GA_ROOTOWNER) or user32.GetAncestor(hwnd, GA_ROOT) or hwnd
    return root


def find_host_window():
    candidates = []
    hwnd = kernel32.GetConsoleWindow()
    if hwnd:
        candidates.append(_visible_root(hwnd) or hwnd)
    fg = user32.GetForegroundWindow()
    if fg:
        candidates.append(_visible_root(fg) or fg)

    family = _ancestor_pids()
    found = []

    def _enum(hwnd, _lparam):
        if not user32.IsWindowVisible(hwnd):
            return True
        if _window_pid(hwnd) not in family:
            return True
        found.append(hwnd)
        return True

    callback = WNDENUMPROC(_enum)
    user32.EnumWindows(callback, 0)
    candidates.extend(found)

    ranked = []
    seen = set()
    for hwnd in candidates:
        if not hwnd or hwnd in seen:
            continue
        seen.add(hwnd)
        cls = _window_class(hwnd)
        score = 0
        if cls == "CASCADIA_HOSTING_WINDOW_CLASS":
            score += 40
        elif cls in ("ConsoleWindowClass", "PseudoConsoleWindow"):
            score += 20
        if user32.IsWindowVisible(hwnd):
            score += 10
        ranked.append((score, hwnd))
    ranked.sort(key=lambda item: item[0], reverse=True)
    if ranked and ranked[0][0] > 0:
        return ranked[0][1]
    return candidates[0] if candidates else None


def _force_focus(hwnd):
    fg = user32.GetForegroundWindow()
    ours = kernel32.GetCurrentThreadId()
    other = user32.GetWindowThreadProcessId(fg, None) if fg else 0
    attached = False
    if other and other != ours:
        attached = bool(user32.AttachThreadInput(ours, other, True))
    user32.ShowWindow(hwnd, SW_RESTORE)
    user32.BringWindowToTop(hwnd)
    user32.SetForegroundWindow(hwnd)
    user32.SetActiveWindow(hwnd)
    if attached:
        user32.AttachThreadInput(ours, other, False)


def _fill_monitor(hwnd):
    monitor = user32.MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST)
    if not monitor:
        return False
    info = MONITORINFO()
    info.cbSize = ctypes.sizeof(MONITORINFO)
    if not user32.GetMonitorInfoW(monitor, ctypes.byref(info)):
        return False
    area = info.rcWork
    return bool(
        user32.SetWindowPos(
            hwnd,
            HWND_TOP,
            area.left,
            area.top,
            area.right - area.left,
            area.bottom - area.top,
            SWP_SHOWWINDOW | SWP_FRAMECHANGED,
        )
    )


def _placement_maximize(hwnd):
    place = WINDOWPLACEMENT()
    place.length = ctypes.sizeof(WINDOWPLACEMENT)
    if not user32.GetWindowPlacement(hwnd, ctypes.byref(place)):
        return False
    place.showCmd = SW_MAXIMIZE
    return bool(user32.SetWindowPlacement(hwnd, ctypes.byref(place)))


def maximize_game_window():
    global _host_hwnd, _host_was_zoomed, _host_rect
    hwnd = find_host_window()
    _host_hwnd = hwnd
    if not hwnd:
        return
    _host_was_zoomed = bool(user32.IsZoomed(hwnd))
    rect = wintypes.RECT()
    if user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        _host_rect = (rect.left, rect.top, rect.right, rect.bottom)
    else:
        _host_rect = None
    _force_focus(hwnd)
    if not _host_was_zoomed:
        user32.ShowWindow(hwnd, SW_MAXIMIZE)
        result = wintypes.DWORD(0)
        user32.SendMessageTimeoutW(
            hwnd,
            WM_SYSCOMMAND,
            SC_MAXIMIZE,
            0,
            SMTO_ABORTIFHUNG,
            250,
            ctypes.byref(result),
        )
        user32.PostMessageW(hwnd, WM_SYSCOMMAND, SC_MAXIMIZE, 0)
        _placement_maximize(hwnd)
        _fill_monitor(hwnd)
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.25)


def restore_game_window():
    if not _host_hwnd or _host_was_zoomed:
        return
    user32.PostMessageW(_host_hwnd, WM_SYSCOMMAND, SC_RESTORE, 0)
    user32.ShowWindow(_host_hwnd, SW_RESTORE)
    if _host_rect:
        left, top, right, bottom = _host_rect
        user32.SetWindowPos(
            _host_hwnd,
            HWND_TOP,
            left,
            top,
            right - left,
            bottom - top,
            SWP_SHOWWINDOW | SWP_FRAMECHANGED,
        )


def configure_console_size():
    maximize_game_window()
    handle = _handle_from_std(STD_OUTPUT_HANDLE)
    try:
        largest = kernel32.GetLargestConsoleWindowSize(handle)
        cols, rows = get_window_size()
        want_cols = TARGET_WIDTH + 2 + 34
        want_rows = TARGET_HEIGHT + 2
        if largest.X > 0:
            want_cols = min(max(want_cols, cols), int(largest.X))
        if largest.Y > 0:
            want_rows = min(max(want_rows, rows), int(largest.Y))
        kernel32.SetConsoleScreenBufferSize(
            handle, COORD(max(want_cols, cols), max(want_rows, rows) + 4)
        )
        rect = SMALL_RECT(0, 0, want_cols - 1, want_rows - 1)
        kernel32.SetConsoleWindowInfo(handle, True, ctypes.byref(rect))
    except Exception:
        pass
    apply_layout()


def enter_display():
    console_write("\033[?1049h\033[?25l\033[?7l\033[2J\033[H")


def console_write(text):
    if "VIDEO" in globals() and VIDEO.active:
        return
    try:
        if sys.stdout is None:
            return
        sys.stdout.write(text)
        sys.stdout.flush()
    except Exception:
        pass


def leave_display():
    VIDEO.stop()
    console_write("\033[?7h\033[?25h\033[?1049l")
    restore_game_window()


_CSI_RE = re.compile(r"\033\[([0-9;?]*)([A-Za-z])")
SPRITE_OVERLAYS = []
SPRITE_FILES = {
    "rear": "car_rear.png",
    "side": "car_side.png",
    "skyline": "skyline.png",
    "tree": "tree.png",
    "tree_tall": "tree_tall.png",
    "cloud": "cloud.png",
    "cloud_small": "cloud_small.png",
    "road": "road.png",
}
# car_side.png faces right (Race car Splash). Overlay wheels map through
# the same scale as the car, no horizontal flip. Near-side rear then front.
SIDE_WHEEL_SRC = (
    (348, 288, 98),
    (1168, 300, 100),
)
SPRITE_CELL_WIDTH = {
    "side": 22.0,
    "tree": 10.5,
    "tree_tall": 8.5,
    "cloud": 22.0,
    "cloud_small": 12.0,
}
SCENERY_SPRITES = {
    "skyline.png",
    "cloud.png",
    "cloud_small.png",
}
CROWD_KINDS = []
CROWD_TALL = set()
CROWD_FLASHERS = set()
CROWD_SHORT = set()
for _crowd_i in range(1, 31):
    _kind = f"person_{_crowd_i:02d}"
    SPRITE_FILES[_kind] = f"{_kind}.png"
    SPRITE_CELL_WIDTH[_kind] = 10.5
    CROWD_KINDS.append(_kind)
CROWD_TALL.update(
    f"person_{n:02d}" for n in (4, 5, 7, 16, 20, 22, 26)
)
CROWD_FLASHERS.update(
    f"person_{n:02d}" for n in (3, 5, 8, 15, 18, 24, 29)
)
CROWD_SHORT.add("person_02")
SCENE_BANDS = []
SCENE_EDGES = []
RAIN_GLYPHS = (
    "ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝ"
    "012345789:.=*+<>|"
)
RAIN_CELLS = []


def _visible_width(text):
    width = 0
    index = 0
    length = len(text)
    while index < length:
        if text.startswith("\033[", index):
            match = _CSI_RE.match(text, index)
            if match:
                index = match.end()
                continue
        char = text[index]
        index += 1
        if char not in "\n\r":
            width += 1
    return width


class GameVideo:
    """Real OS window via pygame so maximize actually works."""

    def __init__(self):
        self.active = False
        self.closed = False
        self.screen = None
        self.font = None
        self.cell = (9, 16)
        self.hwnd = None
        self._pygame = None
        self._keys = []
        self._pressed = set()
        self._console_hwnd = None
        self.fullscreen = False
        self.origin = (0, 0)
        self.sprites = {}
        self._sprite_cache = {}
        self._grid_cols = 80
        self._grid_rows = 24
        self._needs_refit = False
        self._held_pg = set()
        self.matrix_font = None

    def start(self):
        import pygame

        self._pygame = pygame
        pygame.init()
        pygame.event.set_blocked(None)
        pygame.event.set_allowed([pygame.QUIT])
        pygame.display.set_caption(GAME_TITLE)
        pygame.display.set_mode((960, 540), pygame.RESIZABLE)
        self._maximize_current()
        self.fullscreen = False
        self.hwnd = pygame.display.get_wm_info().get("window")
        self.screen = pygame.display.get_surface()
        if self.screen:
            self._load_sprites()
            self._fit_font()
            self._apply_from_surface()
        self.active = True
        self._detach_console()
        pygame.event.clear()
        if self.hwnd:
            user32.SetForegroundWindow(self.hwnd)
        pygame.event.pump()
        pygame.display.flip()

    def _maximize_current(self):
        pygame = self._pygame
        import pygame._sdl2.video as sdl_video

        win = sdl_video.Window.from_display_module()
        win.maximize()
        deadline = time.time() + 2.0
        while time.time() < deadline:
            pygame.event.pump()
            pygame.display.flip()
            hwnd = pygame.display.get_wm_info().get("window")
            if hwnd and user32.IsZoomed(hwnd):
                break
            time.sleep(0.05)
        hwnd = pygame.display.get_wm_info().get("window")
        if hwnd and not user32.IsZoomed(hwnd):
            user32.ShowWindow(hwnd, SW_MAXIMIZE)
            time.sleep(0.15)
            pygame.event.pump()
            pygame.display.flip()

    def _detach_console(self):
        """Detach stdout so later writes cannot crash after the console is gone."""
        try:
            nul = open(os.devnull, "w", encoding="utf-8")
            sys.stdout = nul
            sys.stderr = nul
        except Exception:
            pass
        pygame_hwnd = None
        if self._pygame is not None:
            pygame_hwnd = self._pygame.display.get_wm_info().get("window")
        hwnd = kernel32.GetConsoleWindow()
        self._console_hwnd = hwnd
        if hwnd and hwnd != pygame_hwnd:
            root = _visible_root(hwnd) or hwnd
            if _window_class(root) != "CASCADIA_HOSTING_WINDOW_CLASS":
                user32.ShowWindow(hwnd, 0)
        kernel32.FreeConsole()
        self._console_hwnd = None

    def set_fullscreen(self, enabled):
        pygame = self._pygame
        if pygame is None or pygame.display.get_surface() is None:
            return
        surf = pygame.display.get_surface()
        currently = bool(surf.get_flags() & pygame.FULLSCREEN)
        if bool(enabled) != currently:
            pygame.display.toggle_fullscreen()
            for _ in range(10):
                pygame.event.pump()
                pygame.display.flip()
                time.sleep(0.03)
        if not enabled:
            try:
                import pygame._sdl2.video as sdl_video

                sdl_video.Window.from_display_module().maximize()
            except Exception:
                pass
            hwnd = pygame.display.get_wm_info().get("window")
            if hwnd:
                user32.ShowWindow(hwnd, SW_MAXIMIZE)
            pygame.event.pump()
            pygame.display.flip()
        self.hwnd = pygame.display.get_wm_info().get("window")
        self.screen = pygame.display.get_surface()
        self.fullscreen = bool(
            self.screen and (self.screen.get_flags() & pygame.FULLSCREEN)
        )
        if self.screen:
            self._fit_font()
            self._apply_from_surface()

    def _trim_sprite(self, image):
        pygame = self._pygame
        width, height = image.get_size()
        try:
            raw = pygame.image.tostring(image, "RGBA")
        except Exception:
            return image
        mv = memoryview(raw)
        stride = width * 4

        def row_opaque(y):
            base = y * stride
            for x in range(width):
                if mv[base + x * 4 + 3] > 20:
                    return True
            return False

        def col_opaque(x, y0, y1):
            for y in range(y0, y1 + 1):
                if mv[y * stride + x * 4 + 3] > 20:
                    return True
            return False

        min_y = 0
        while min_y < height and not row_opaque(min_y):
            min_y += 1
        max_y = height - 1
        while max_y >= min_y and not row_opaque(max_y):
            max_y -= 1
        if max_y < min_y:
            return image
        min_x = 0
        while min_x < width and not col_opaque(min_x, min_y, max_y):
            min_x += 1
        max_x = width - 1
        while max_x >= min_x and not col_opaque(max_x, min_y, max_y):
            max_x -= 1
        pad = 3
        x = max(0, min_x - pad)
        y = max(0, min_y - pad)
        w = min(width - x, (max_x - min_x + 1) + pad * 2)
        h = min(height - y, (max_y - min_y + 1) + pad * 2)
        if w < 8 or h < 8 or (w >= width - 2 and h >= height - 2):
            return image
        return image.subsurface((x, y, w, h)).copy()

    def _load_sprites(self):
        pygame = self._pygame
        folder = os.path.join(GAME_DIR, "Assets", "sprites")
        self.sprites = {}
        names = []
        seen = set()
        for name in SPRITE_FILES.values():
            if name not in seen:
                seen.add(name)
                names.append(name)
        for name in names:
            path = os.path.join(folder, name)
            if not os.path.isfile(path):
                continue
            image = pygame.image.load(path).convert_alpha()
            if (
                name != "road.png"
                and image.get_width() > 2
                and image.get_height() > 2
                and image.get_at((2, 2))[3] > 0
            ):
                bg = image.get_at((2, 2))
                width, height = image.get_size()
                threshold = 72
                for y in range(height):
                    for x in range(width):
                        pixel = image.get_at((x, y))
                        if (
                            abs(pixel[0] - bg[0]) < threshold
                            and abs(pixel[1] - bg[1]) < threshold
                            and abs(pixel[2] - bg[2]) < threshold
                        ):
                            image.set_at((x, y), (0, 0, 0, 0))
            if name in SCENERY_SPRITES and name not in ("skyline.png", "road.png"):
                image = self._trim_sprite(image)
            self.sprites[name] = image
        self._sprite_cache = {}

    def _scaled_sprite(self, name, dest_w, dest_h, flip=False, hue=None):
        pygame = self._pygame
        key = (name, dest_w, dest_h, flip, None if hue is None else round(hue, 0))
        cached = self._sprite_cache.get(key)
        if cached is not None:
            return cached
        image = self.sprites.get(name)
        if image is None:
            return None
        sprite = pygame.transform.smoothscale(image, (dest_w, dest_h))
        if flip:
            sprite = pygame.transform.flip(sprite, True, False)
        if hue is not None:
            sprite = self.tint_sprite(sprite, hue)
        self._sprite_cache[key] = sprite
        if len(self._sprite_cache) > 160:
            self._sprite_cache.pop(next(iter(self._sprite_cache)))
        return sprite

    def tint_sprite(self, image, hue):
        pygame = self._pygame
        tinted = image.copy()
        red, green, blue = hsv_rgb(hue, saturation=0.55, value=1.0)
        tinted.fill((red, green, blue), special_flags=pygame.BLEND_RGB_MULT)
        return tinted

    def toggle_fullscreen(self):
        self.set_fullscreen(not self.fullscreen)

    def display_label(self):
        return "Fullscreen" if self.fullscreen else "Windowed"

    def _fit_font(self):
        pygame = self._pygame
        width, height = self.screen.get_size()
        margin = 8
        inner_w = max(200, width - 2 * margin)
        inner_h = max(160, height - 2 * margin)
        chosen = None
        cell = (8, 16)
        cols = rows = 0
        for size in range(18, 7, -1):
            font = pygame.font.SysFont("consolas", size)
            cell_w = max(font.size(ch)[0] for ch in "MW█┌│#")
            cell_h = max(font.get_linesize(), max(font.size(ch)[1] for ch in "M█g┌"))
            if cell_w < 1 or cell_h < 1:
                continue
            fit_cols = inner_w // cell_w
            fit_rows = inner_h // cell_h
            if fit_cols >= 72 and fit_rows >= 22:
                chosen = font
                cell = (cell_w, cell_h)
                cols, rows = fit_cols, fit_rows
                break
        if chosen is None:
            chosen = pygame.font.SysFont("consolas", 10)
            cell_w = max(1, chosen.size("M")[0])
            cell_h = max(1, chosen.get_linesize())
            cell = (cell_w, cell_h)
            cols = max(60, inner_w // cell_w)
            rows = max(16, inner_h // cell_h)
        self.font = chosen
        self.cell = cell
        self._grid_cols = cols
        self._grid_rows = rows
        px = max(10, cell[1])
        self.matrix_font = None
        for path in (
            r"C:\Windows\Fonts\msgothic.ttc",
            r"C:\Windows\Fonts\YuGothR.ttc",
        ):
            try:
                self.matrix_font = pygame.font.Font(path, px)
                break
            except Exception:
                continue
        if self.matrix_font is None:
            self.matrix_font = pygame.font.SysFont("ms gothic", px)

    def _apply_from_surface(self):
        apply_layout(self._grid_cols, self._grid_rows, tight=True)

    def pump(self):
        if not self.active:
            return
        pygame = self._pygame
        try:
            pygame.event.pump()
        except Exception:
            return
        try:
            if pygame.event.peek(pygame.QUIT):
                pygame.event.get(pygame.QUIT)
                self.closed = True
                self._keys.append("esc")
        except Exception:
            pass
        mapping = {
            pygame.K_w: VK_W,
            pygame.K_a: VK_A,
            pygame.K_s: VK_S,
            pygame.K_d: VK_D,
            pygame.K_UP: VK_UP,
            pygame.K_DOWN: VK_DOWN,
            pygame.K_LEFT: VK_LEFT,
            pygame.K_RIGHT: VK_RIGHT,
            pygame.K_ESCAPE: VK_ESCAPE,
            pygame.K_q: VK_Q,
        }
        names = {
            pygame.K_UP: "up",
            pygame.K_DOWN: "down",
            pygame.K_LEFT: "left",
            pygame.K_RIGHT: "right",
            pygame.K_RETURN: "enter",
            pygame.K_KP_ENTER: "enter",
            pygame.K_ESCAPE: "esc",
            pygame.K_BACKSPACE: "backspace",
            pygame.K_SPACE: " ",
            pygame.K_F11: "f11",
        }
        try:
            pressed = pygame.key.get_pressed()
        except Exception:
            return
        now = set()
        for code in range(pygame.K_a, pygame.K_z + 1):
            if pressed[code]:
                now.add(code)
        for code in range(pygame.K_0, pygame.K_9 + 1):
            if pressed[code]:
                now.add(code)
        for code in list(mapping) + list(names):
            try:
                if pressed[code]:
                    now.add(code)
            except Exception:
                continue
        newly = now - self._held_pg
        self._held_pg = now
        self._pressed = {mapping[code] for code in now if code in mapping}
        for code in newly:
            if code == pygame.K_F11:
                self.toggle_fullscreen()
                continue
            if code in names:
                self._keys.append(names[code])
            elif pygame.K_a <= code <= pygame.K_z:
                self._keys.append(chr(ord("a") + (code - pygame.K_a)))
            elif pygame.K_0 <= code <= pygame.K_9:
                self._keys.append(chr(ord("0") + (code - pygame.K_0)))

    def pop_key(self):
        if not self.active:
            return None
        self.pump()
        if self._keys:
            return self._keys.pop(0)
        return None

    def flush_keys(self):
        self._keys.clear()
        if self._pygame is None or not self.active:
            self._held_pg = set()
            return
        try:
            self._pygame.event.pump()
            pressed = self._pygame.key.get_pressed()
            held = set()
            pygame = self._pygame
            for code in list(range(pygame.K_a, pygame.K_z + 1)) + list(
                range(pygame.K_0, pygame.K_9 + 1)
            ) + [
                pygame.K_RETURN,
                pygame.K_KP_ENTER,
                pygame.K_ESCAPE,
                pygame.K_SPACE,
                pygame.K_UP,
                pygame.K_DOWN,
            ]:
                if pressed[code]:
                    held.add(code)
            self._held_pg = held
        except Exception:
            self._held_pg = set()

    def key_down(self, vk):
        return vk in self._pressed

    def present(self, text):
        if not self.active:
            return
        self.pump()
        pygame = self._pygame
        self.screen.fill((0, 0, 0) if SCENE_BANDS else (8, 8, 14))
        cell_w, cell_h = self.cell
        lines = text.split("\n")
        content_cols = 1
        for line in lines:
            content_cols = max(content_cols, _visible_width(line))
        content_rows = max(1, len(lines))
        content_w = content_cols * cell_w
        content_h = content_rows * cell_h
        screen_w, screen_h = self.screen.get_size()
        origin_x = max(0, (screen_w - content_w) // 2)
        origin_y = max(0, (screen_h - content_h) // 2)
        self.origin = (origin_x, origin_y)
        self._blit_scene_bands(origin_x, origin_y, cell_w, cell_h, content_cols)
        self._blit_road_layers(origin_x, origin_y, cell_w, cell_h)
        x = y = 0
        run = []
        run_color = (220, 220, 220)
        run_x = 0
        color = (220, 220, 220)

        def flush():
            nonlocal run, run_x
            if not run:
                return
            glyph = "".join(run)
            image = self.font.render(glyph, True, run_color)
            self.screen.blit(image, (origin_x + run_x * cell_w, origin_y + y * cell_h))
            run = []

        index = 0
        length = len(text)
        while index < length:
            if text.startswith("\033[", index):
                match = _CSI_RE.match(text, index)
                if match:
                    params, cmd = match.group(1), match.group(2)
                    if cmd == "m":
                        parts = [int(part) for part in params.split(";") if part.isdigit()] if params else [0]
                        if not parts or parts[0] == 0:
                            color = (220, 220, 220)
                        elif len(parts) >= 5 and parts[0] == 38 and parts[1] == 2:
                            color = (parts[2], parts[3], parts[4])
                    index = match.end()
                    continue
            char = text[index]
            index += 1
            if char == "\n":
                flush()
                y += 1
                x = 0
                continue
            if char == "\r":
                continue
            if color != run_color or not run:
                flush()
                run_color = color
                run_x = x
            run.append(char)
            x += 1
        flush()
        self._blit_matrix_rain(origin_x, origin_y, cell_w, cell_h)
        self._blit_sprites(origin_x, origin_y, cell_w, cell_h)
        self._blit_scene_edges(origin_x, origin_y, cell_w, cell_h, content_cols)
        SPRITE_OVERLAYS.clear()
        SCENE_BANDS.clear()
        SCENE_EDGES.clear()
        RAIN_CELLS.clear()
        pygame.display.flip()

    def _blit_scene_bands(self, origin_x, origin_y, cell_w, cell_h, cols):
        pygame = self._pygame
        width = int(cols * cell_w)
        for y0, y1, color in SCENE_BANDS:
            height = int((y1 - y0) * cell_h)
            if height <= 0 or width <= 0:
                continue
            top = origin_y + int(y0 * cell_h)
            pygame.draw.rect(self.screen, color, (origin_x, top, width, height))

    def _blit_scene_edges(self, origin_x, origin_y, cell_w, cell_h, cols):
        pygame = self._pygame
        width = int(cols * cell_w)
        for anchor, row, color, thickness in SCENE_EDGES:
            if width <= 0 or thickness <= 0:
                continue
            y = origin_y + int(row * cell_h)
            if anchor == "bottom":
                y -= thickness
            pygame.draw.rect(self.screen, color, (origin_x, y, width, thickness))

    def _blit_matrix_rain(self, origin_x, origin_y, cell_w, cell_h):
        if not RAIN_CELLS or self.matrix_font is None:
            return
        pygame = self._pygame
        for gx, gy, glyph, rgb in RAIN_CELLS:
            color = (rgb[0] & ~7, rgb[1] & ~7, rgb[2] & ~7)
            key = ("rain", glyph, color)
            surf = self._sprite_cache.get(key)
            if surf is None:
                surf = self.matrix_font.render(glyph, True, color)
                self._sprite_cache[key] = surf
            self.screen.blit(
                surf,
                (origin_x + gx * cell_w, origin_y + gy * cell_h),
            )

    def _blit_road_layers(self, origin_x, origin_y, cell_w, cell_h):
        for kind, cx, cy, scale, hue, grid_w, tint in SPRITE_OVERLAYS:
            if kind == "road":
                self._blit_road_strip(origin_x, origin_y, cell_w, cell_h, cx, cy, scale, grid_w)

    def _blit_road_strip(self, origin_x, origin_y, cell_w, cell_h, cx, cy, scale, grid_w):
        pygame = self._pygame
        name = SPRITE_FILES.get("road")
        image = self.sprites.get(name) if name else None
        if image is None:
            return
        rows = max(int(scale), int(cy) + 2)
        dest_h = max(8, int((rows - cy) * cell_h))
        dest_w = max(32, int(dest_h * image.get_width() / max(1, image.get_height())))
        sprite = self._scaled_sprite(name, dest_w, dest_h)
        if sprite is None:
            return
        content_w = int(grid_w * cell_w)
        top = origin_y + int(cy * cell_h)
        offset = int(cx * cell_w) % dest_w
        x = origin_x - offset
        while x < origin_x + content_w:
            self.screen.blit(sprite, (x, top))
            x += dest_w

    def _make_wheel(self, radius, angle, style="race"):
        pygame = self._pygame
        quant = 8 if style == "neon" else 6
        key = ("wheel", style, int(radius), int(angle * quant) % (quant * 8))
        cached = self._sprite_cache.get(key)
        if cached is not None:
            return cached
        size = max(8, int(radius * 2) + 4)
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        cx = cy = size // 2
        if style == "neon":
            pygame.draw.circle(surf, (12, 12, 14), (cx, cy), radius)
            pygame.draw.circle(surf, (28, 28, 32), (cx, cy), max(3, int(radius * 0.90)))
            rim_outer = max(4, int(radius * 0.78))
            rim_inner = max(3, int(radius * 0.64))
            pygame.draw.circle(surf, (255, 110, 28), (cx, cy), rim_outer)
            pygame.draw.circle(surf, (40, 40, 48), (cx, cy), rim_inner)
            pygame.draw.circle(surf, (22, 22, 26), (cx, cy), max(2, int(radius * 0.50)))
            spoke_color = (255, 150, 50)
            spokes = 5
            thick = max(2, radius // 6)
            for index in range(spokes):
                theta = angle + index * (2 * math.pi / spokes)
                inner = max(2, int(radius * 0.12))
                outer = int(radius * 0.62)
                x1 = cx + math.cos(theta) * inner
                y1 = cy + math.sin(theta) * inner
                x2 = cx + math.cos(theta) * outer
                y2 = cy + math.sin(theta) * outer
                pygame.draw.line(surf, spoke_color, (x1, y1), (x2, y2), thick)
            pygame.draw.circle(surf, (255, 140, 40), (cx, cy), max(3, int(radius * 0.20)))
            pygame.draw.circle(surf, (50, 50, 56), (cx, cy), max(1, int(radius * 0.08)))
            pygame.draw.circle(surf, (255, 120, 35), (cx, cy), radius, max(1, radius // 14))
        else:
            pygame.draw.circle(surf, (18, 18, 20), (cx, cy), radius)
            pygame.draw.circle(surf, (48, 48, 52), (cx, cy), max(3, int(radius * 0.88)))
            pygame.draw.circle(surf, (28, 28, 30), (cx, cy), max(2, int(radius * 0.55)))
            spoke_color = (210, 210, 220)
            for index in range(6):
                theta = angle + index * (math.pi / 3)
                inner = max(2, int(radius * 0.18))
                outer = int(radius * 0.82)
                x1 = cx + math.cos(theta) * inner
                y1 = cy + math.sin(theta) * inner
                x2 = cx + math.cos(theta) * outer
                y2 = cy + math.sin(theta) * outer
                pygame.draw.line(surf, spoke_color, (x1, y1), (x2, y2), max(1, radius // 7))
            pygame.draw.circle(surf, (190, 190, 196), (cx, cy), max(2, int(radius * 0.22)))
            pygame.draw.circle(surf, (90, 90, 96), (cx, cy), max(1, int(radius * 0.10)))
        self._sprite_cache[key] = surf
        return surf

    def _blit_wheel_spin(self, dest_rect, kind, angle):
        if dest_rect.width < 18 or dest_rect.height < 12:
            return
        wheels = []
        style = "race"
        if kind == "side":
            style = "neon"
            src = self.sprites.get(SPRITE_FILES["side"])
            if src is None:
                return
            sw, sh = src.get_size()
            for sx, sy, sr in SIDE_WHEEL_SRC:
                fx = sx / float(sw)
                fy = sy / float(sh)
                cx = dest_rect.x + fx * dest_rect.width
                cy = dest_rect.y + fy * dest_rect.height
                radius = max(5, int(round(sr * dest_rect.width / float(sw))))
                wheels.append((cx, cy, radius))
        else:
            rear_r = max(3, int(dest_rect.width * 0.12))
            front_r = max(2, int(dest_rect.width * 0.07))
            wheels = [
                (dest_rect.x + int(dest_rect.width * 0.20), dest_rect.y + int(dest_rect.height * 0.68), rear_r),
                (dest_rect.x + int(dest_rect.width * 0.80), dest_rect.y + int(dest_rect.height * 0.68), rear_r),
                (dest_rect.x + int(dest_rect.width * 0.27), dest_rect.y + int(dest_rect.height * 0.36), front_r),
                (dest_rect.x + int(dest_rect.width * 0.73), dest_rect.y + int(dest_rect.height * 0.36), front_r),
            ]
        for cx, cy, radius in wheels:
            wheel = self._make_wheel(radius, angle, style)
            ghost = self._make_wheel(radius, angle - 0.45, style)
            ghost.set_alpha(90)
            self.screen.blit(ghost, ghost.get_rect(center=(cx, cy)))
            self.screen.blit(wheel, wheel.get_rect(center=(cx, cy)))

    def _blit_camera_flash(self, origin_x, origin_y, cell_w, cell_h, cx, cy, intensity):
        pygame = self._pygame
        intensity = max(0.0, min(1.0, float(intensity)))
        if intensity <= 0.02:
            return
        px = origin_x + int(cx * cell_w)
        py = origin_y + int(cy * cell_h)
        radius = max(3, int(cell_w * (0.22 + 0.38 * intensity)))
        size = radius * 6
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        center = (size // 2, size // 2)
        pygame.draw.circle(surf, (255, 220, 140, int(70 * intensity)), center, radius * 2)
        pygame.draw.circle(surf, (255, 255, 220, int(160 * intensity)), center, radius)
        pygame.draw.circle(surf, (255, 255, 255, int(230 * intensity)), center, max(2, radius // 3))
        arm = int(radius * 1.6)
        thick = max(1, radius // 5)
        pygame.draw.line(surf, (255, 255, 255, int(180 * intensity)), (center[0] - arm, center[1]), (center[0] + arm, center[1]), thick)
        pygame.draw.line(surf, (255, 255, 255, int(180 * intensity)), (center[0], center[1] - arm), (center[0], center[1] + arm), thick)
        self.screen.blit(surf, surf.get_rect(center=(px, py)), special_flags=pygame.BLEND_ADD)

    def _blit_sprites(self, origin_x, origin_y, cell_w, cell_h):
        pygame = self._pygame
        for kind, cx, cy, scale, hue, grid_w, tint in SPRITE_OVERLAYS:
            if kind == "flash":
                self._blit_camera_flash(origin_x, origin_y, cell_w, cell_h, cx, cy, scale)
                continue
            if kind == "road":
                continue
            name = SPRITE_FILES.get(kind)
            image = self.sprites.get(name) if name else None
            if image is None:
                continue
            if kind == "skyline":
                dest_h = max(64, int(cy * cell_h * 0.82))
                dest_w = int(dest_h * image.get_width() / max(1, image.get_height()))
                sprite = self._scaled_sprite(name, dest_w, dest_h)
                if sprite is None:
                    continue
                content_w = int(grid_w * cell_w)
                foot = origin_y + int(cy * cell_h)
                prev_clip = self.screen.get_clip()
                self.screen.set_clip(pygame.Rect(origin_x, origin_y, content_w, max(1, foot - origin_y)))
                offset = int(cx * cell_w) % dest_w
                x = origin_x - offset
                while x < origin_x + content_w:
                    self.screen.blit(sprite, (x, foot - dest_h))
                    x += dest_w
                self.screen.set_clip(prev_clip)
                continue
            if kind == "side":
                dest_w = max(48, int(cell_w * SPRITE_CELL_WIDTH["side"] * max(0.4, scale)))
            elif kind == "rear":
                dest_w = max(12, int(cell_w * (3.2 + scale * 5.5) * 0.9))
            else:
                dest_w = max(16, int(cell_w * SPRITE_CELL_WIDTH.get(kind, 10.0) * max(0.4, scale)))
            dest_h = int(dest_w * image.get_height() / max(1, image.get_width()))
            if kind in ("tree", "tree_tall"):
                max_h = max(24, int(cell_h * 18))
                if dest_h > max_h:
                    dest_w = max(12, int(dest_w * max_h / dest_h))
                    dest_h = max_h
            elif kind.startswith("person"):
                max_h = max(24, int(cell_h * 18))
                if kind in CROWD_TALL:
                    dest_h = max(6, int(max_h * 0.10))
                elif kind in CROWD_SHORT:
                    dest_h = max(6, int(max_h * 0.07))
                else:
                    dest_h = max(6, int(max_h * 0.086))
                dest_w = max(4, int(dest_h * image.get_width() / max(1, image.get_height())))
            sprite = self._scaled_sprite(
                name, dest_w, dest_h, flip=False, hue=(hue if tint else None)
            )
            if sprite is None:
                continue
            y_bias = 1 if kind == "rear" else 0
            if grid_w == MIRROR_WIDTH:
                px = origin_x + int((WIDTH + MIRROR_GAP + 1 + cx) * cell_w)
                py = origin_y + int((2 + cy) * cell_h)
                foot = py + cell_h
            else:
                px = origin_x + int(cx * cell_w)
                py = origin_y + int((cy + y_bias) * cell_h)
                foot = py + cell_h if kind in ("side", "rear") else py
            rect = sprite.get_rect(midbottom=(px, foot))
            self.screen.blit(sprite, rect)
            if kind == "side":
                self._blit_wheel_spin(rect, kind, time.time() * 22.0)

    def stop(self):
        if self.active and self._pygame is not None:
            try:
                self._pygame.quit()
            except Exception:
                pass
        self.active = False
        if self._console_hwnd:
            user32.ShowWindow(self._console_hwnd, 5)
            user32.SetForegroundWindow(self._console_hwnd)


VIDEO = GameVideo()


class GameAudio:
    MUSIC_ALIAS = "racerbgm"

    def __init__(self):
        self.music_on = False
        self.music_enabled = False
        self._music_open = False
        self._looping = False
        self._music_path = MUSIC_FILE

    def mci(self, command):
        buf = ctypes.create_unicode_buffer(256)
        err = winmm.mciSendStringW(command, buf, 255, None)
        return err, buf.value

    def _write_tagless_mp3(self, src, dst):
        """MCI mpegvideo fails (error 277) on some MP3s with large ID3/album art."""
        with open(src, "rb") as handle:
            header = handle.read(10)
            skip = 0
            if len(header) == 10 and header.startswith(b"ID3"):
                skip = (
                    10
                    + ((header[6] & 0x7F) << 21)
                    + ((header[7] & 0x7F) << 14)
                    + ((header[8] & 0x7F) << 7)
                    + (header[9] & 0x7F)
                )
            handle.seek(skip)
            with open(dst, "wb") as out:
                shutil.copyfileobj(handle, out)

    def _open_and_play(self, path):
        self.mci(f"close {self.MUSIC_ALIAS}")
        err, _ = self.mci(f'open "{path}" type mpegvideo alias {self.MUSIC_ALIAS}')
        if err != 0:
            return False
        self._music_open = True
        self._music_path = path
        self.mci(f"setaudio {self.MUSIC_ALIAS} volume to 400")
        err, _ = self.mci(f"play {self.MUSIC_ALIAS} repeat")
        if err == 0:
            self.music_on = True
            self.music_enabled = True
            return True
        err, _ = self.mci(f"play {self.MUSIC_ALIAS}")
        if err != 0:
            self.mci(f"close {self.MUSIC_ALIAS}")
            self._music_open = False
            return False
        self.music_on = True
        self.music_enabled = True
        if not self._looping:
            self._looping = True
            threading.Thread(target=self._loop_music, daemon=True).start()
        return True

    def start(self):
        if not os.path.isfile(MUSIC_FILE):
            return
        if self._open_and_play(MUSIC_FILE):
            return
        stripped = os.path.join(tempfile.gettempdir(), "psyracer_bgm.mp3")
        try:
            self._write_tagless_mp3(MUSIC_FILE, stripped)
        except OSError:
            return
        self._open_and_play(stripped)

    def _loop_music(self):
        while self._looping:
            time.sleep(0.8)
            if not self.music_enabled:
                continue
            _, mode = self.mci(f"status {self.MUSIC_ALIAS} mode")
            if (mode or "").strip().lower() in ("stopped", ""):
                self.mci(f"play {self.MUSIC_ALIAS} from 0")

    def pause_music(self):
        if self._music_open:
            self.mci(f"pause {self.MUSIC_ALIAS}")
        self.music_enabled = False
        self.music_on = False

    def resume_music(self):
        if not self._music_open:
            self.start()
            return
        err, _ = self.mci(f"resume {self.MUSIC_ALIAS}")
        if err != 0:
            err, _ = self.mci(f"play {self.MUSIC_ALIAS} repeat")
            if err != 0:
                self.mci(f"play {self.MUSIC_ALIAS} from 0")
        self.music_enabled = True
        self.music_on = True

    def toggle_music(self):
        if self.music_enabled:
            self.pause_music()
        else:
            self.resume_music()

    def stop(self):
        self._looping = False
        self.music_on = False
        self.music_enabled = False
        self.mci(f"stop {self.MUSIC_ALIAS}")
        self.mci(f"close {self.MUSIC_ALIAS}")
        self._music_open = False


AUDIO = GameAudio()


def async_key_down(vk):
    try:
        return user32.GetAsyncKeyState(vk) < 0
    except Exception:
        return False


class GameKeys:
    TRACKED = (VK_W, VK_A, VK_S, VK_D, VK_UP, VK_DOWN, VK_LEFT, VK_RIGHT, VK_ESCAPE, VK_Q)

    def __init__(self):
        self._pressed = set()
        self._taps = set()
        self._got_key_up = False
        self._h_in = _handle_from_std(STD_INPUT_HANDLE)
        self._h_out = _handle_from_std(STD_OUTPUT_HANDLE)
        self._old_in = wintypes.DWORD()
        self._old_out = wintypes.DWORD()
        self._in_saved = False
        self._out_saved = False
        self._msvcrt = None
        try:
            import msvcrt as _msvcrt

            self._msvcrt = _msvcrt
        except ImportError:
            self._msvcrt = None

    def __enter__(self):
        if not VIDEO.active:
            try:
                if kernel32.GetConsoleMode(self._h_in, ctypes.byref(self._old_in)):
                    self._in_saved = True
                    kernel32.SetConsoleMode(self._h_in, ENABLE_EXTENDED_FLAGS | ENABLE_PROCESSED_INPUT)
                    kernel32.FlushConsoleInputBuffer(self._h_in)
                if kernel32.GetConsoleMode(self._h_out, ctypes.byref(self._old_out)):
                    self._out_saved = True
                    kernel32.SetConsoleMode(
                        self._h_out,
                        (self._old_out.value | ENABLE_PROCESSED_OUTPUT | ENABLE_VIRTUAL_TERMINAL_PROCESSING)
                        & ~ENABLE_WRAP_AT_EOL_OUTPUT,
                    )
            except Exception:
                self._in_saved = False
                self._out_saved = False
        console_write("\033[?25l\033[?7l\033[H")
        return self

    def __exit__(self, exc_type, exc, tb):
        console_write("\033[?25h")
        if self._in_saved:
            try:
                kernel32.FlushConsoleInputBuffer(self._h_in)
                kernel32.SetConsoleMode(self._h_in, self._old_in)
            except Exception:
                pass
        if self._out_saved:
            try:
                kernel32.SetConsoleMode(self._h_out, self._old_out)
            except Exception:
                pass
        self._pressed.clear()
        return False

    def pump(self):
        self._taps = set()
        VIDEO.pump()
        if VIDEO.active:
            return
        self._pump_console()
        self._pump_msvcrt()

    def down(self, vk):
        if VIDEO.closed and vk in (VK_ESCAPE, VK_Q):
            return True
        if VIDEO.key_down(vk):
            return True
        if async_key_down(vk):
            return True
        if vk in self._taps:
            return True
        return self._got_key_up and vk in self._pressed

    def _pump_console(self):
        if VIDEO.active:
            return
        count = wintypes.DWORD()
        try:
            if not kernel32.GetNumberOfConsoleInputEvents(self._h_in, ctypes.byref(count)):
                return
        except Exception:
            return
        if count.value == 0:
            return
        records = (INPUT_RECORD * count.value)()
        read = wintypes.DWORD()
        if not kernel32.ReadConsoleInputW(
            self._h_in, ctypes.byref(records), count.value, ctypes.byref(read)
        ):
            return
        for i in range(read.value):
            rec = records[i]
            if rec.EventType != KEY_EVENT:
                continue
            event = rec.Event.KeyEvent
            vk = event.wVirtualKeyCode
            if vk not in self.TRACKED:
                vk = _vk_from_char(event.UnicodeChar) or vk
            if vk not in self.TRACKED:
                continue
            if event.bKeyDown:
                self._pressed.add(vk)
                self._taps.add(vk)
            else:
                self._pressed.discard(vk)
                self._got_key_up = True

    def _pump_msvcrt(self):
        if VIDEO.active or self._msvcrt is None:
            return
        buf = bytearray()
        while self._msvcrt.kbhit():
            buf.extend(self._msvcrt.getch())
        for vk, is_down in parse_console_bytes(bytes(buf)):
            if is_down:
                self._taps.add(vk)


def _vk_from_char(char):
    if not char:
        return None
    lowered = char.lower()
    mapping = {"w": VK_W, "a": VK_A, "s": VK_S, "d": VK_D, "q": VK_Q}
    if lowered in mapping:
        return mapping[lowered]
    if char == "\x1b":
        return VK_ESCAPE
    return None


def parse_console_bytes(data):
    updates = []
    i = 0
    while i < len(data):
        b = data[i]
        if b in (0x00, 0xE0) and i + 1 < len(data):
            code = data[i + 1]
            i += 2
            arrows = {72: VK_UP, 80: VK_DOWN, 75: VK_LEFT, 77: VK_RIGHT}
            if code in arrows:
                updates.append((arrows[code], True))
            continue
        if b == 0x1B:
            if i + 2 < len(data) and data[i + 1] == 0x5B:
                final = data[i + 2]
                i += 3
                arrows = {65: VK_UP, 66: VK_DOWN, 67: VK_RIGHT, 68: VK_LEFT}
                if final in arrows:
                    updates.append((arrows[final], True))
                continue
            updates.append((VK_ESCAPE, True))
            i += 1
            continue
        try:
            char = bytes([b]).decode("ascii")
        except UnicodeDecodeError:
            i += 1
            continue
        vk = _vk_from_char(char)
        if vk is not None:
            updates.append((vk, True))
        i += 1
    return updates


def enable_color_output():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    handle = _handle_from_std(STD_OUTPUT_HANDLE)
    mode = wintypes.DWORD()
    if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
        kernel32.SetConsoleMode(
            handle,
            (mode.value | ENABLE_PROCESSED_OUTPUT | ENABLE_VIRTUAL_TERMINAL_PROCESSING)
            & ~ENABLE_WRAP_AT_EOL_OUTPUT,
        )
    in_handle = _handle_from_std(STD_INPUT_HANDLE)
    in_mode = wintypes.DWORD()
    if kernel32.GetConsoleMode(in_handle, ctypes.byref(in_mode)):
        kernel32.SetConsoleMode(in_handle, ENABLE_EXTENDED_FLAGS | ENABLE_PROCESSED_INPUT)
    VIDEO.start()


def hsv_rgb(hue, saturation=1.0, value=1.0):
    hue = hue % 360
    chroma = value * saturation
    x = chroma * (1 - abs((hue / 60.0) % 2 - 1))
    m = value - chroma
    if hue < 60:
        red, green, blue = chroma, x, 0
    elif hue < 120:
        red, green, blue = x, chroma, 0
    elif hue < 180:
        red, green, blue = 0, chroma, x
    elif hue < 240:
        red, green, blue = 0, x, chroma
    elif hue < 300:
        red, green, blue = x, 0, chroma
    else:
        red, green, blue = chroma, 0, x
    return int((red + m) * 255), int((green + m) * 255), int((blue + m) * 255)


def fg(red, green, blue):
    return f"\033[38;2;{red};{green};{blue}m"


def rgb_text(text, hue, saturation=1.0, value=1.0):
    red, green, blue = hsv_rgb(hue, saturation, value)
    return f"{fg(red, green, blue)}{text}{RESET}"


def rainbow_text(text, offset=0, step=16):
    parts = []
    for index, char in enumerate(text):
        if char == " ":
            parts.append(char)
            continue
        red, green, blue = hsv_rgb(offset + index * step)
        parts.append(f"{fg(red, green, blue)}{char}")
    return "".join(parts) + RESET


_last_win = (0, 0)


def draw_frame(text):
    if VIDEO.active:
        VIDEO.present(text)
        return
    global _last_win
    cols, rows = get_window_size()
    if (cols, rows) != _last_win:
        apply_layout(cols, rows)
        _last_win = (cols, rows)
    lines = text.split("\n")
    parts = ["\033[?7l"]
    for index in range(rows):
        parts.append(f"\033[{index + 1};1H")
        if index < len(lines):
            line = lines[index]
            if line.endswith("\033[K"):
                line = line[:-3]
            parts.append(line)
        parts.append("\033[K")
    console_write("".join(parts))


def read_menu_key():
    if VIDEO.active:
        return VIDEO.pop_key()
    try:
        import msvcrt
    except ImportError:
        return None
    if not msvcrt.kbhit():
        return None
    char = msvcrt.getch()
    if char in (b"\x00", b"\xe0"):
        if msvcrt.kbhit():
            code = msvcrt.getch()
            if code == b"H":
                return "up"
            if code == b"P":
                return "down"
            if code == b"K":
                return "left"
            if code == b"M":
                return "right"
        return None
    if char in (b"\r", b"\n"):
        return "enter"
    if char in (b"\x08", b"\x7f"):
        return "backspace"
    if char == b"\x1b":
        if msvcrt.kbhit():
            nxt = msvcrt.getch()
            if nxt == b"[" and msvcrt.kbhit():
                final = msvcrt.getch()
                return {"A": "up", "B": "down", "C": "right", "D": "left"}.get(final.decode("ascii", "ignore"))
            return None
        return "esc"
    try:
        return char.decode("ascii").lower()
    except UnicodeDecodeError:
        return None


def wait_for_menu_choice(render, valid):
    apply_layout()
    console_write("\033[?25l")
    hue = 0
    try:
        while True:
            draw_frame(render(hue))
            key = read_menu_key()
            if key is not None and key in valid:
                return key
            hue = (hue + 7) % 360
            time.sleep(1 / 18)
    finally:
        console_write("\033[?25h")


def wait_for_menu_select(option_count, render, start=0):
    apply_layout()
    console_write("\033[?25l")
    if VIDEO.active:
        VIDEO.flush_keys()
    selected = start % option_count if option_count else 0
    hue = 0
    ignore_enter_until = time.time() + 0.3
    try:
        while True:
            draw_frame(render(hue, selected))
            key = read_menu_key()
            if key == "up":
                selected = (selected - 1) % option_count
            elif key == "down":
                selected = (selected + 1) % option_count
            elif key == "enter":
                if time.time() < ignore_enter_until:
                    continue
                return selected
            elif key is not None and key.isdigit():
                number = int(key)
                if 1 <= number <= option_count:
                    return number - 1
            elif key in ("esc", "q"):
                return None
            hue = (hue + 7) % 360
            time.sleep(1 / 18)
    finally:
        console_write("\033[?25h")


def fit_text(text, width):
    text = text.replace("\n", " ").replace("\t", " ")
    if len(text) <= width:
        return text
    return text[: width - 1].rstrip() + "."


def menu_rule(hue):
    return rgb_text("+" + ("-" * MENU_INNER) + "+", hue, value=0.7) + "\033[K"


def menu_row(text, hue, align="left", rainbow=False, value=1.0):
    body = fit_text(text, MENU_INNER)
    if align == "center":
        body = body.strip().center(MENU_INNER)
    else:
        body = body.ljust(MENU_INNER)
    body = body[:MENU_INNER]
    inner = rainbow_text(body, offset=hue, step=14) if rainbow else rgb_text(body, hue, value=value)
    edge = rgb_text("|", hue, value=0.7)
    return f"{edge}{inner}{edge}\033[K"


def boxed_menu(hue, rows, selected=None):
    lines = []
    option_index = 0
    for kind, text in rows:
        if kind == "rule":
            lines.append(menu_rule(hue + 50))
        elif kind == "blank":
            lines.append(menu_row("", hue + 50, value=0.7))
        elif kind == "title":
            lines.append(menu_row(text, hue, align="center", rainbow=True))
        elif kind == "center":
            lines.append(menu_row(text, hue + 170, align="center", value=0.9))
        elif kind == "option":
            label = text.strip()
            if selected is not None and option_index == selected:
                lines.append(menu_row(f" > {label}", hue + option_index * 42, value=1.0))
            else:
                dim = 0.55 if selected is not None else 1.0
                lines.append(menu_row(f"   {label}", hue + option_index * 42, value=dim))
            option_index += 1
        elif kind == "hint":
            lines.append(menu_row(text, hue + 110, align="center", rainbow=True))
        else:
            lines.append(menu_row(text, hue + 220, value=0.82))
    pad = max(0, (WIDTH - (MENU_INNER + 2)) // 2)
    prefix = " " * pad
    return "\n".join(prefix + line for line in lines)


INITIAL_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ "
HIGH_SCORE_LIMIT = 10
INITIALS_LEN = 3


def normalize_name(text):
    cleaned = "".join(ch for ch in str(text).upper() if ch in INITIAL_CHARS)
    return (cleaned + "   ")[:INITIALS_LEN]


def score_sort_key(item):
    place, distance, _level, _name = item
    return (place, -int(distance))


def parse_score_line(line):
    parts = [part.strip() for part in line.split(",")]
    if len(parts) >= 4:
        return int(parts[0]), int(parts[1]), parts[2].lower(), normalize_name(parts[3])
    if len(parts) == 3:
        if parts[0].isdigit() and parts[1].isdigit() and 1 <= int(parts[0]) <= 6:
            return int(parts[0]), int(parts[1]), parts[2].lower(), "---"
        return 6, int(parts[0]), parts[1].lower(), normalize_name(parts[2])
    if len(parts) == 2:
        return 6, int(parts[0]), parts[1].lower(), "---"
    raise ValueError("bad score line")


def load_high_scores():
    scores = []
    if os.path.isfile(HIGH_SCORES_FILE):
        try:
            with open(HIGH_SCORES_FILE, "r", encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    scores.append(parse_score_line(line))
        except (OSError, ValueError):
            scores = []
    scores.sort(key=score_sort_key)
    return scores[:HIGH_SCORE_LIMIT]


def is_high_score(place, distance):
    scores = load_high_scores()
    if len(scores) < HIGH_SCORE_LIMIT:
        return True
    worst = scores[-1]
    return score_sort_key((int(place), int(distance), "", "")) < score_sort_key(worst)


def save_high_score(place, distance, difficulty, name):
    scores = load_high_scores()
    scores.append((int(place), int(distance), difficulty, normalize_name(name)))
    scores.sort(key=score_sort_key)
    scores = scores[:HIGH_SCORE_LIMIT]
    with open(HIGH_SCORES_FILE, "w", encoding="utf-8") as handle:
        for item_place, dist, level, item_name in scores:
            handle.write(f"{item_place},{dist},{level},{item_name.rstrip()}\n")


def road_curve(distance):
    return (
        math.sin(distance * 0.011) * 0.55
        + math.sin(distance * 0.027) * 0.28
        + math.sin(distance * 0.003) * 0.18
    )


def clamp(value, low, high):
    return max(low, min(high, value))


class Racer:
    def __init__(self, z, x, hue, target_speed, number, name):
        self.z = z
        self.x = x
        self.lane = x
        self.hue = hue
        self.speed = 0.0
        self.target_speed = target_speed
        self.number = number
        self.name = name


def make_field(settings):
    field = []
    for spec in AI_FIELD:
        target = settings["max_speed"] * settings["ai_speed"] * spec["pace"]
        field.append(Racer(spec["z"], spec["x"], spec["hue"], target, spec["number"], spec["name"]))
    return field


def project_row(y, distance, player_x, width, height, horizon, reverse=False):
    t = (y - horizon) / max(1, height - 1 - horizon)
    t = max(0.02, min(1.0, t))
    look_ahead = (1.0 - t) * 70
    curve_at = distance - look_ahead if reverse else distance + look_ahead
    bend_scale = 22.0 * width / 79.0
    bend = road_curve(curve_at) * ((1.0 - t) ** 2) * bend_scale
    half = (2.2 + t * 26.0) * (width / 79.0)
    center = width / 2 - player_x * half + bend
    return t, center, half


def world_project(rel_z, x_lane, distance, player_x, width, height, horizon, reverse=False):
    if rel_z < 1.2 or rel_z > 88:
        return None
    place = clamp(13.0 / rel_z, 0.04, 1.15)
    scale = clamp(22.0 / rel_z, 0.04, 2.4)
    y = int(horizon + place * (height - 1 - horizon))
    y = clamp(y, horizon, height - 2)
    _, center, half = project_row(y, distance, player_x, width, height, horizon, reverse)
    return scale, center + x_lane * half, y


def paint_cell(char, hue, value=1.0, saturation=0.85):
    if char == " ":
        return " "
    return rgb_text(char, hue, saturation=saturation, value=value)


def blit_sprite(grid, colors, cx, bottom_y, lines, hue, value=1.0):
    height = len(grid)
    width = len(grid[0]) if height else 0
    start_y = int(bottom_y) - len(lines) + 1
    sprite_w = max(len(line) for line in lines)
    left = int(cx - sprite_w / 2)
    for row_i, line in enumerate(lines):
        gy = start_y + row_i
        if gy < 0 or gy >= height:
            continue
        pad = line.ljust(sprite_w)
        for i, char in enumerate(pad):
            gx = left + i
            if 0 <= gx < width and char != " ":
                grid[gy][gx] = char
                colors[gy][gx] = (hue, value)


def indy_sprite(scale, number=None):
    mark = "█"
    if number is None:
        nose = "█"
    elif number < 10:
        nose = str(number)
    else:
        nose = str(number)[-1]
    if scale < 0.22:
        return ["▲"]
    if scale < 0.40:
        return ["▲", "o"]
    if scale < 0.62:
        return [" /\\ ", f"o{nose}{nose}o"]
    if scale < 0.90:
        return ["  /\\  ", f" /{nose}{nose}\\ ", f"o|{mark}{mark}|o"]
    if scale < 1.30:
        return [
            "   /\\   ",
            f"  /{nose}{nose}\\  ",
            f" /{mark}{mark}{mark}{mark}\\ ",
            f"o|{mark}{mark}{mark}{mark}|o",
        ]
    if scale < 1.80:
        return [
            "    /\\    ",
            f"   /{nose}{nose}\\   ",
            f"  /{mark}{mark}{mark}{mark}\\  ",
            f" /|{mark}{mark}{mark}{mark}|\\ ",
            f"o|{mark}{mark}{mark}{mark}{mark}{mark}|o",
            " ''      '' ",
        ]
    return [
        "      /\\      ",
        f"     /{nose}{nose}\\     ",
        f"    /{mark}{mark}{mark}{mark}\\    ",
        f"   /|{mark}  {mark}|\\   ",
        f"  / |{mark}{mark}{mark}{mark}| \\  ",
        f" /  |{mark}{mark}{mark}{mark}|  \\ ",
        f"o|{mark}{mark}{mark}{mark}{mark}{mark}{mark}{mark}|o",
        "  ''        ''  ",
    ]


def draw_tree(grid, colors, cx, cy, scale):
    if scale < 0.30:
        blit_sprite(grid, colors, cx, cy, ["*"], 125, 0.8)
        return
    if scale < 0.55:
        blit_sprite(grid, colors, cx, cy, ["^", "|"], 125)
        return
    if scale < 1.00:
        blit_sprite(grid, colors, cx, cy, [" ### ", "#####", "  |  "], 125)
        blit_sprite(grid, colors, cx, cy, ["     ", "     ", "  |  "], 30, 0.7)
        return
    if scale < 1.60:
        blit_sprite(grid, colors, cx, cy, ["  ###  ", " ##### ", "#######", "   |   ", "   |   "], 125)
        blit_sprite(grid, colors, cx, cy, ["       ", "       ", "       ", "   |   ", "   |   "], 30, 0.7)
        return
    blit_sprite(
        grid,
        colors,
        cx,
        cy,
        ["   ###   ", "  #####  ", " ####### ", "#########", "    |    ", "    |    ", "    |    "],
        125,
    )
    blit_sprite(
        grid,
        colors,
        cx,
        cy,
        ["         ", "         ", "         ", "         ", "    |    ", "    |    ", "    |    "],
        30,
        0.7,
    )


def draw_building(grid, colors, cx, cy, scale, hue):
    if scale < 0.35:
        blit_sprite(grid, colors, cx, cy, ["█"], hue, 0.7)
        return
    if scale < 0.70:
        blit_sprite(grid, colors, cx, cy, ["▄█▄", "█▄█"], hue, 0.8)
        return
    if scale < 1.20:
        blit_sprite(grid, colors, cx, cy, ["▄████▄", "█ ▄▄ █", "█▄▄▄▄█"], hue, 0.85)
        return
    blit_sprite(
        grid,
        colors,
        cx,
        cy,
        ["▄██████▄", "█ ▄  ▄ █", "█ ▄  ▄ █", "█▄▄▄▄▄▄█", "████████"],
        hue,
        0.85,
    )


def draw_person(grid, colors, cx, cy, scale, hue):
    if scale < 0.40:
        blit_sprite(grid, colors, cx, cy, ["o"], hue)
        return
    if scale < 0.80:
        blit_sprite(grid, colors, cx, cy, ["o", "|"], hue)
        return
    if scale < 1.30:
        pose = random.Random(int(cx) * 13 + int(cy)).choice(
            [[" o ", "/|\\", " | "], [" o ", "/| ", " | "], [" o ", " |\\", " | "]]
        )
        blit_sprite(grid, colors, cx, cy, pose, hue)
        return
    pose = random.Random(int(cx) * 13 + int(cy)).choice(
        [[" o ", "/|\\", " | ", "/ \\"], [" o ", "/| ", " | ", "/ \\"], [" o ", " |\\", " | ", "/ \\"]]
    )
    blit_sprite(grid, colors, cx, cy, pose, hue)


def draw_scenery(grid, colors, distance, player_x, finish_distance, width, height, horizon, reverse=False):
    if reverse:
        start = int(distance) - 82
        end = int(distance) - 4
    else:
        start = int(distance) + 6
        end = int(distance) + 82
    z = start - (start % 4)
    props = []
    while z < end:
        rel = (distance - z) if reverse else (z - distance)
        if (z * 3) % 5 != 1:
            side = -1 if (z // 4) % 2 == 0 else 1
            props.append((rel, "tree", side * 1.42))
        if z % 16 == 0:
            side = -1 if (z // 16) % 2 == 0 else 1
            props.append((rel, "building", side * 1.95))
        near_finish = finish_distance - 90 < z <= finish_distance + 8
        if near_finish and z % 3 == 0:
            props.append((rel, "crowd", -1.35))
            props.append((rel, "crowd", 1.35))
            props.append((rel, "crowd", -1.7))
            props.append((rel, "crowd", 1.7))
        z += 4
    props.sort(key=lambda item: -item[0])
    for rel, kind, x_lane in props:
        projected = world_project(rel, x_lane, distance, player_x, width, height, horizon, reverse)
        if projected is None:
            continue
        scale, cx, cy = projected
        if kind == "tree":
            draw_tree(grid, colors, cx, cy, scale)
        elif kind == "building":
            draw_building(grid, colors, cx, cy, scale, 200 + int(rel * 3) % 80)
        else:
            draw_person(grid, colors, cx, cy, scale, 20 + int(cx * 7) % 40)


def draw_finish_banner(grid, colors, distance, player_x, finish_distance, width, height, horizon, reverse=False):
    rel = (distance - finish_distance) if reverse else (finish_distance - distance)
    projected = world_project(max(rel, 1.4), 0.0, distance, player_x, width, height, horizon, reverse)
    if projected is None:
        return
    scale, cx, cy = projected
    _, center, half = project_row(cy, distance, player_x, width, height, horizon, reverse)
    left = int(center - half)
    right = int(center + half)
    if 0 <= cy < height:
        for x in range(max(0, left), min(width, right + 1)):
            check = ((x + int(distance)) // 2) % 2 == 0
            grid[cy][x] = "#" if check else " "
            colors[cy][x] = (0 if check else 50, 1.0)
        if cy - 1 >= 0:
            label = " FINISH "
            start = max(0, int(center - len(label) / 2))
            for i, char in enumerate(label):
                x = start + i
                if 0 <= x < width:
                    grid[cy - 1][x] = char
                    colors[cy - 1][x] = (50, 1.0)
    posts = [center - half, center + half]
    for post in posts:
        px = int(post)
        post_h = 3 + int(scale * 4)
        for i in range(post_h):
            gy = cy - i
            if 0 <= gy < height and 0 <= px < width:
                grid[gy][px] = "║"
                colors[gy][px] = (40, 1.0)


def draw_start_lights(grid, colors, stage, label):
    """stage 0=off, 1-3 red lamps on from top, 4=green."""
    width = len(grid[0]) if grid else 0
    height = len(grid)
    cx = width // 2
    top = 2
    box = [
        "┌─────┐",
        "│     │",
        "├─────┤",
        "│     │",
        "├─────┤",
        "│     │",
        "└─────┘",
    ]
    blit_sprite(grid, colors, cx, top + len(box) - 1, box, 220, 0.9)
    lamp_rows = [top + 1, top + 3, top + 5]
    for index, gy in enumerate(lamp_rows):
        if not (0 <= gy < height):
            continue
        if stage == 4:
            lamp, hue, value = "●", 120, 1.0
        elif index < stage:
            lamp, hue, value = "●", 0, 1.0
        else:
            lamp, hue, value = "○", 0, 0.25
        gx = cx
        if 0 <= gx < width:
            grid[gy][gx] = lamp
            colors[gy][gx] = (hue, value)
    if label:
        text = f" {label} "
        start = cx - len(text) // 2
        gy = top + len(box)
        if 0 <= gy < height:
            for i, char in enumerate(text):
                gx = start + i
                if 0 <= gx < width:
                    grid[gy][gx] = char
                    colors[gy][gx] = (50 if stage == 4 else 0, 1.0)


def draw_car_sprite(grid, colors, cx, cy, scale, hue, number=None):
    grid_w = len(grid[0]) if grid else WIDTH
    SPRITE_OVERLAYS.append(("rear", cx, cy, scale, hue, grid_w, True))
    if not VIDEO.active:
        body = indy_sprite(scale, number)
        blit_sprite(grid, colors, cx, cy, body, hue)


def draw_player_car(grid, colors, hue, crashed):
    height = len(grid)
    width = len(grid[0]) if height else 0
    car_hue = 0 if crashed else hue
    SPRITE_OVERLAYS.append(("rear", width / 2, height - 3, 2.2, car_hue, width, crashed))
    if not VIDEO.active:
        sprite = indy_sprite(2.2, None)
        blit_sprite(grid, colors, width / 2, height - 3, sprite, car_hue)


def race_position(distance, cars):
    ahead = sum(1 for car in cars if car.z > distance)
    return ahead + 1, len(cars) + 1


def fill_world(
    grid,
    colors,
    distance,
    player_x,
    cars,
    hue,
    crashed,
    finish_distance,
    reverse=False,
    draw_player=True,
    lights_stage=0,
    countdown_text="",
    horizon=None,
):
    height = len(grid)
    width = len(grid[0]) if height else 0
    if horizon is None:
        horizon = max(2, int(round(HORIZON * height / float(HEIGHT))))

    for y in range(horizon):
        sky_v = 0.18 + 0.55 * (1 - y / max(1, horizon))
        for x in range(width):
            grid[y][x] = "·" if (x + y + int(distance / 8)) % 17 == 0 else " "
            colors[y][x] = (hue + 210 + y * 6, sky_v)

    edge_w = 2 if width >= 100 else 1
    center_w = 1 if width >= 100 else 0
    for y in range(horizon, height):
        t, center, half = project_row(y, distance, player_x, width, height, horizon, reverse)
        left_edge = int(center - half)
        right_edge = int(center + half)
        stripe = int(distance * 0.35 + (1 - t) * 18)
        rumble = stripe % 2 == 0
        grass_hue = hue + 110 if rumble else hue + 130
        road_hue = hue + 280
        for x in range(width):
            if x < left_edge - edge_w or x > right_edge + edge_w:
                grid[y][x] = "." if rumble else " "
                colors[y][x] = (grass_hue, 0.35 + 0.25 * t)
            elif x <= left_edge or x >= right_edge:
                grid[y][x] = "#"
                colors[y][x] = (0 if rumble else 40, 0.9)
            else:
                center_mark = abs(x - int(center)) <= center_w and stripe % 4 < 2 and t > 0.2
                grid[y][x] = ":" if center_mark else " "
                colors[y][x] = (road_hue, 0.25 + 0.5 * t)

    draw_scenery(grid, colors, distance, player_x, finish_distance, width, height, horizon, reverse)
    finish_rel = (distance - finish_distance) if reverse else (finish_distance - distance)
    if -5 < finish_rel < 85:
        draw_finish_banner(
            grid, colors, distance, player_x, finish_distance, width, height, horizon, reverse
        )

    cars_draw = sorted(
        cars, key=lambda car: -((distance - car.z) if reverse else (car.z - distance))
    )
    for car in cars_draw:
        rel = (distance - car.z) if reverse else (car.z - distance)
        if rel < 2.2 or rel > 78:
            continue
        projected = world_project(rel, car.x, distance, player_x, width, height, horizon, reverse)
        if projected is None:
            continue
        scale, cx, cy = projected
        draw_car_sprite(grid, colors, cx, cy, scale, car.hue, car.number)

    if draw_player:
        draw_player_car(grid, colors, hue + 20, crashed)
    if lights_stage and not reverse:
        draw_start_lights(grid, colors, lights_stage, countdown_text)


def colorize_row(grid_row, color_row):
    parts = []
    for x, char in enumerate(grid_row):
        info = color_row[x]
        if info is None:
            parts.append(char)
        else:
            parts.append(paint_cell(char, info[0], value=info[1]))
    return "".join(parts)


def render_mirror_panel(distance, player_x, cars, hue, finish_distance):
    grid = [[" " for _ in range(MIRROR_WIDTH)] for _ in range(MIRROR_HEIGHT)]
    colors = [[None] * MIRROR_WIDTH for _ in range(MIRROR_HEIGHT)]
    fill_world(
        grid,
        colors,
        distance,
        player_x,
        cars,
        hue,
        False,
        finish_distance,
        reverse=True,
        draw_player=False,
        horizon=MIRROR_HORIZON,
    )
    for y in range(MIRROR_HEIGHT):
        for x in range(MIRROR_WIDTH):
            info = colors[y][x]
            if info is None:
                colors[y][x] = (200, 0.16)
                if grid[y][x] == " ":
                    grid[y][x] = "░"
            else:
                cell_hue, value = info
                colors[y][x] = (cell_hue + 18, max(0.12, value * 0.72))

    frame_hue = 210
    label = " REAR VIEW "
    left = max(0, (MIRROR_WIDTH - len(label)) // 2)
    right = max(0, MIRROR_WIDTH - len(label) - left)
    top = "┌" + ("─" * left) + label + ("─" * right) + "┐"
    bot = "└" + ("─" * MIRROR_WIDTH) + "┘"
    rows = [None] * HEIGHT
    box_top = 1
    rows[box_top] = rgb_text(top[:MIRROR_BOX_W], frame_hue, value=0.85)
    for i in range(MIRROR_HEIGHT):
        gy = box_top + 1 + i
        if gy >= HEIGHT:
            break
        inner = colorize_row(grid[i], colors[i])
        edge = rgb_text("│", frame_hue, value=0.85)
        rows[gy] = f"{edge}{inner}{edge}"
    bot_y = box_top + 1 + MIRROR_HEIGHT
    if bot_y < HEIGHT:
        rows[bot_y] = rgb_text(bot[:MIRROR_BOX_W], frame_hue, value=0.85)
    blank = " " * MIRROR_BOX_W
    return [row if row is not None else blank for row in rows]


def draw_scene(
    distance,
    player_x,
    speed,
    cars,
    hue,
    crashed,
    finished,
    difficulty,
    finish_distance,
    lights_stage=0,
    countdown_text="",
):
    SPRITE_OVERLAYS.clear()
    grid = [[" " for _ in range(WIDTH)] for _ in range(HEIGHT)]
    colors = [[None] * WIDTH for _ in range(HEIGHT)]
    fill_world(
        grid,
        colors,
        distance,
        player_x,
        cars,
        hue,
        crashed,
        finish_distance,
        reverse=False,
        draw_player=True,
        lights_stage=lights_stage,
        countdown_text=countdown_text,
        horizon=HORIZON,
    )
    mirror_rows = render_mirror_panel(distance, player_x, cars, hue, finish_distance)

    pos, field = race_position(distance, cars)
    hud_speed = int(speed * 180)
    hud_dist = int(distance)
    status = "CRASH" if crashed else ("FINISH" if finished else difficulty.upper())
    header = (
        f" {GAME_TITLE}  P{pos}/{field}  SPEED {hud_speed:3d}  "
        f"{hud_dist:5d}/{int(finish_distance)}m  {status} "
    )
    header = header[:FRAME_WIDTH].ljust(FRAME_WIDTH)

    gap = " " * MIRROR_GAP
    lines = [rainbow_text(header, offset=hue, step=8) + "\033[K"]
    for y in range(HEIGHT):
        main = colorize_row(grid[y], colors[y])
        lines.append(main + gap + mirror_rows[y] + "\033[K")
    help_line = "  W/Up gas   S/Down brake   A/D or Arrows steer   Esc quit "
    lines.append(rgb_text(help_line.ljust(FRAME_WIDTH), hue + 90, value=0.8) + "\033[K")
    return "\n".join(lines)


def pulse_beep(freq, duration_ms=160):
    def _run():
        try:
            import winsound

            winsound.Beep(freq, duration_ms)
        except Exception:
            pass

    threading.Thread(target=_run, daemon=True).start()


def update_ai(cars, settings, racing):
    if not racing:
        return
    for car in cars:
        if car.speed < car.target_speed:
            car.speed += settings["accel"] * random.uniform(0.55, 1.05)
        else:
            car.speed -= 0.004
        car.speed = clamp(car.speed, 0.0, car.target_speed)
        car.x += (car.lane - car.x) * 0.08
        car.x += math.sin(car.z * 0.04 + car.number) * 0.004
        car.x = clamp(car.x, -0.82, 0.82)
        car.z += car.speed * 6.5


def play_race(difficulty):
    apply_layout()
    settings = DIFFICULTY[difficulty]
    finish_distance = settings["finish"]
    distance = 0.0
    player_x = 0.0
    speed = 0.0
    cars = make_field(settings)
    crashed = False
    crash_timer = 0
    overlapping = set()
    finished = False
    racing = False
    hue = 0
    countdown_started = time.time()
    last_stage = 0

    with GameKeys() as keys:
        while True:
            keys.pump()
            if keys.down(VK_ESCAPE) or keys.down(VK_Q):
                return int(distance), False, race_position(distance, cars)[0]

            elapsed = time.time() - countdown_started
            if elapsed < 0.9:
                stage, label = 0, "READY"
            elif elapsed < 1.8:
                stage, label = 1, "3"
            elif elapsed < 2.7:
                stage, label = 2, "2"
            elif elapsed < 3.6:
                stage, label = 3, "1"
            elif elapsed < 4.4:
                stage, label = 4, "GO!"
                racing = True
            else:
                stage, label = 0, ""
                racing = True

            if stage != last_stage:
                if stage in (1, 2, 3):
                    pulse_beep(420, 140)
                elif stage == 4:
                    pulse_beep(880, 260)
                last_stage = stage

            steer = 0.0
            if racing:
                if keys.down(VK_LEFT) or keys.down(VK_A):
                    steer -= 1.0
                if keys.down(VK_RIGHT) or keys.down(VK_D):
                    steer += 1.0
                if keys.down(VK_UP) or keys.down(VK_W):
                    speed += settings["accel"]
                if keys.down(VK_DOWN) or keys.down(VK_S):
                    speed -= settings["accel"] * 1.4
                speed -= 0.006
            else:
                speed = 0.0

            if crash_timer:
                crash_timer -= 1
                if crash_timer <= 0:
                    crashed = False
            speed = clamp(speed, 0.0, settings["max_speed"])

            if racing:
                curve = road_curve(distance + 8)
                player_x += steer * (0.045 + speed * 0.03)
                player_x += curve * speed * 0.018
                offroad = abs(player_x) > 0.92
                if offroad:
                    speed *= 0.94
                    player_x = clamp(player_x, -1.15, 1.15)
                else:
                    player_x = clamp(player_x, -1.08, 1.08)
                distance += speed * 6.5
                update_ai(cars, settings, True)

            if racing and not finished:
                current_hits = set()
                for car in cars:
                    rel = car.z - distance
                    if 2.0 < rel < 7.5 and abs(car.x - player_x) < 0.28:
                        current_hits.add(car.number)
                        if car.number not in overlapping:
                            speed = settings["max_speed"] * 0.5
                            car.speed = car.target_speed * 0.5
                            crashed = True
                            crash_timer = 8
                overlapping = current_hits

            if distance >= finish_distance:
                finished = True
                speed *= 0.9
                if speed < 0.08:
                    draw_frame(
                        draw_scene(
                            distance,
                            player_x,
                            speed,
                            cars,
                            hue,
                            crashed,
                            True,
                            difficulty,
                            finish_distance,
                        )
                    )
                    time.sleep(0.8)
                    return int(distance), True, race_position(distance, cars)[0]

            draw_frame(
                draw_scene(
                    distance,
                    player_x,
                    speed,
                    cars,
                    hue,
                    crashed,
                    finished,
                    difficulty,
                    finish_distance,
                    lights_stage=stage,
                    countdown_text=label,
                )
            )
            hue = (hue + 6) % 360
            time.sleep(1 / FPS)


def splash_blit(grid, colors, x, y, art, hue, value=1.0):
    for row_i, line in enumerate(art):
        gy = y + row_i
        if gy < 0 or gy >= HEIGHT:
            continue
        for i, char in enumerate(line):
            gx = x + i
            if 0 <= gx < WIDTH and char != " ":
                grid[gy][gx] = char
                colors[gy][gx] = (hue, value)


def splash_put(grid, colors, x, y, char, hue, value):
    if 0 <= x < WIDTH and 0 <= y < HEIGHT and char != " ":
        grid[y][x] = char
        colors[y][x] = (hue, value)


def loop_x(spacing, phase, speed, tick, extra=12):
    start = -extra + int(-(tick * speed + phase) % spacing)
    x = start
    while x < WIDTH + extra:
        yield x
        x += spacing


def f1_side_car(wheel_frame):
    wheels = ["(O)", "(0)", "(o)", "(0)"]
    wheel = wheels[wheel_frame % 4]
    body = [
        r"                   ____                    ",
        r"           _______//_\\_______             ",
        r"          /  __  //////  __    \           ",
        r"         /  __  ///////  __     \          ",
        "        /  " + wheel + "|========|" + wheel + r"    \        ",
        r"        \___/                  \___/       ",
    ]
    width = max(len(line) for line in body)
    return [line.ljust(width) for line in body]


def _splash_sprites_ready():
    if not VIDEO.active:
        return False
    if not all(VIDEO.sprites.get(name) for name in SCENERY_SPRITES):
        return False
    return any(VIDEO.sprites.get(SPRITE_FILES.get(kind)) for kind in CROWD_KINDS)


def _draw_matrix_rain(grid, colors, tick, hue, cols, road_top):
    RAIN_CELLS.clear()
    glyphs = RAIN_GLYPHS
    glyph_count = len(glyphs)
    video = VIDEO.active
    for x in range(cols):
        seed = (x * 1103515245 + 12345) & 0x7FFFFFFF
        if seed % 5 == 0:
            continue
        speed = 9.0 + (seed % 17)
        trail = 10 + (seed % 12)
        offset = seed % 131
        streams = 1 + (1 if seed % 7 == 0 else 0)
        for stream in range(streams):
            cycle = road_top + trail
            head = int(tick * speed + offset + stream * (cycle * 0.55)) % cycle
            for i in range(trail):
                y = head - i
                if y < 0 or y >= road_top:
                    continue
                fade = 1.0 - (i / trail)
                if fade < 0.1:
                    continue
                glyph = glyphs[(x * 13 + y * 7 + int(tick * 14) + stream * 3) % glyph_count]
                rain_hue = (hue + tick * 90 + x * 6 - i * 10) % 360
                value = 1.0 if i == 0 else 0.22 + 0.78 * fade
                sat = 0.35 if i == 0 else 0.9
                if video:
                    if y >= 3:
                        RAIN_CELLS.append((x, y, glyph, hsv_rgb(rain_hue, sat, value)))
                else:
                    grid[y][x] = glyph
                    colors[y][x] = (rain_hue, value, sat)


def _queue_splash_scenery(tick, cols, rows, road_top):
    rng = random.Random(3)
    span = cols + 50
    sky = max(8, road_top)
    for index in range(7):
        kind = "cloud" if index % 2 == 0 else "cloud_small"
        speed = 1.6 + (index % 4) * 0.45
        x = (rng.uniform(0, span) - tick * speed) % span - 18
        y = 7 + rng.randint(0, max(1, sky // 4))
        scale = 0.78 + (index % 3) * 0.16
        SPRITE_OVERLAYS.append((kind, x, y, scale, 0, cols, False))

    city_scroll = tick * 8.0
    SPRITE_OVERLAYS.append(("skyline", city_scroll, road_top, 1.0, 0, cols, False))
    if VIDEO.sprites.get(SPRITE_FILES.get("road")):
        SPRITE_OVERLAYS.append(("road", tick * 54.0, road_top, float(rows), 0, cols, False))

    kinds = [kind for kind in CROWD_KINDS if VIDEO.sprites.get(SPRITE_FILES.get(kind))]
    if kinds:
        spacing = 1.45
        start = -spacing
        x = start - 2
        index = 0
        while x < cols + 4:
            kind = kinds[index % len(kinds)]
            SPRITE_OVERLAYS.append((kind, x, road_top, 1.0, 0, cols, False))
            if kind in CROWD_FLASHERS:
                period = 1.6 + (index % 11) * 0.37
                phase = (tick * 3.1 + index * 1.17) % period
                if phase < 0.08:
                    burst = 1.0 - phase / 0.08
                    flash_y = road_top - (1.65 if kind in CROWD_TALL else 1.35)
                    SPRITE_OVERLAYS.append(("flash", x + 0.25, flash_y, burst, 0, cols, False))
            x += spacing
            index += 1

    if VIDEO.sprites.get(SPRITE_FILES.get("side")):
        road_y = road_top + max(3, int((rows - road_top) * 0.62))
        bob = math.sin(tick * 11.0) * 0.12
        drive_x = cols * 0.34 + math.sin(tick * 1.5) * 2.2
        SPRITE_OVERLAYS.append(("side", drive_x, road_y + bob, 2.15, 0, cols, False))


def render_title_cruise(tick, hue):
    SPRITE_OVERLAYS.clear()
    SCENE_BANDS.clear()
    SCENE_EDGES.clear()
    cols = FRAME_WIDTH if VIDEO.active else WIDTH
    rows = MENU_ROWS if VIDEO.active else HEIGHT
    cols = max(cols, WIDTH)
    rows = max(rows, HEIGHT)
    grid = [[" " for _ in range(cols)] for _ in range(rows)]
    colors = [[None] * cols for _ in range(rows)]
    road_top = max(12, (rows * 2) // 3)
    use_sprites = _splash_sprites_ready()

    use_road = bool(VIDEO.sprites.get(SPRITE_FILES.get("road")))
    if use_sprites:
        SCENE_BANDS.append((0, road_top, (0, 0, 0)))
        if not use_road:
            SCENE_BANDS.append((road_top, rows, (40, 40, 44)))
            SCENE_EDGES.append(("top", road_top, (255, 255, 255), 3))
            SCENE_EDGES.append(("bottom", rows, (255, 255, 255), 3))
        _queue_splash_scenery(tick, cols, rows, road_top)
    else:
        for y in range(road_top, rows):
            for x in range(cols):
                grid[y][x] = "█"
                colors[y][x] = (0, 0.24, 0.0)
        for x in range(cols):
            grid[road_top][x] = "▀"
            colors[road_top][x] = (0, 1.0, 0.0)
            grid[rows - 1][x] = "▄"
            colors[rows - 1][x] = (0, 1.0, 0.0)
        building_a = [" .----. ", " |[][]| ", " |[][]| ", " |[][]| ", " |____| "]
        building_b = ["  .--.  ", " /____\\ ", " |█ █| ", " |█ █| ", " |____| "]
        start = -12 + int(-(tick * 11 + 4) % 28)
        index = 0
        x = start
        while x < cols + 12:
            art = building_a if index % 2 == 0 else building_b
            splash_blit_at(grid, colors, x, road_top - len(art), art, 15 + (index * 10) % 25, 0.35)
            x += 28
            index += 1
        person = [" o ", "/|\\", " | "]
        tall = [" o ", "/|\\", " | ", "/ \\"]
        start = -12 + int(-(tick * 18 + 9) % 7)
        index = 0
        x = start
        while x < cols + 12:
            art = tall if index % 3 == 0 else person
            splash_blit_at(grid, colors, x, road_top - len(art), art, 30 + (index * 18) % 50, 0.85)
            x += 7
            index += 1

    _draw_matrix_rain(grid, colors, tick, hue, cols, road_top)

    if not (VIDEO.active and VIDEO.sprites.get(SPRITE_FILES.get("road"))):
        dash_shift = int(tick * 34) % 10
        dash_y = min(rows - 2, road_top + max(2, (rows - road_top) // 2))
        for x in range(cols):
            if (x + dash_shift) % 10 < 5:
                if 0 <= dash_y < rows:
                    grid[dash_y][x] = "▀"
                    colors[dash_y][x] = (52, 1.0, 1.0)

    lines = []
    for y in range(rows):
        parts = []
        for x in range(cols):
            info = colors[y][x]
            char = grid[y][x]
            if info is None or char == " ":
                parts.append(" " if char == " " else paint_cell(char, hue, 0.2))
            else:
                cell_hue, value = info[0], info[1]
                sat = info[2] if len(info) > 2 else 0.85
                parts.append(paint_cell(char, cell_hue, value=value, saturation=sat))
        lines.append("".join(parts) + "\033[K")

    pulse = 0.45 + 0.55 * (0.5 + 0.5 * math.sin(tick * 4))
    lines[0] = rainbow_text(GAME_NAME.center(cols), offset=hue, step=12) + "\033[K"
    lines[1] = rgb_text(GAME_BYLINE.center(cols), hue + 160, value=0.9) + "\033[K"
    lines[2] = rgb_text(GAME_VERSION.center(cols), hue + 40, value=0.85) + "\033[K"
    prompt_row = rows - 2
    if prompt_row > 3:
        lines[prompt_row] = rgb_text("Press Enter To Play".center(cols), hue + 90, value=pulse) + "\033[K"
    return "\n".join(lines)


def splash_blit_at(grid, colors, x, y, art, hue, value=1.0):
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    for row_i, line in enumerate(art):
        gy = y + row_i
        if gy < 0 or gy >= rows:
            continue
        for i, char in enumerate(line):
            gx = x + i
            if 0 <= gx < cols and char != " ":
                grid[gy][gx] = char
                colors[gy][gx] = (hue, value)


def show_splash():
    apply_layout()
    console_write("\033[?25l\033[2J\033[H")
    hue = 0
    started = time.time()
    try:
        while True:
            tick = time.time() - started
            draw_frame(render_title_cruise(tick, hue))
            key = read_menu_key()
            if key in ("enter", " "):
                if VIDEO.active:
                    VIDEO.flush_keys()
                return True
            if key in ("esc", "q"):
                return False
            hue = (hue + 4) % 360
            time.sleep(1 / 18)
    finally:
        SPRITE_OVERLAYS.clear()
        SCENE_BANDS.clear()
        SCENE_EDGES.clear()


def pause_message(message, hint="Press Enter to continue"):
    def render(hue):
        return boxed_menu(
            hue,
            [
                ("rule", ""),
                ("title", GAME_TITLE),
                ("center", GAME_BYLINE),
                ("rule", ""),
                ("blank", ""),
                ("center", message),
                ("blank", ""),
                ("rule", ""),
                ("hint", hint),
                ("rule", ""),
            ],
        )

    wait_for_menu_choice(render, {"enter", "esc", "q", " "})


def show_high_scores():
    scores = load_high_scores()

    def render(hue):
        rows = [
            ("rule", ""),
            ("title", GAME_TITLE),
            ("center", GAME_BYLINE),
            ("rule", ""),
            ("center", "Top Placing"),
            ("blank", ""),
        ]
        if not scores:
            rows.append(("center", "No records yet. Finish a race."))
        else:
            rows.append(("dim", "   #  NAME   PLC     DIST   LEVEL"))
            for index, (place, dist, level, name) in enumerate(scores, start=1):
                label = (name.replace(" ", "_") if name.strip() else "---")[:INITIALS_LEN]
                rows.append(
                    ("dim", f"  {index:>2}. {label:<3}    P{place}  {dist:>6}   {level}")
                )
        rows.extend([("blank", ""), ("rule", ""), ("hint", "Press Enter to return"), ("rule", "")])
        return boxed_menu(hue, rows)

    wait_for_menu_choice(render, {"enter", "esc", "q"})


def enter_initials(place, distance, difficulty, start="AAA"):
    letters = list(normalize_name(start))
    cursor = 0
    while read_menu_key() is not None:
        pass

    def render(hue):
        slots = []
        for index, char in enumerate(letters):
            glyph = "_" if char == " " else char
            if index == cursor:
                slots.append(f"[{glyph}]")
            else:
                slots.append(f" {glyph} ")
        return boxed_menu(
            hue,
            [
                ("rule", ""),
                ("title", GAME_TITLE),
                ("center", GAME_BYLINE),
                ("rule", ""),
                ("center", "New High Score"),
                ("blank", ""),
                ("center", f"P{place}  {int(distance)}m  {difficulty}"),
                ("blank", ""),
                ("center", "Enter initials"),
                ("center", "  ".join(slots)),
                ("blank", ""),
                ("rule", ""),
                ("dim", "  Type A-Z   Up/Down cycle   Left/Right   Enter"),
                ("rule", ""),
            ],
        )

    console_write("\033[?25l")
    hue = 0
    try:
        while True:
            draw_frame(render(hue))
            key = read_menu_key()
            if key == "left":
                cursor = (cursor - 1) % INITIALS_LEN
            elif key == "right":
                cursor = (cursor + 1) % INITIALS_LEN
            elif key == "up":
                idx = INITIAL_CHARS.find(letters[cursor])
                letters[cursor] = INITIAL_CHARS[(idx - 1) % len(INITIAL_CHARS)]
            elif key == "down":
                idx = INITIAL_CHARS.find(letters[cursor])
                letters[cursor] = INITIAL_CHARS[(idx + 1) % len(INITIAL_CHARS)]
            elif key in ("enter", "esc", "q"):
                return "".join(letters)
            elif key == "backspace":
                letters[cursor] = " "
                if cursor > 0:
                    cursor -= 1
            elif key == " ":
                letters[cursor] = " "
                if cursor < INITIALS_LEN - 1:
                    cursor += 1
            elif key and len(key) == 1 and "a" <= key <= "z":
                letters[cursor] = key.upper()
                if cursor < INITIALS_LEN - 1:
                    cursor += 1
            hue = (hue + 7) % 360
            time.sleep(1 / 18)
    finally:
        console_write("\033[?25h")


def choose_difficulty():
    labels = ["easy", "medium", "hard"]

    def render(hue, selected):
        return boxed_menu(
            hue,
            [
                ("rule", ""),
                ("title", GAME_TITLE),
                ("center", GAME_BYLINE),
                ("rule", ""),
                ("center", "Select difficulty"),
                ("blank", ""),
                ("option", "1.  Easy     10,000 m"),
                ("option", "2.  Medium   20,000 m"),
                ("option", "3.  Hard     30,000 m"),
                ("option", "4.  Back"),
                ("blank", ""),
                ("rule", ""),
                ("dim", "  5 AI Indy cars. Lights: 3, 2, 1, GO!"),
                ("rule", ""),
                ("hint", "Up/Down + Enter"),
                ("rule", ""),
            ],
            selected=selected,
        )

    choice = wait_for_menu_select(4, render)
    if choice is None or choice == 3:
        return None
    return labels[choice]


def main():
    enable_color_output()
    AUDIO.start()
    try:
        if not show_splash():
            return
        selected = 0
        last = ""
        last_name = "AAA"
        while True:
            def render(hue, index):
                music = "On" if AUDIO.music_enabled else "Off"
                return boxed_menu(
                    hue,
                    [
                        ("rule", ""),
                        ("title", GAME_TITLE),
                        ("center", GAME_BYLINE),
                        ("rule", ""),
                        ("blank", ""),
                        ("option", "1.  Start Race"),
                        ("option", "2.  High Scores"),
                        ("option", f"3.  Music: {music}"),
                        ("option", f"4.  Display: {VIDEO.display_label()}"),
                        ("option", "5.  Exit"),
                        ("blank", ""),
                        ("rule", ""),
                        ("dim", "  " + (last or "Last: none")),
                        ("rule", ""),
                        ("dim", "  W / Up         accelerate"),
                        ("dim", "  S / Down       brake"),
                        ("dim", "  A/D or Arrows  steer"),
                        ("dim", "  5 AI racers   3-2-1-GO lights"),
                        ("rule", ""),
                        ("hint", "Up/Down + Enter"),
                        ("rule", ""),
                    ],
                    selected=index,
                )

            choice = wait_for_menu_select(5, render, start=selected)
            if choice is None or choice == 4:
                break
            selected = choice
            if choice == 0:
                difficulty = choose_difficulty()
                if difficulty is None:
                    continue
                distance, finished, place = play_race(difficulty)
                last = f"Last: P{place}  {distance}m  {difficulty}"
                if distance > 0 and is_high_score(place, distance):
                    last_name = enter_initials(place, distance, difficulty, last_name)
                    save_high_score(place, distance, difficulty, last_name)
                    show_high_scores()
                elif finished:
                    pause_message(f"Finished P{place}!  {distance}m")
                elif distance > 0:
                    pause_message(f"Race over. P{place}  {distance}m")
                selected = 0
            elif choice == 1:
                show_high_scores()
                selected = 1
            elif choice == 2:
                AUDIO.toggle_music()
                selected = 2
            elif choice == 3:
                VIDEO.toggle_fullscreen()
                selected = 3
    finally:
        AUDIO.stop()
        leave_display()
    print("Goodbye!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        AUDIO.stop()
        leave_display()
        print("Goodbye!")
        sys.exit(0)
