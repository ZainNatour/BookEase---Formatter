import os
import sys
import types
import zipfile
from pathlib import Path

# Stub GUI libraries before importing the module under test
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

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.process_epub import main as cli
import src.process_epub as process_epub


class DummyBot:
    def __init__(self, prompt, window_title="ChatGPT"):
        self.prompt = prompt
    def bootstrap(self):
        pass
    def _focus(self):
        pass
    def _paste(self, text, hit_enter=False):
        self.last = text


def create_sample_epub(path: Path) -> None:
    container_xml = (
        "<?xml version='1.0'?>\n"
        "<container version='1.0' xmlns='urn:oasis:names:tc:opendocument:xmlns:container'>\n"
        "  <rootfiles>\n"
        "    <rootfile full-path='OEBPS/content.opf' media-type='application/oebps-package+xml'/>\n"
        "  </rootfiles>\n"
        "</container>"
    )
    content_opf = (
        "<?xml version='1.0'?>\n"
        "<package version='2.0' xmlns='http://www.idpf.org/2007/opf' unique-identifier='BookId'>\n"
        "  <metadata xmlns:dc='http://purl.org/dc/elements/1.1/'>\n"
        "    <dc:title>Sample</dc:title>\n"
        "    <dc:identifier id='BookId'>id123</dc:identifier>\n"
        "  </metadata>\n"
        "  <manifest>\n"
        "    <item id='ncx' href='toc.ncx' media-type='application/x-dtbncx+xml'/>\n"
        "    <item id='chap' href='chapter.xhtml' media-type='application/xhtml+xml'/>\n"
        "  </manifest>\n"
        "  <spine toc='ncx'>\n"
        "    <itemref idref='chap'/>\n"
        "  </spine>\n"
        "</package>"
    )
    toc_ncx = (
        "<?xml version='1.0' encoding='UTF-8'?>\n"
        "<ncx xmlns='http://www.daisy.org/z3986/2005/ncx/' version='2005-1'>\n"
        "  <head>\n"
        "    <meta name='dtb:uid' content='id123'/>\n"
        "  </head>\n"
        "  <docTitle><text>Sample</text></docTitle>\n"
        "  <navMap>\n"
        "    <navPoint id='navPoint-1' playOrder='1'>\n"
        "      <navLabel><text>Chapter 1</text></navLabel>\n"
        "      <content src='chapter.xhtml'/>\n"
        "    </navPoint>\n"
        "  </navMap>\n"
        "</ncx>"
    )
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        z.writestr("META-INF/container.xml", container_xml, compress_type=zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/content.opf", content_opf, compress_type=zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/toc.ncx", toc_ncx, compress_type=zipfile.ZIP_DEFLATED)
        z.writestr(
            "OEBPS/chapter.xhtml",
            "<html><body><p>Hello world.</p></body></html>",
            compress_type=zipfile.ZIP_DEFLATED,
        )
        z.writestr("OEBPS/style.css", "p { color: red; }", compress_type=zipfile.ZIP_DEFLATED)


def test_chunk_count(tmp_path, monkeypatch):
    in_path = tmp_path / "sample.epub"
    out_path = tmp_path / "out.epub"
    create_sample_epub(in_path)

    monkeypatch.setattr(process_epub, 'ChatGPTAutomation', DummyBot)
    monkeypatch.setattr(process_epub.subprocess, 'run', lambda *a, **k: types.SimpleNamespace(returncode=0, stdout='', stderr=''))

    chunks = ['a', 'b', 'c']
    def stub_split(text):
        if text.startswith('<html'):
            return list(chunks)
        return [text]
    monkeypatch.setattr(process_epub, 'split_text', stub_split)

    calls = []
    def record(bot, path, idx, total, chunk, tool, **kwargs):
        calls.append(chunk)
        return chunk
    monkeypatch.setattr(process_epub, 'ask_gpt', record)

    from click.testing import CliRunner
    runner = CliRunner()
    result = runner.invoke(cli, ['--input', str(in_path), '--output', str(out_path)])
    assert result.exit_code == 0
    html_calls = [c for c in calls if c in chunks]
    assert len(html_calls) == len(chunks)
