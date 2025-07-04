import os
import sys
import types
import importlib

# Patch src.process_epub.main before importing src.main
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

pyautogui_stub = types.SimpleNamespace(
    locateOnScreen=lambda *a, **k: None,
    moveTo=lambda *a, **k: None,
    click=lambda *a, **k: None,
    center=lambda box: (box[0] + box[2] / 2, box[1] + box[3] / 2),
)
pygetwindow_stub = types.SimpleNamespace(getWindowsWithTitle=lambda *a, **k: [])
pyperclip_stub = types.SimpleNamespace(copy=lambda *a, **k: None, paste=lambda: '')
sys.modules['pyautogui'] = pyautogui_stub
sys.modules['pygetwindow'] = pygetwindow_stub
sys.modules['pyperclip'] = pyperclip_stub
sys.modules['language_tool_python'] = types.SimpleNamespace(LanguageTool=lambda *a, **k: types.SimpleNamespace(check=lambda *_: []))

import src.process_epub as process_epub

def test_choose_epub_invokes(monkeypatch):
    called = {}

    def fake_main(in_path, out_path):
        called['args'] = (in_path, out_path)

    monkeypatch.setattr(process_epub, 'main', fake_main)

    tk_stub = types.SimpleNamespace(
        Tk=lambda: types.SimpleNamespace(withdraw=lambda: None)
    )
    filedialog_stub = types.SimpleNamespace(
        askopenfilename=lambda *a, **k: 'in.epub',
        asksaveasfilename=lambda *a, **k: 'out.epub',
    )
    tk_stub.filedialog = filedialog_stub

    monkeypatch.setitem(sys.modules, 'tkinter', tk_stub)
    monkeypatch.setitem(sys.modules, 'tkinter.filedialog', filedialog_stub)

    main = importlib.import_module('src.main')
    main = importlib.reload(main)

    main.choose_epub()

    assert called['args'] == ('in.epub', 'out.epub')
