# PsyRacer V1.0 by DiamondHand.Dev
# Arcade pseudo-3D racer. Arrows/WASD to drive. Esc: menu.

import ctypes
import math
import os
import random
import sys
import threading
import time
from ctypes import wintypes

WIDTH = 79
HEIGHT = 24
HORIZON = 7
FPS = 20
GAME_DIR = os.path.dirname(os.path.abspath(__file__))
HIGH_SCORES_FILE = os.path.join(GAME_DIR, "racer_scores.txt")
MUSIC_FILE = os.path.join(GAME_DIR, "Assets", "Background Music.mp3")
GAME_NAME = "PsyRacer"
GAME_VERSION = "V1.0"
GAME_TITLE = "PsyRacer V1.0"
GAME_BYLINE = "by Diamond Hand Dev"
RESET = "\033[0m"
MENU_INNER = 52
MENU_ROWS = 24

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


def _handle_from_std(kind):
    return kernel32.GetStdHandle(ctypes.c_ulong(kind).value)


class GameAudio:
    MUSIC_ALIAS = "racerbgm"

    def __init__(self):
        self.music_on = False
        self.music_enabled = False
        self._music_open = False
        self._looping = False

    def mci(self, command):
        buf = ctypes.create_unicode_buffer(256)
        err = winmm.mciSendStringW(command, buf, 255, None)
        return err, buf.value

    def start(self):
        if not os.path.isfile(MUSIC_FILE):
            return
        self.mci(f"close {self.MUSIC_ALIAS}")
        err, _ = self.mci(f'open "{MUSIC_FILE}" type mpegvideo alias {self.MUSIC_ALIAS}')
        if err != 0:
            return
        self._music_open = True
        self.mci(f"setaudio {self.MUSIC_ALIAS} volume to 400")
        err, _ = self.mci(f"play {self.MUSIC_ALIAS} repeat")
        if err == 0:
            self.music_on = True
            self.music_enabled = True
            return
        err, _ = self.mci(f"play {self.MUSIC_ALIAS}")
        if err == 0:
            self.music_on = True
            self.music_enabled = True
            self._looping = True
            threading.Thread(target=self._loop_music, daemon=True).start()

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
                self.mci(f"play {self.MUSIC_ALIAS}")
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
        if kernel32.GetConsoleMode(self._h_in, ctypes.byref(self._old_in)):
            self._in_saved = True
            kernel32.SetConsoleMode(self._h_in, ENABLE_EXTENDED_FLAGS | ENABLE_PROCESSED_INPUT)
            kernel32.FlushConsoleInputBuffer(self._h_in)
        if kernel32.GetConsoleMode(self._h_out, ctypes.byref(self._old_out)):
            self._out_saved = True
            kernel32.SetConsoleMode(
                self._h_out,
                self._old_out.value | ENABLE_PROCESSED_OUTPUT | ENABLE_VIRTUAL_TERMINAL_PROCESSING,
            )
        sys.stdout.write("\033[?25l\033[2J\033[H")
        sys.stdout.flush()
        return self

    def __exit__(self, exc_type, exc, tb):
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()
        if self._in_saved:
            kernel32.FlushConsoleInputBuffer(self._h_in)
            kernel32.SetConsoleMode(self._h_in, self._old_in)
        if self._out_saved:
            kernel32.SetConsoleMode(self._h_out, self._old_out)
        self._pressed.clear()
        return False

    def pump(self):
        self._taps = set()
        self._pump_console()
        self._pump_msvcrt()

    def down(self, vk):
        if async_key_down(vk):
            return True
        if vk in self._taps:
            return True
        return self._got_key_up and vk in self._pressed

    def _pump_console(self):
        count = wintypes.DWORD()
        if not kernel32.GetNumberOfConsoleInputEvents(self._h_in, ctypes.byref(count)):
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
        if self._msvcrt is None:
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
            handle, mode.value | ENABLE_PROCESSED_OUTPUT | ENABLE_VIRTUAL_TERMINAL_PROCESSING
        )
    in_handle = _handle_from_std(STD_INPUT_HANDLE)
    in_mode = wintypes.DWORD()
    if kernel32.GetConsoleMode(in_handle, ctypes.byref(in_mode)):
        kernel32.SetConsoleMode(in_handle, ENABLE_EXTENDED_FLAGS | ENABLE_PROCESSED_INPUT)


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


