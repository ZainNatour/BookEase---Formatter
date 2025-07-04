import os
import sys
import types
import pytest

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


@pytest.mark.parametrize(
    "icon_ret, empties, expected, hotkey_count",
    [
        (True, 0, 'icon text', 0),             # icon_success
        (False, 1, 'fallback text', 2),        # fallback_success
        (True, 2, 'retry text', 2),            # retry_success
    ],
    ids=["icon_success", "fallback_success", "retry_success"],
)
def test_read_response(monkeypatch, icon_ret, empties, expected, hotkey_count):
    hotkeys.clear()
    monkeypatch.setattr(automation, '_scroll_to_bottom', lambda: None)
    ui_stub = types.SimpleNamespace(click_copy_icon=lambda: icon_ret)
    monkeypatch.setitem(sys.modules, 'ui_capture', ui_stub)

    values = [''] * empties + [expected]

    def fake_paste():
        return values.pop(0)

    monkeypatch.setattr(pyperclip_stub, 'paste', fake_paste)

    result = automation.read_response()

    assert result == expected
    assert hotkeys == [('ctrl', 'a'), ('ctrl', 'c')] * (hotkey_count // 2)

