import os
import sys
import types

# Ensure src package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

calls = {
    'hotkey': [],
    'scroll': []
}

pyautogui_stub = types.SimpleNamespace(
    hotkey=lambda *a: calls['hotkey'].append(a),
    scroll=lambda v: calls['scroll'].append(v),
    screenshot=lambda *a, **k: types.SimpleNamespace(tobytes=lambda: b'')
)
pygetwindow_stub = types.SimpleNamespace(getWindowsWithTitle=lambda *a, **k: [])
pyperclip_stub = types.SimpleNamespace(copy=lambda *a, **k: None, paste=lambda: '')

sys.modules['pyautogui'] = pyautogui_stub
sys.modules['pygetwindow'] = pygetwindow_stub
sys.modules['pyperclip'] = pyperclip_stub

import automation

def test_scroll_to_bottom(monkeypatch):
    calls['hotkey'].clear()
    calls['scroll'].clear()
    monkeypatch.setattr(automation.time, 'sleep', lambda *a, **k: None)
    monkeypatch.setattr(automation, 'pag', pyautogui_stub)

    automation._scroll_to_bottom()

    assert calls['hotkey'] == [('end',)]
    assert calls['scroll'] == [-1500]

