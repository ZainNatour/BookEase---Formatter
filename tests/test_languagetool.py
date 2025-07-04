import os
import sys
import types
import pytest

# Stub GUI and language tool modules before importing the module under test
pyautogui_stub = types.SimpleNamespace()
pygetwindow_stub = types.SimpleNamespace()
pyperclip_stub = types.SimpleNamespace()
sys.modules['pyautogui'] = pyautogui_stub
sys.modules['pygetwindow'] = pygetwindow_stub
sys.modules['pyperclip'] = pyperclip_stub
sys.modules['language_tool_python'] = types.SimpleNamespace(LanguageTool=lambda *a, **k: None)

# Ensure src package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src import process_epub

class DummyBot:
    def __init__(self):
        self.calls = []
    def _focus(self):
        self.calls.append('focus')
    def _paste(self, text, hit_enter=False):
        self.calls.append(('paste', text, hit_enter))


def test_retry_success(monkeypatch):
    bot = DummyBot()
    responses = ['bad text', 'good text']
    monkeypatch.setattr(process_epub, 'read_response', lambda: responses.pop(0))
    tool = types.SimpleNamespace(check=lambda txt: [1, 2, 3, 4] if txt == 'bad text' else [])
    result = process_epub.ask_gpt(bot, 'file', 1, 1, 'prompt', tool)
    assert result == 'good text'
    assert len(bot.calls) == 4  # focus/paste twice


def test_retry_failure(monkeypatch):
    bot = DummyBot()
    responses = ['bad', 'still bad']
    monkeypatch.setattr(process_epub, 'read_response', lambda: responses.pop(0))
    tool = types.SimpleNamespace(check=lambda txt: [1] * 4)
    with pytest.raises(RuntimeError):
        process_epub.ask_gpt(bot, 'file', 1, 1, 'prompt', tool)
