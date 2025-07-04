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

pygetwindow_stub = types.SimpleNamespace(
    getWindowsWithTitle=lambda *a, **k: [],
    getAllWindows=lambda: [],
)
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
    class FakeWin:
        title = 'ChatGPT'

    windows = [[], [], [FakeWin()]]

    def fake_get_all():
        calls.setdefault('get', 0)
        calls['get'] += 1
        res = windows[0]
        if len(windows) > 1:
            windows.pop(0)
        return res

    monkeypatch.setattr(pygetwindow_stub, 'getAllWindows', fake_get_all)
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
    win = bot._ensure_running()

    assert calls.get('popen') is True
    assert calls['get'] >= 2
    assert isinstance(win, FakeWin)



def test_focus(monkeypatch):
    import automation
    monkeypatch.setattr(automation, 'pag', pyautogui_stub)
    monkeypatch.setattr(automation, 'gw', pygetwindow_stub)
    monkeypatch.setattr(automation, 'pyperclip', pyperclip_stub)
    monkeypatch.setattr(automation.time, 'sleep', lambda *a, **k: None)
    activated = {'count': 0}

    class FakeWin:
        def __init__(self):
            self.title = 'ChatGPT'
        def activate(self):
            activated['count'] += 1

    win = FakeWin()
    monkeypatch.setattr(pygetwindow_stub, 'getAllWindows', lambda: [win])
    bot = automation.ChatGPTAutomation('prompt')
    bot._focus()
    assert activated['count'] == 1
    assert bot.window is win

    win.title = 'Renamed'
    bot._focus()
    assert activated['count'] == 2
    assert bot.window is win


def test_focus_restores_minimized(monkeypatch):
    import automation
    monkeypatch.setattr(automation, 'pag', pyautogui_stub)
    monkeypatch.setattr(automation, 'gw', pygetwindow_stub)
    monkeypatch.setattr(automation, 'pyperclip', pyperclip_stub)
    monkeypatch.setattr(automation.time, 'sleep', lambda *a, **k: None)
    calls = {'activate': 0, 'restore': 0}

    class FakeWin:
        def __init__(self):
            self.title = 'ChatGPT'
            self.minimized = True

        def activate(self):
            calls['activate'] += 1

        @property
        def isMinimized(self):
            return self.minimized

        def restore(self):
            calls['restore'] += 1
            self.minimized = False

    win = FakeWin()
    monkeypatch.setattr(pygetwindow_stub, 'getAllWindows', lambda: [win])
    bot = automation.ChatGPTAutomation('prompt')
    bot.window = win
    bot._focus()

    assert calls['restore'] == 1
    assert calls['activate'] == 1
    assert bot.window is win


def test_focus_recovers_missing(monkeypatch):
    import automation
    monkeypatch.setattr(automation, 'pag', pyautogui_stub)
    monkeypatch.setattr(automation, 'gw', pygetwindow_stub)
    monkeypatch.setattr(automation, 'pyperclip', pyperclip_stub)
    monkeypatch.setattr(automation.time, 'sleep', lambda *a, **k: None)
    calls = {'activate': 0}

    class FakeWin:
        def __init__(self, title='ChatGPT'):
            self.title = title

        def activate(self):
            calls['activate'] += 1

        @property
        def isMinimized(self):
            return False

        def restore(self):
            pass

    old_win = FakeWin('Old')
    new_win = FakeWin()
    windows = [[], [new_win]]

    def fake_get_all():
        res = windows[0]
        if len(windows) > 1:
            windows.pop(0)
        return res

    monkeypatch.setattr(pygetwindow_stub, 'getAllWindows', fake_get_all)
    monkeypatch.setattr(automation.ChatGPTAutomation, '_ensure_running', lambda self, timeout=10.0: new_win)

    bot = automation.ChatGPTAutomation('prompt')
    bot.window = old_win
    bot._focus()

    assert calls['activate'] == 1
    assert bot.window is new_win



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


def test_env_overrides(monkeypatch):
    monkeypatch.setenv('CHATGPT_WINDOW_TITLE', 'Foo')
    monkeypatch.setenv('CHATGPT_EXE', r'C:\Temp\ChatGPT.exe')

    import importlib
    import automation
    monkeypatch.setattr(automation, 'pag', pyautogui_stub)
    monkeypatch.setattr(automation, 'gw', pygetwindow_stub)
    monkeypatch.setattr(automation, 'pyperclip', pyperclip_stub)

    automation = importlib.reload(automation)
    bot = automation.ChatGPTAutomation('prompt')

    assert bot.window_title == 'Foo'
    assert str(automation.CHATGPT_EXE) == os.path.expandvars(r'C:\Temp\ChatGPT.exe')

