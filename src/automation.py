import time, pyautogui as pag, pygetwindow as gw, pyperclip
import subprocess, os, pathlib, sys
import logging

logging.basicConfig(level=logging.INFO)

# Determine the location of the ChatGPT desktop executable.
# ``pathlib.Path`` does not provide ``expandvars`` like ``os.path`` does, so we
# expand the environment variables in the string first and then create a
# ``Path`` object. Users can override this path with the ``CHATGPT_EXE``
# environment variable.
CHATGPT_EXE = pathlib.Path(
    os.path.expanduser(
        os.path.expandvars(
            os.environ.get(
                "CHATGPT_EXE",
                r"C:\Users\ZBook\AppData\Local\Microsoft\WindowsApps\ChatGPT.exe",
            )
        )
    )
)

# Allow customising the ChatGPT window title via ``CHATGPT_WINDOW_TITLE``.
DEFAULT_WINDOW_TITLE = os.environ.get("CHATGPT_WINDOW_TITLE", "ChatGPT")


class ChatGPTAutomation:
    def __init__(self, system_prompt: str, window_title: str = DEFAULT_WINDOW_TITLE):
        self.system_prompt = system_prompt
        self.window_title = window_title
        self._window = None  # remember the ChatGPT window once located

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

    def _focus(self, timeout: float = 10.0) -> None:
        """Focus the ChatGPT window, restarting the app if needed."""
        win = self._window

        if win is None or getattr(win, "isMinimized", False):
            # Either no handle was stored or the window was minimised or closed.
            self._ensure_running(timeout=timeout)
            t0 = time.time()
            win = None
            while time.time() - t0 < timeout:
                wins = gw.getWindowsWithTitle(self.window_title)
                if wins:
                    win = wins[0]
                    break
                time.sleep(0.5)
            if win is None:
                raise RuntimeError(
                    f"ChatGPT window titled '{self.window_title}' not found after restart"
                )
            if getattr(win, "isMinimized", False):
                try:
                    win.restore()
                except Exception:
                    pass
            self._window = win

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
    same_count = 0
    t0 = time.time()
    while time.time() - t0 < timeout:
        time.sleep(0.5)
        current = pag.screenshot(region=bbox).tobytes()
        if current == last:
            same_count += 1
            if same_count == 2:
                return
        else:
            same_count = 0
        last = current
    raise RuntimeError("Timed out waiting for typing to stop")


def _scroll_to_bottom():
    """Ensure the current conversation is scrolled to the bottom so the
    Copy icon is visible."""
    pag.hotkey("end")
    time.sleep(0.2)
    pag.scroll(-1500)


def read_response(verbose: bool = False):
    """Retrieve the assistant's response from the ChatGPT Desktop UI."""
    wait_until_typing_stops()

    try:
        from src import ui_capture
    except ModuleNotFoundError:  # Fallback when src isn't a package
        import ui_capture

    for attempt in range(5):
        _scroll_to_bottom()
        try:
            ui_capture.click_copy_icon()
        except Exception as e:
            if verbose:
                print(f"Failed to click copy icon: {e}", file=sys.stderr)
        time.sleep(0.6)
        text = pyperclip.paste()
        if not text.strip():
            pag.hotkey("ctrl", "a")
            pag.hotkey("ctrl", "c")
            time.sleep(0.6)
            text = pyperclip.paste()
        if text.strip():
            return text
        logging.warning("Clipboard empty on attempt %d", attempt + 1)

    raise RuntimeError("Clipboard remained empty after 5 attempts")
