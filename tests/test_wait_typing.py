import os
import sys
import types
import pytest

# Ensure src package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# Stub GUI modules before importing automation
class FakeImage:
    def __init__(self, data=b'img'):
        self.data = data
    def tobytes(self):
        return self.data

pyautogui_stub = types.SimpleNamespace(screenshot=lambda *a, **k: FakeImage())
pygetwindow_stub = types.SimpleNamespace(getWindowsWithTitle=lambda *a, **k: [])
pyperclip_stub = types.SimpleNamespace(copy=lambda *a, **k: None, paste=lambda: '')

sys.modules['pyautogui'] = pyautogui_stub
sys.modules['pygetwindow'] = pygetwindow_stub
sys.modules['pyperclip'] = pyperclip_stub

import automation


def test_wait_until_typing_stops(monkeypatch):
    images = [b'1', b'2', b'3', b'3', b'3']

    def screenshot(*args, **kwargs):
        return FakeImage(images.pop(0))

    monkeypatch.setattr(automation.pag, 'screenshot', screenshot)
    monkeypatch.setattr(automation.time, 'sleep', lambda s: None)

    automation.wait_until_typing_stops(timeout=5)
    assert len(images) == 0


def test_wait_until_typing_timeout(monkeypatch):
    t = {'now': 0}

    def fake_time():
        return t['now']

    def fake_sleep(s):
        t['now'] += s

    # images change every call
    seq = [b'a', b'b', b'c', b'd', b'e']
    def screenshot(*args, **kwargs):
        return FakeImage(seq.pop(0)) if seq else FakeImage(b'x')

    monkeypatch.setattr(automation.pag, 'screenshot', screenshot)
    monkeypatch.setattr(automation.time, 'sleep', fake_sleep)
    monkeypatch.setattr(automation.time, 'time', fake_time)

    with pytest.raises(RuntimeError):
        automation.wait_until_typing_stops(timeout=1)
