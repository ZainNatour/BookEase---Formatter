import time, pyautogui as pag, pygetwindow as gw, pyperclip
import subprocess, os, pathlib

# Determine the location of the ChatGPT desktop executable. ``pathlib.Path``
# does not provide ``expandvars`` like ``os.path`` does, so we expand the
# environment variables in the string first and then create a ``Path`` object.
CHATGPT_EXE = pathlib.Path(
    os.path.expandvars(r"%LOCALAPPDATA%\Programs\ChatGPT\ChatGPT.exe")
)


class ChatGPTAutomation:
    def __init__(self, system_prompt: str, window_title="ChatGPT"):
        self.system_prompt = system_prompt
        self.window_title = window_title

    def _ensure_running(self, timeout: float = 10.0) -> None:
        """Start ChatGPT Desktop if it isn't already running."""
        if gw.getWindowsWithTitle(self.window_title):
            return
        if not CHATGPT_EXE.exists():
            raise FileNotFoundError(f"ChatGPT.exe not found at {CHATGPT_EXE}")
        subprocess.Popen(
            [str(CHATGPT_EXE)], stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, shell=False
        )
        # Wait for window to appear
        t0 = time.time()
        while time.time() - t0 < timeout:
            if gw.getWindowsWithTitle(self.window_title):
                return
            time.sleep(0.5)
        raise RuntimeError("ChatGPT window did not appear within timeout")

    def _focus(self) -> None:
        wins = gw.getWindowsWithTitle(self.window_title)
        if not wins:
            raise RuntimeError(f"ChatGPT window titled '{self.window_title}' not found. "
                            "Start the desktop app and try again.")
        win = wins[0]
        win.activate()
        time.sleep(0.2)


    def _paste(self, text: str, hit_enter=False):
        pyperclip.copy(text)
        pag.hotkey("ctrl", "v")
        if hit_enter:
            pag.press("enter")

    def bootstrap(self):
        self._ensure_running()        # ← NEW: make sure the app is up
        self._focus()
        self._paste(self.system_prompt, hit_enter=True)


def wait_until_typing_stops(bbox=(1150, 850, 50, 20), timeout=30):
    """Return when text generation finishes by monitoring a screen region.

    A small rectangle of the ChatGPT window is repeatedly captured. When two
    consecutive screenshots are identical, typing is assumed to have stopped.
    ``RuntimeError`` is raised if this doesn't happen within ``timeout``
    seconds.
    """
    last = pag.screenshot(region=bbox).tobytes()
    t0 = time.time()
    while time.time() - t0 < timeout:
        time.sleep(0.5)
        current = pag.screenshot(region=bbox).tobytes()
        if current == last:
            return
        last = current
    raise RuntimeError("Timed out waiting for typing to stop")


def read_response():
    """Retrieve the assistant's response from the ChatGPT Desktop UI."""
    wait_until_typing_stops()

    try:
        import ui_capture

        ui_capture.click_copy_icon()
    except Exception:
        pass

    text = pyperclip.paste()
    if not text:
        pag.hotkey("ctrl", "a")
        pag.hotkey("ctrl", "c")
        text = pyperclip.paste()

    if not text:
        raise RuntimeError("Clipboard did not contain any text")

    return text
