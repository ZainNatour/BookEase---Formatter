import os
import sys
import types

# Ensure src package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# Provide a minimal pyautogui stub so tests run without a display
pyautogui_stub = types.SimpleNamespace(
    locateOnScreen=lambda *a, **k: None,
    moveTo=lambda *a, **k: None,
    click=lambda *a, **k: None,
    center=lambda box: (box[0] + box[2] / 2, box[1] + box[3] / 2),
)
sys.modules['pyautogui'] = pyautogui_stub

import ui_capture
from ui_capture import click_copy_icon
import config


def test_click_copy_icon_found(monkeypatch):
    called = {}

    def fake_locate(*args, **kwargs):
        return (10, 20, 30, 40)

    def fake_click():
        called['clicked'] = True

    def fake_move(x, y):
        called['moved'] = (x, y)

    monkeypatch.setattr(pyautogui_stub, 'locateOnScreen', fake_locate)
    monkeypatch.setattr(pyautogui_stub, 'click', fake_click)
    monkeypatch.setattr(pyautogui_stub, 'moveTo', fake_move)
    monkeypatch.setattr(config, 'copy_icon_templates', ['dummy'])

    result = click_copy_icon()

    assert result is True
    assert called.get('clicked') is True
    assert called.get('moved') == pyautogui_stub.center((10, 20, 30, 40))


def test_click_copy_icon_not_found(monkeypatch):
    called = {}

    def fake_locate(*args, **kwargs):
        return None

    def fake_click():
        called['clicked'] = True

    monkeypatch.setattr(pyautogui_stub, 'locateOnScreen', fake_locate)
    monkeypatch.setattr(pyautogui_stub, 'click', fake_click)
    monkeypatch.setattr(pyautogui_stub, 'moveTo', lambda *a, **k: called.__setitem__('moved', True))
    monkeypatch.setattr(config, 'copy_icon_templates', ['dummy'])

    result = click_copy_icon()

    assert result is False
    assert 'clicked' not in called
    assert 'moved' not in called
