import os
import sys
import types
import pathlib
import pytest

# Ensure src package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# Minimal stubs for GUI libraries compatible with other tests
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
    center=lambda box: (box[0] + box[2] / 2, box[1] + box[3] / 2),
)
pygetwindow_stub = types.SimpleNamespace(
    getWindowsWithTitle=lambda *a, **k: [],
    getAllWindows=lambda: [],
)
pyperclip_stub = types.SimpleNamespace(copy=lambda *a, **k: None, paste=lambda: '')

sys.modules['pyautogui'] = pyautogui_stub
sys.modules['pygetwindow'] = pygetwindow_stub
sys.modules['pyperclip'] = pyperclip_stub




def test_find_default_exe_selects_first_existing(monkeypatch):
    monkeypatch.setitem(sys.modules, 'pyautogui', pyautogui_stub)
    monkeypatch.setitem(sys.modules, 'pygetwindow', pygetwindow_stub)
    monkeypatch.setitem(sys.modules, 'pyperclip', pyperclip_stub)
    import automation
    monkeypatch.setattr(automation, 'DEFAULT_CHATGPT_PATHS', ['a.exe', 'b.exe', 'c.exe'])
    monkeypatch.setattr(automation.os.path, 'expandvars', lambda s: s)
    monkeypatch.setattr(automation.os.path, 'expanduser', lambda s: s)

    def fake_exists(self):
        return str(self) == 'b.exe'

    monkeypatch.setattr(pathlib.Path, 'exists', fake_exists, raising=False)

    result = automation._find_default_exe()
    assert str(result) == 'b.exe'


def test_find_default_exe_none(monkeypatch):
    monkeypatch.setitem(sys.modules, 'pyautogui', pyautogui_stub)
    monkeypatch.setitem(sys.modules, 'pygetwindow', pygetwindow_stub)
    monkeypatch.setitem(sys.modules, 'pyperclip', pyperclip_stub)
    import automation
    monkeypatch.setattr(automation, 'DEFAULT_CHATGPT_PATHS', ['x.exe', 'y.exe'])
    monkeypatch.setattr(automation.os.path, 'expandvars', lambda s: s)
    monkeypatch.setattr(automation.os.path, 'expanduser', lambda s: s)
    monkeypatch.setattr(pathlib.Path, 'exists', lambda self: False, raising=False)

    with pytest.raises(FileNotFoundError):
        automation._find_default_exe()


def test_bootstrap_pastes_prompt_once(monkeypatch):
    monkeypatch.setitem(sys.modules, 'pyautogui', pyautogui_stub)
    monkeypatch.setitem(sys.modules, 'pygetwindow', pygetwindow_stub)
    monkeypatch.setitem(sys.modules, 'pyperclip', pyperclip_stub)
    import automation
    calls = {'ensure': 0, 'focus': 0, 'paste': []}

    def fake_ensure(self):
        calls['ensure'] += 1

    def fake_focus(self):
        calls['focus'] += 1

    def fake_paste(self, text, hit_enter=False):
        calls['paste'].append((text, hit_enter))

    monkeypatch.setattr(automation.ChatGPTAutomation, '_ensure_running', fake_ensure)
    monkeypatch.setattr(automation.ChatGPTAutomation, '_focus', fake_focus)
    monkeypatch.setattr(automation.ChatGPTAutomation, '_paste', fake_paste)

    bot = automation.ChatGPTAutomation('hello')
    bot.bootstrap()

    assert calls['ensure'] == 1
    assert calls['focus'] == 1
    assert calls['paste'] == [('hello', True)]

