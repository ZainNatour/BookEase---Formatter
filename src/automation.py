import time, pyautogui as pag, pygetwindow as gw, pyperclip

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
        self._focus()
        self._paste(self.system_prompt, hit_enter=True)
