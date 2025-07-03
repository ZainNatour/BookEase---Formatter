import os
import sys
import types

# Ensure src package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

hotkeys = []
presses = []

class FakeImage:
    def __init__(self, data=b'img'):
        self.data = data
    def tobytes(self):
        return self.data

pyautogui_stub = types.SimpleNamespace(
    screenshot=lambda *a, **k: FakeImage(),
    hotkey=lambda *a: hotkeys.append(a),
    press=lambda k: presses.append(k),
    locateOnScreen=lambda *a, **k: None,
    moveTo=lambda *a, **k: None,
    click=lambda *a, **k: None,
    center=lambda box: (box[0] + box[2]/2, box[1] + box[3]/2),
)

pygetwindow_stub = types.SimpleNamespace(getWindowsWithTitle=lambda *a, **k: [])
pyperclip_stub = types.SimpleNamespace(copy=lambda *a, **k: None, paste=lambda: '')

sys.modules['pyautogui'] = pyautogui_stub
sys.modules['pygetwindow'] = pygetwindow_stub
sys.modules['pyperclip'] = pyperclip_stub


def test_ensure_running(monkeypatch):
    import automation
    monkeypatch.setattr(automation, 'pag', pyautogui_stub)
    monkeypatch.setattr(automation, 'gw', pygetwindow_stub)
    monkeypatch.setattr(automation, 'pyperclip', pyperclip_stub)
    monkeypatch.setattr(automation.time, 'sleep', lambda *a, **k: None)
    calls = {}
    windows = [[], [], [object()]]

    def fake_get(title):
        calls.setdefault('get', []).append(title)
        return windows.pop(0)

    monkeypatch.setattr(pygetwindow_stub, 'getWindowsWithTitle', fake_get)
    monkeypatch.setattr(automation, 'CHATGPT_EXE', types.SimpleNamespace(exists=lambda: True))

    def fake_popen(*a, **k):
        calls['popen'] = True
        return types.SimpleNamespace()

    monkeypatch.setattr(automation.subprocess, 'Popen', fake_popen)
    t = {'n': 0}
    def fake_time():
        val = t['n']
        t['n'] += 1
        return val
    monkeypatch.setattr(automation.time, 'time', fake_time)

    bot = automation.ChatGPTAutomation('prompt')
    bot._ensure_running()

    assert calls.get('popen') is True
    assert len(calls['get']) >= 2



def test_focus(monkeypatch):
    import automation
    monkeypatch.setattr(automation, 'pag', pyautogui_stub)
    monkeypatch.setattr(automation, 'gw', pygetwindow_stub)
    monkeypatch.setattr(automation, 'pyperclip', pyperclip_stub)
    monkeypatch.setattr(automation.time, 'sleep', lambda *a, **k: None)
    activated = {}

    class FakeWin:
        def activate(self):
            activated['done'] = True

    monkeypatch.setattr(pygetwindow_stub, 'getWindowsWithTitle', lambda t: [FakeWin()])
    bot = automation.ChatGPTAutomation('prompt')
    bot._focus()

    assert activated.get('done') is True



def test_paste(monkeypatch):
    import automation
    monkeypatch.setattr(automation, 'pag', pyautogui_stub)
    monkeypatch.setattr(automation, 'gw', pygetwindow_stub)
    monkeypatch.setattr(automation, 'pyperclip', pyperclip_stub)
    monkeypatch.setattr(automation.time, 'sleep', lambda *a, **k: None)
    calls = []

    monkeypatch.setattr(pyperclip_stub, 'copy', lambda t: calls.append(('copy', t)))
    monkeypatch.setattr(pyautogui_stub, 'hotkey', lambda *a: calls.append(('hotkey', a)))
    monkeypatch.setattr(pyautogui_stub, 'press', lambda k: calls.append(('press', k)))

    bot = automation.ChatGPTAutomation('prompt')
    bot._paste('text', hit_enter=True)

    assert ('copy', 'text') in calls
    assert ('hotkey', ('ctrl', 'v')) in calls
    assert ('press', 'enter') in calls

