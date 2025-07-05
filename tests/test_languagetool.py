import os
import sys
import types
import logging
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
    result = process_epub.ask_gpt(bot, 'file', 1, 1, 'prompt', tool)
    assert result == 'still bad'


def test_read_error_retry(monkeypatch):
    bot = DummyBot()
    responses = [RuntimeError('oops'), 'good']

    def fake_read():
        val = responses.pop(0)
        if isinstance(val, Exception):
            raise val
        return val

    monkeypatch.setattr(process_epub, 'read_response', fake_read)
    tool = types.SimpleNamespace(check=lambda txt: [])
    result = process_epub.ask_gpt(bot, 'file', 1, 1, 'prompt', tool)
    assert result == 'good'
    assert len(bot.calls) == 4


def test_language_error_with_read_failure(monkeypatch):
    bot = DummyBot()
    responses = ['bad text', RuntimeError('oops'), 'bad text']

    def fake_read():
        val = responses.pop(0)
        if isinstance(val, Exception):
            raise val
        return val

    monkeypatch.setattr(process_epub, 'read_response', fake_read)
    tool = types.SimpleNamespace(check=lambda txt: [1, 2, 3, 4])
    result = process_epub.ask_gpt(bot, 'file', 1, 1, 'prompt', tool)
    assert result == 'bad text'
    assert len(bot.calls) == 6


def test_language_failures_capped(monkeypatch, caplog):
    bot = DummyBot()
    monkeypatch.setattr(process_epub, 'read_response', lambda: 'bad')
    tool = types.SimpleNamespace(check=lambda txt: [1, 2, 3, 4])
    with caplog.at_level(logging.WARNING):
        result = process_epub.ask_gpt(
            bot, 'file', 1, 1, 'prompt', tool, max_language_failures=1
        )
    assert result == 'bad'
    assert (
        "Too many language issues in file chunk 1/1" in caplog.text
    )


def test_read_failures_capped(monkeypatch, caplog):
    bot = DummyBot()
    count = {'n': 0}

    def always_fail():
        count['n'] += 1
        raise RuntimeError('no clip')

    monkeypatch.setattr(process_epub, 'read_response', always_fail)
    tool = types.SimpleNamespace(check=lambda txt: [])
    with caplog.at_level(logging.WARNING):
        result = process_epub.ask_gpt(
            bot, 'file', 1, 1, 'prompt', tool, max_read_failures=2
        )
    assert result == ''
    assert count['n'] == 2
    assert len(bot.calls) == 4
    assert (
        "Too many read_response failures for file chunk 1/1" in caplog.text
    )


def test_login_retry(monkeypatch):
    bot = DummyBot()

    calls = {'n': 0}

    def maybe_login():
        if calls['n'] == 0:
            calls['n'] += 1
            raise process_epub.LoginRequiredError('login')
        return 'ok'

    monkeypatch.setattr(process_epub, 'read_response', maybe_login)
    import builtins
    monkeypatch.setattr(builtins, 'input', lambda *a, **k: '')
    tool = types.SimpleNamespace(check=lambda txt: [])

    result = process_epub.ask_gpt(bot, 'f', 1, 1, 'prompt', tool)
    assert result == 'ok'
    assert calls['n'] == 1


def test_login_quit(monkeypatch):
    bot = DummyBot()
    monkeypatch.setattr(
        process_epub,
        'read_response',
        lambda: (_ for _ in ()).throw(process_epub.LoginRequiredError('login')),
    )
    import builtins
    monkeypatch.setattr(builtins, 'input', lambda *a, **k: 'q')
    tool = types.SimpleNamespace(check=lambda txt: [])

    with pytest.raises(process_epub.LoginRequiredError):
        process_epub.ask_gpt(bot, 'f', 1, 1, 'prompt', tool)
