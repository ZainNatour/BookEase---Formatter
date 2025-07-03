import os
import sys
import types

# Ensure src package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

hotkeys = []

def fake_hotkey(*args):
    hotkeys.append(args)

class FakeImage:
    def __init__(self, data=b'img'):
        self.data = data
    def tobytes(self):
        return self.data

# Stub pyautogui
pyautogui_stub = types.SimpleNamespace(
    screenshot=lambda *a, **k: FakeImage(),
    hotkey=fake_hotkey,
    locateOnScreen=lambda *a, **k: None,
    moveTo=lambda *a, **k: None,
    click=lambda *a, **k: None,
    center=lambda box: (box[0] + box[2] / 2, box[1] + box[3] / 2),
)
sys.modules['pyautogui'] = pyautogui_stub

# Stub pygetwindow to avoid platform errors
pygetwindow_stub = types.SimpleNamespace(getWindowsWithTitle=lambda *a, **k: [])
sys.modules['pygetwindow'] = pygetwindow_stub

# Stub pyperclip
pyperclip_stub = types.SimpleNamespace(copy=lambda *a, **k: None, paste=lambda: '')
sys.modules['pyperclip'] = pyperclip_stub

import automation

# Avoid waiting during tests
automation.time.sleep = lambda *a, **k: None


def test_read_response_icon_success(monkeypatch):
    hotkeys.clear()
    ui_stub = types.SimpleNamespace(click_copy_icon=lambda: True)
    monkeypatch.setitem(sys.modules, 'ui_capture', ui_stub)
    monkeypatch.setattr(pyperclip_stub, 'paste', lambda: 'icon text')

    result = automation.read_response()

    assert result == 'icon text'
    assert hotkeys == []


def test_read_response_fallback_success(monkeypatch):
    hotkeys.clear()
    ui_stub = types.SimpleNamespace(click_copy_icon=lambda: False)
    monkeypatch.setitem(sys.modules, 'ui_capture', ui_stub)
    paste_values = ['', 'fallback text']
    monkeypatch.setattr(pyperclip_stub, 'paste', lambda: paste_values.pop(0))

    result = automation.read_response()

    assert result == 'fallback text'
    assert hotkeys == [('ctrl', 'a'), ('ctrl', 'c')]

