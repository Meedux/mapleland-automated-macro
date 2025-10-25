import platform
import ctypes
from ctypes import wintypes
import time


def _ensure_windows():
    if platform.system().lower() != 'windows':
        raise OSError('Window utilities currently only supported on Windows')


def list_windows():
    """Enumerate top-level visible windows and return list of (hwnd:int, title:str)."""
    _ensure_windows()
    user32 = ctypes.WinDLL('user32', use_last_error=True)

    EnumWindows = user32.EnumWindows
    EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    IsWindowVisible = user32.IsWindowVisible
    IsIconic = user32.IsIconic
    GetWindowTextLengthW = user32.GetWindowTextLengthW
    GetWindowTextW = user32.GetWindowTextW

    windows = []

    @EnumWindowsProc
    def _enum_proc(hwnd, lParam):
        try:
            if not IsWindowVisible(hwnd):
                return True
            if IsIconic(hwnd):
                return True
            length = GetWindowTextLengthW(hwnd)
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                GetWindowTextW(hwnd, buf, length + 1)
                title = buf.value
                if title and title.strip():
                    windows.append((int(hwnd), title))
        except Exception:
            pass
        return True

    EnumWindows(_enum_proc, 0)
    return windows


def find_window_by_title(substr: str):
    """Return hwnd of the first window whose title contains substr (case-insensitive), or None."""
    _ensure_windows()
    if not substr:
        return None
    for hwnd, title in list_windows():
        try:
            if substr.lower() in title.lower():
                return hwnd
        except Exception:
            continue
    return None


def _get_foreground():
    user32 = ctypes.WinDLL('user32', use_last_error=True)
    return int(user32.GetForegroundWindow())


def focus_window(hwnd: int, timeout: float = 1.0) -> bool:
    """Attempt to bring a window to the foreground using multiple techniques.

    Returns True if the window became foreground within timeout, False otherwise.
    """
    _ensure_windows()
    user32 = ctypes.WinDLL('user32', use_last_error=True)
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

    SW_RESTORE = 9
    # Try restore if minimized
    try:
        user32.ShowWindow(wintypes.HWND(hwnd), SW_RESTORE)
    except Exception:
        pass

    # If already foreground, done
    try:
        if _get_foreground() == hwnd:
            return True
    except Exception:
        pass

    # Technique: AttachThreadInput between current thread and target window thread
    try:
        GetWindowThreadProcessId = user32.GetWindowThreadProcessId
        AttachThreadInput = user32.AttachThreadInput
        BringWindowToTop = user32.BringWindowToTop
        SetForegroundWindow = user32.SetForegroundWindow
        SetFocus = user32.SetFocus
        GetCurrentThreadId = kernel32.GetCurrentThreadId

        target_tid = GetWindowThreadProcessId(wintypes.HWND(hwnd), None)
        if isinstance(target_tid, tuple):
            target_tid = target_tid[0]
        current_tid = GetCurrentThreadId()

        # Attach input, bring to top, set foreground, detach
        attached = False
        try:
            AttachThreadInput(wintypes.DWORD(current_tid), wintypes.DWORD(target_tid), True)
            attached = True
        except Exception:
            attached = False
        try:
            BringWindowToTop(wintypes.HWND(hwnd))
        except Exception:
            pass
        try:
            SetForegroundWindow(wintypes.HWND(hwnd))
        except Exception:
            pass
        try:
            SetFocus(wintypes.HWND(hwnd))
        except Exception:
            pass
        if attached:
            try:
                AttachThreadInput(wintypes.DWORD(current_tid), wintypes.DWORD(target_tid), False)
            except Exception:
                pass
    except Exception:
        pass

    # Fallback: use Alt trick — send a harmless Alt press to allow SetForegroundWindow
    try:
        # Virtual-Key codes
        VK_MENU = 0x12
        KEYEVENTF_KEYUP = 0x0002
        user32.keybd_event(VK_MENU, 0, 0, 0)
        time.sleep(0.02)
        user32.keybd_event(VK_MENU, 0, KEYEVENTF_KEYUP, 0)
    except Exception:
        pass

    # Final attempt to set foreground
    try:
        user32.SetForegroundWindow(wintypes.HWND(hwnd))
    except Exception:
        pass

    # Wait until window is foreground or timeout
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if _get_foreground() == hwnd:
                return True
        except Exception:
            pass
        time.sleep(0.05)
    return False