def draw_frame(text):
    lines = text.split("\n")
    parts = ["\033[H"]
    height = max(MENU_ROWS, len(lines), HEIGHT)
    for index in range(height):
        line = lines[index] if index < len(lines) else ""
        if "\033[K" not in line:
            line += "\033[K"
        parts.append(line + "\n")
    sys.stdout.write("".join(parts))
    sys.stdout.flush()


def read_menu_key():
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
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()
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
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()


def wait_for_menu_select(option_count, render, start=0):
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()
    selected = start % option_count if option_count else 0
    hue = 0
    try:
        while True:
            draw_frame(render(hue, selected))
            key = read_menu_key()
            if key == "up":
                selected = (selected - 1) % option_count
            elif key == "down":
                selected = (selected + 1) % option_count
            elif key == "enter":
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
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()


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
    return "\n".join(lines)


def load_high_scores():
    scores = []
    if os.path.isfile(HIGH_SCORES_FILE):
        try:
            with open(HIGH_SCORES_FILE, "r", encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split(",")
                    scores.append((int(parts[0]), parts[1] if len(parts) > 1 else "medium"))
        except (OSError, ValueError):
            scores = []
    scores.sort(key=lambda item: item[0], reverse=True)
    return scores[:10]


def save_high_score(distance, difficulty):
    scores = load_high_scores()
    scores.append((int(distance), difficulty))
    scores.sort(key=lambda item: item[0], reverse=True)
    scores = scores[:10]
    with open(HIGH_SCORES_FILE, "w", encoding="utf-8") as handle:
        for dist, level in scores:
            handle.write(f"{dist},{level}\n")


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


def project_row(y, distance, player_x):
    t = (y - HORIZON) / max(1, HEIGHT - 1 - HORIZON)
    t = max(0.02, min(1.0, t))
    look_ahead = (1.0 - t) * 70
    bend = road_curve(distance + look_ahead) * ((1.0 - t) ** 2) * 22
    half = 2.2 + t * 26
    center = WIDTH / 2 - player_x * half + bend
    return t, center, half


def world_project(rel_z, x_lane, distance, player_x):
    if rel_z < 1.2 or rel_z > 88:
        return None
    t = clamp(13.0 / rel_z, 0.04, 1.15)
    y = int(HORIZON + t * (HEIGHT - 1 - HORIZON))
    y = clamp(y, HORIZON, HEIGHT - 2)
    _, center, half = project_row(y, distance, player_x)
    return t, center + x_lane * half, y


def paint_cell(char, hue, value=1.0, saturation=0.85):
    if char == " ":
        return " "
    return rgb_text(char, hue, saturation=saturation, value=value)


def blit_sprite(grid, colors, cx, bottom_y, lines, hue, value=1.0):
    start_y = int(bottom_y) - len(lines) + 1
    width = max(len(line) for line in lines)
    left = int(cx - width / 2)
    for row_i, line in enumerate(lines):
        gy = start_y + row_i
        if gy < 0 or gy >= HEIGHT:
            continue
        pad = line.ljust(width)
        for i, char in enumerate(pad):
            gx = left + i
            if 0 <= gx < WIDTH and char != " ":
                grid[gy][gx] = char
                colors[gy][gx] = (hue, value)


def indy_sprite(scale, number=None):
    if scale < 0.28:
        return ["▲"]
    if scale < 0.55:
        return ["▲", "o"]
    if scale < 0.85:
        mark = str(number)[-1] if number is not None else "█"
        return [" /\\ ", f"o{mark}{mark}o"]
    if scale < 1.2:
        mark = str(number)[-1] if number is not None else "█"
        return ["  /\\  ", f" /{mark}{mark}\\ ", f"o|{mark}{mark}|o"]
    mark = "█"
    nose = str(number) if number is not None and number < 10 else (str(number)[-1] if number else "█")
    return [
        "   /\\   ",
        f"  /{nose}{nose}\\  ",
        f" /{mark}{mark}{mark}{mark}\\ ",
        f"o|{mark}{mark}{mark}{mark}|o",
    ]


def draw_tree(grid, colors, cx, cy, scale):
    if scale < 0.35:
        blit_sprite(grid, colors, cx, cy, ["*"], 125, 0.8)
        return
    if scale < 0.7:
        blit_sprite(grid, colors, cx, cy, ["^", "|"], 125)
        return
    blit_sprite(grid, colors, cx, cy, [" ### ", "#####", "  |  "], 125)
    # trunk slightly browner
    blit_sprite(grid, colors, cx, cy, ["     ", "     ", "  |  "], 30, 0.7)


def draw_building(grid, colors, cx, cy, scale, hue):
    if scale < 0.4:
        blit_sprite(grid, colors, cx, cy, ["█"], hue, 0.7)
        return
    if scale < 0.8:
        blit_sprite(grid, colors, cx, cy, ["▄█▄", "█▄█"], hue, 0.8)
        return
    blit_sprite(grid, colors, cx, cy, ["▄████▄", "█ ▄▄ █", "█▄▄▄▄█"], hue, 0.85)


def draw_person(grid, colors, cx, cy, scale, hue):
    if scale < 0.45:
        blit_sprite(grid, colors, cx, cy, ["o"], hue)
        return
    if scale < 0.9:
        blit_sprite(grid, colors, cx, cy, ["o", "|"], hue)
        return
    pose = random.Random(int(cx) * 13 + int(cy)).choice(
        [[" o ", "/|\\", " | "], [" o ", "/| ", " | "], [" o ", " |\\", " | "]]
    )
    blit_sprite(grid, colors, cx, cy, pose, hue)


def draw_scenery(grid, colors, distance, player_x, finish_distance):
    start = int(distance) + 6
    end = int(distance) + 82
    z = start - (start % 4)
    props = []
    while z < end:
        rel = z - distance
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
        projected = world_project(rel, x_lane, distance, player_x)
        if projected is None:
            continue
        scale, cx, cy = projected
        if kind == "tree":
            draw_tree(grid, colors, cx, cy, scale)
        elif kind == "building":
            draw_building(grid, colors, cx, cy, scale, 200 + int(rel * 3) % 80)
        else:
            draw_person(grid, colors, cx, cy, scale, 20 + int(cx * 7) % 40)


def draw_finish_banner(grid, colors, distance, player_x, finish_distance):
    rel = finish_distance - distance
    projected = world_project(max(rel, 1.4), 0.0, distance, player_x)
    if projected is None:
        return
    scale, cx, cy = projected
    _, center, half = project_row(cy, distance, player_x)
    left = int(center - half)
    right = int(center + half)
    if 0 <= cy < HEIGHT:
        for x in range(max(0, left), min(WIDTH, right + 1)):
            check = ((x + int(distance)) // 2) % 2 == 0
            grid[cy][x] = "#" if check else " "
            colors[cy][x] = (0 if check else 50, 1.0)
        if cy - 1 >= 0:
            label = " FINISH "
            start = max(0, int(center - len(label) / 2))
            for i, char in enumerate(label):
                x = start + i
                if 0 <= x < WIDTH:
                    grid[cy - 1][x] = char
                    colors[cy - 1][x] = (50, 1.0)
    posts = [center - half, center + half]
    for post in posts:
        px = int(post)
        height = 2 + int(scale * 3)
        for i in range(height):
            gy = cy - i
            if 0 <= gy < HEIGHT and 0 <= px < WIDTH:
                grid[gy][px] = "║"
                colors[gy][px] = (40, 1.0)


def draw_start_lights(grid, colors, stage, label):
    """stage 0=off, 1-3 red lamps on from top, 4=green."""
    cx = WIDTH // 2
    top = 1
    box = [
        "┌─┐",
        "│ │",
        "├─┤",
        "│ │",
        "├─┤",
        "│ │",
        "└─┘",
    ]
    blit_sprite(grid, colors, cx, top + len(box) - 1, box, 220, 0.9)
    lamp_rows = [top + 1, top + 3, top + 5]
    for index, gy in enumerate(lamp_rows):
        if not (0 <= gy < HEIGHT):
            continue
        if stage == 4:
            lamp, hue, value = "●", 120, 1.0
        elif index < stage:
            lamp, hue, value = "●", 0, 1.0
        else:
            lamp, hue, value = "○", 0, 0.25
        gx = cx
        if 0 <= gx < WIDTH:
            grid[gy][gx] = lamp
            colors[gy][gx] = (hue, value)
    if label:
        text = f" {label} "
        start = cx - len(text) // 2
        gy = top + len(box)
        if 0 <= gy < HEIGHT:
            for i, char in enumerate(text):
                gx = start + i
                if 0 <= gx < WIDTH:
                    grid[gy][gx] = char
                    colors[gy][gx] = (50 if stage == 4 else 0, 1.0)


def draw_car_sprite(grid, colors, cx, cy, scale, hue, number=None):
    body = indy_sprite(scale, number)
    blit_sprite(grid, colors, cx, cy, body, hue)


def draw_player_car(grid, colors, hue, crashed):
    sprite = indy_sprite(1.35, None)
    car_hue = 0 if crashed else hue
    blit_sprite(grid, colors, WIDTH / 2, HEIGHT - 2, sprite, car_hue)


def race_position(distance, cars):
    ahead = sum(1 for car in cars if car.z > distance)
    return ahead + 1, len(cars) + 1


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
    grid = [[" " for _ in range(WIDTH)] for _ in range(HEIGHT)]
    colors = [[None] * WIDTH for _ in range(HEIGHT)]

    for y in range(HORIZON):
        sky_v = 0.18 + 0.55 * (1 - y / max(1, HORIZON))
        for x in range(WIDTH):
            grid[y][x] = "·" if (x + y + int(distance / 8)) % 17 == 0 else " "
            colors[y][x] = (hue + 210 + y * 6, sky_v)

    for y in range(HORIZON, HEIGHT):
        t, center, half = project_row(y, distance, player_x)
        left_edge = int(center - half)
        right_edge = int(center + half)
        stripe = int(distance * 0.35 + (1 - t) * 18)
        rumble = stripe % 2 == 0
        grass_hue = hue + 110 if rumble else hue + 130
        road_hue = hue + 280
        for x in range(WIDTH):
            if x < left_edge - 1 or x > right_edge + 1:
                grid[y][x] = "." if rumble else " "
                colors[y][x] = (grass_hue, 0.35 + 0.25 * t)
            elif x in (left_edge - 1, left_edge, right_edge, right_edge + 1):
                grid[y][x] = "#"
                colors[y][x] = (0 if rumble else 40, 0.9)
            else:
                center_mark = abs(x - int(center)) <= 0 and stripe % 4 < 2 and t > 0.2
                grid[y][x] = ":" if center_mark else " "
                colors[y][x] = (road_hue, 0.25 + 0.5 * t)

    draw_scenery(grid, colors, distance, player_x, finish_distance)
    if -5 < finish_distance - distance < 85:
        draw_finish_banner(grid, colors, distance, player_x, finish_distance)

    cars_draw = sorted(cars, key=lambda car: -(car.z - distance))
    for car in cars_draw:
        rel = car.z - distance
        if rel < 2.2 or rel > 78:
            continue
        projected = world_project(rel, car.x, distance, player_x)
        if projected is None:
            continue
        scale, cx, cy = projected
        draw_car_sprite(grid, colors, cx, cy, scale, car.hue, car.number)

    draw_player_car(grid, colors, hue + 20, crashed)
    if lights_stage:
        draw_start_lights(grid, colors, lights_stage, countdown_text)

    pos, field = race_position(distance, cars)
    hud_speed = int(speed * 180)
    hud_dist = int(distance)
    remain = max(0, int(finish_distance - distance))
    status = "CRASH" if crashed else ("FINISH" if finished else difficulty.upper())
    header = (
        f" {GAME_TITLE}  P{pos}/{field}  SPEED {hud_speed:3d}  "
        f"{hud_dist:5d}/{int(finish_distance)}m  {status} "
    )
    header = header[:WIDTH].ljust(WIDTH)

    lines = [rainbow_text(header, offset=hue, step=8) + "\033[K"]
    for y in range(HEIGHT):
        parts = []
        for x in range(WIDTH):
            info = colors[y][x]
            if info is None:
                parts.append(grid[y][x])
            else:
                cell_hue, value = info
                parts.append(paint_cell(grid[y][x], cell_hue, value=value))
        lines.append("".join(parts) + "\033[K")
    help_line = "  W/Up gas   S/Down brake   A/D or Arrows steer   Esc quit "
    lines.append(rgb_text(help_line.ljust(WIDTH), hue + 90, value=0.8) + "\033[K")
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
    settings = DIFFICULTY[difficulty]
    finish_distance = settings["finish"]
    distance = 0.0
    player_x = 0.0
    speed = 0.0
    cars = make_field(settings)
    crashed = False
    crash_timer = 0
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

            if crashed:
                speed *= 0.86
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

            if not crashed and racing and not finished:
                for car in cars:
                    rel = car.z - distance
                    if 2.0 < rel < 7.5 and abs(car.x - player_x) < 0.28:
                        crashed = True
                        crash_timer = 12
                        speed *= 0.25
                        car.speed *= 0.7
                        break

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
        r"              ___               ",
        r"      _______//_\\_______       ",
        r"     /  __  /////  __    \      ",
        "    /  " + wheel + "|======|" + wheel + r"   \     ",
        r"    \__/               \__/     ",
    ]
    width = max(len(line) for line in body)
    return [line.ljust(width) for line in body]


def render_title_cruise(tick, hue):
    grid = [[" " for _ in range(WIDTH)] for _ in range(HEIGHT)]
    colors = [[None] * WIDTH for _ in range(HEIGHT)]
    cream_start = 8
    road_top = 16
    road_bot = 21

    for y in range(cream_start):
        for x in range(WIDTH):
            speck = (x * 13 + y * 7 + int(tick * 3)) % 11 == 0
            grid[y][x] = "█" if speck else " "
            colors[y][x] = (10, 0.12 if speck else 0.06)

    for y in range(cream_start, road_top):
        for x in range(WIDTH):
            grid[y][x] = " "
            colors[y][x] = (28, 0.78)

    # Pixel smoke / debris behind the car, drifting slowly
    rng = random.Random(7)
    for _ in range(48):
        bx = (rng.randint(8, 55) - int(tick * 10)) % (WIDTH + 12) - 4
        by = rng.randint(2, 12)
        size = rng.choice((1, 1, 2, 3))
        smoke_hue = rng.choice((160, 170, 0, 10))
        smoke_v = rng.choice((0.08, 0.12, 0.18, 0.28))
        for dy in range(size):
            for dx in range(size):
                splash_put(grid, colors, bx + dx, by + dy, "█", smoke_hue, smoke_v)

    building_a = [" .----. ", " |[][]| ", " |[][]| ", " |____| "]
    building_b = ["  .--.  ", " /____\\ ", " |█ █| ", " |____| "]
    for index, x in enumerate(loop_x(24, 4, 11, tick)):
        art = building_a if index % 2 == 0 else building_b
        splash_blit(grid, colors, x, 12, art, 15 + (index * 10) % 25, 0.35)

    tree = ["  ###  ", " ##### ", "   |   "]
    tall = ["   #   ", "  ###  ", " ##### ", "   |   "]
    for index, x in enumerate(loop_x(18, 9, 18, tick)):
        art = tall if index % 3 == 0 else tree
        splash_blit(grid, colors, x, road_top - len(art), art, 120, 0.55)

    for y in range(road_top, HEIGHT):
        for x in range(WIDTH):
            grid[y][x] = "█"
            colors[y][x] = (0, 0.07)
    dash_shift = int(tick * 34) % 10
    for x in range(WIDTH):
        if (x + dash_shift) % 10 < 5:
            splash_put(grid, colors, x, road_top + 2, "▀", 0, 0.35)

    car = f1_side_car(int(tick * 18))
    splash_blit(grid, colors, 10, road_top - 2, car, hue, 1.0)

    lines = []
    for y in range(HEIGHT):
        parts = []
        for x in range(WIDTH):
            info = colors[y][x]
            char = grid[y][x]
            if info is None or char == " ":
                parts.append(" " if char == " " else paint_cell(char, hue, 0.2))
            else:
                cell_hue, value = info
                parts.append(paint_cell(char, cell_hue, value=value))
        lines.append("".join(parts) + "\033[K")

    pulse = 0.45 + 0.55 * (0.5 + 0.5 * math.sin(tick * 4))
    lines[0] = rainbow_text(GAME_NAME.center(WIDTH), offset=hue, step=12) + "\033[K"
    lines[1] = rgb_text(GAME_BYLINE.center(WIDTH), hue + 160, value=0.9) + "\033[K"
    lines[2] = rgb_text(GAME_VERSION.center(WIDTH), hue + 40, value=0.85) + "\033[K"
    if HEIGHT > 22:
        lines[22] = rgb_text("Press Enter To Play".center(WIDTH), hue + 90, value=pulse) + "\033[K"
    return "\n".join(lines)


def show_splash():
    sys.stdout.write("\033[?25l\033[2J\033[H")
    sys.stdout.flush()
    hue = 0
    started = time.time()
    try:
        while True:
            tick = time.time() - started
            draw_frame(render_title_cruise(tick, hue))
            key = read_menu_key()
            if key in ("enter", " "):
                return True
            if key in ("esc", "q"):
                return False
            hue = (hue + 4) % 360
            time.sleep(1 / 18)
    finally:
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()


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
            ("center", "High Scores"),
            ("blank", ""),
        ]
        if not scores:
            rows.append(("center", "No races finished yet."))
        else:
            rows.append(("dim", "   #    DIST     LEVEL"))
            for index, (dist, level) in enumerate(scores, start=1):
                rows.append(("dim", f"  {index:>2}.  {dist:>6}    {level}"))
        rows.extend([("blank", ""), ("rule", ""), ("hint", "Press Enter to return"), ("rule", "")])
        return boxed_menu(hue, rows)

    wait_for_menu_choice(render, {"enter", "esc", "q"})


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
                        ("option", "4.  Exit"),
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

            choice = wait_for_menu_select(4, render, start=selected)
            if choice is None or choice == 3:
                break
            selected = choice
            if choice == 0:
                difficulty = choose_difficulty()
                if difficulty is None:
                    continue
                distance, finished, place = play_race(difficulty)
                last = f"Last: P{place}  {distance}m  {difficulty}"
                if finished:
                    save_high_score(distance, difficulty)
                    pause_message(f"Finished P{place}!  {distance}m")
                elif distance > 0:
                    save_high_score(distance, difficulty)
                    pause_message(f"Race over. P{place}  {distance}m")
                selected = 0
            elif choice == 1:
                show_high_scores()
                selected = 1
            elif choice == 2:
                AUDIO.toggle_music()
                selected = 2
    finally:
        AUDIO.stop()
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()
    print("Goodbye!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        AUDIO.stop()
        sys.stdout.write("\033[?25h")
        print("\nGoodbye!")
        sys.exit(0)
