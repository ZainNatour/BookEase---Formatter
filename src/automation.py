import time, pyautogui as pag, pygetwindow as gw, pyperclip
import subprocess, os, pathlib

CHATGPT_EXE = pathlib.Path(
    r"%LOCALAPPDATA%\Programs\ChatGPT\ChatGPT.exe"
).expandvars()

def _ensure_running(self, timeout: float = 10.0) -> None:
    """Start ChatGPT Desktop if it isn’t already running."""
    if gw.getWindowsWithTitle(self.window_title):
        return
    if not CHATGPT_EXE.exists():
        raise FileNotFoundError(f"ChatGPT.exe not found at {CHATGPT_EXE}")
    subprocess.Popen([str(CHATGPT_EXE)], stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, shell=False)
    # Wait for window
    t0 = time.time()
    while time.time() - t0 < timeout:
        if gw.getWindowsWithTitle(self.window_title):
            return
        time.sleep(0.5)
    raise RuntimeError("ChatGPT window did not appear within timeout")

class ChatGPTAutomation:
    def __init__(self, system_prompt: str, window_title="ChatGPT"):
        self.system_prompt = system_prompt
        self.window_title = window_title

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
