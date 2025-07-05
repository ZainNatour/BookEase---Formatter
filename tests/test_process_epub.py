import os
import sys
import types
import zipfile
import json
from pathlib import Path
import logging
import pytest

# Stub GUI libraries before importing the module under test
pyautogui_stub = types.SimpleNamespace(
    screenshot=lambda *a, **k: types.SimpleNamespace(tobytes=lambda: b''),
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

class DummySplitter:
    def __init__(self, chunk_size, chunk_overlap, separators):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.sep = separators[0]

    def split_text(self, text):
        yield text

def stub_from_tiktoken_encoder(chunk_size=1500, chunk_overlap=200, separators=None):
    return DummySplitter(chunk_size, chunk_overlap, separators or ['</p>'])

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.process_epub import main as cli
import src.process_epub as process_epub


class DummyBot:
    instances = []

    def __init__(self, prompt, window_title="ChatGPT"):
        self.prompt = prompt
        self.pastes = []
        self.last = ""
        DummyBot.instances.append(self)

    def bootstrap(self):
        self._paste(self.prompt, hit_enter=True)

    def _focus(self):
        pass

    def _paste(self, text, hit_enter=False):
        self.pastes.append(text)
        self.last = text


def create_sample_epub(path: Path) -> None:
    """Create a minimal EPUB file for testing."""
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


def test_process_epub(tmp_path, monkeypatch):
    in_path = tmp_path / "sample.epub"
    out_path = tmp_path / "out.epub"
    create_sample_epub(in_path)

    DummyBot.instances.clear()
    monkeypatch.setattr(process_epub, 'ChatGPTAutomation', DummyBot)
    from langchain.text_splitter import CharacterTextSplitter
    monkeypatch.setattr(CharacterTextSplitter, 'from_tiktoken_encoder', stub_from_tiktoken_encoder)

    calls = {"sys": 0, "user": []}

    def fake_system():
        calls["sys"] += 1
        return "SYS"

    def fake_user(path, idx, total, chunk):
        calls["user"].append((path, idx, total, chunk))
        return chunk

    monkeypatch.setattr(
        process_epub,
        "prompt_factory",
        types.SimpleNamespace(
            build_system_prompt=fake_system, build_user_prompt=fake_user
        ),
    )

    monkeypatch.setattr(
        process_epub,
        "read_response",
        lambda: DummyBot.instances[-1].last.upper(),
    )

    monkeypatch.setattr(
        process_epub.subprocess, "run", lambda *a, **k: types.SimpleNamespace(returncode=0, stdout="", stderr="")
    )

    from click.testing import CliRunner
    runner = CliRunner()
    result = runner.invoke(cli, ['--input', str(in_path), '--output', str(out_path)])
    assert result.exit_code == 0

    with zipfile.ZipFile(out_path, 'r') as z:
        text = z.read('OEBPS/chapter.xhtml').decode('utf-8')
    assert text == '<P>HELLO WORLD.</P>'

    bot = DummyBot.instances[0]
    assert bot.pastes[0] == 'You are a helpful assistant.'
    assert bot.pastes.count('You are a helpful assistant.') == 1
    assert calls['sys'] == 0
    assert len(bot.pastes) - 1 == len(calls['user'])


def test_resume(tmp_path, monkeypatch):
    in_path = tmp_path / "sample.epub"
    out_path = tmp_path / "out.epub"
    create_sample_epub(in_path)

    progress_path = out_path.with_suffix('.progress.json')

    monkeypatch.setattr(process_epub, 'ChatGPTAutomation', DummyBot)
    monkeypatch.setattr(process_epub.subprocess, 'run', lambda *a, **k: types.SimpleNamespace(returncode=0, stdout='', stderr=''))

    # Only split chapter.xhtml
    def split_conditional(txt):
        if txt.startswith('<html'):
            yield txt[:10]
            yield txt[10:]
        else:
            yield txt

    monkeypatch.setattr(process_epub, 'split_text', split_conditional)

    calls = []

    def crash_gpt(bot, path, idx, total, chunk, tool, **kwargs):
        calls.append(chunk)
        if len(calls) == 4:
            raise RuntimeError('boom')
        return chunk.upper()

    from langchain.text_splitter import CharacterTextSplitter
    monkeypatch.setattr(CharacterTextSplitter, 'from_tiktoken_encoder', stub_from_tiktoken_encoder)

    monkeypatch.setattr(process_epub, 'ask_gpt', crash_gpt)

    from click.testing import CliRunner
    runner = CliRunner()
    result = runner.invoke(cli, ['--input', str(in_path), '--output', str(out_path)])
    assert result.exit_code != 0
    assert progress_path.exists()
    with open(progress_path) as f:
        progress = json.load(f)
    assert progress.get('OEBPS/chapter.xhtml') == [0]

    calls.clear()
    count = {'n': 0}

    def resume_gpt(bot, path, idx, total, chunk, tool, **kwargs):
        count['n'] += 1
        return chunk.upper()

    monkeypatch.setattr(process_epub, 'ask_gpt', resume_gpt)

    result = runner.invoke(cli, ['--input', str(in_path), '--output', str(out_path)])
    assert result.exit_code == 0
    assert not progress_path.exists()
    assert count['n'] == 2


def test_focus_retry_success(monkeypatch):
    class Bot:
        def __init__(self):
            self.calls = []
            self.n = 0

        def _focus(self):
            self.calls.append('focus')
            self.n += 1
            if self.n < 2:
                raise RuntimeError('focus fail')

        def _paste(self, text, hit_enter=False):
            self.calls.append(('paste', text, hit_enter))

    bot = Bot()
    monkeypatch.setattr(process_epub, 'read_response', lambda: 'ok')
    tool = types.SimpleNamespace(check=lambda txt: [])
    result = process_epub.ask_gpt(bot, 'f', 1, 1, 'chunk', tool, focus_retries=2)
    assert result == 'ok'
    assert bot.calls.count('focus') == 2
    expected = process_epub.prompt_factory.build_user_prompt('f', 1, 1, 'chunk')
    assert ('paste', expected, True) in bot.calls


def test_focus_retry_failure(monkeypatch):
    class Bot:
        def __init__(self):
            self.calls = []

        def _focus(self):
            self.calls.append('focus')
            raise RuntimeError('no focus')

        def _paste(self, text, hit_enter=False):
            self.calls.append(('paste', text, hit_enter))

    bot = Bot()
    monkeypatch.setattr(process_epub, 'read_response', lambda: 'ok')
    tool = types.SimpleNamespace(check=lambda txt: [])
    with pytest.raises(RuntimeError):
        process_epub.ask_gpt(bot, 'f', 1, 1, 'chunk', tool, focus_retries=2)
    assert bot.calls.count('focus') == 2
    assert all(c[0] != 'paste' for c in bot.calls if isinstance(c, tuple))


def test_epubcheck_missing(tmp_path, monkeypatch):
    in_path = tmp_path / "sample.epub"
    out_path = tmp_path / "out.epub"
    create_sample_epub(in_path)

    DummyBot.instances.clear()
    monkeypatch.setattr(process_epub, 'ChatGPTAutomation', DummyBot)
    from langchain.text_splitter import CharacterTextSplitter
    monkeypatch.setattr(CharacterTextSplitter, 'from_tiktoken_encoder', stub_from_tiktoken_encoder)

    monkeypatch.setattr(
        process_epub,
        'prompt_factory',
        types.SimpleNamespace(
            build_system_prompt=lambda: 'SYS',
            build_user_prompt=lambda *a, **k: 'USER',
        ),
    )

    monkeypatch.setattr(
        process_epub,
        'read_response',
        lambda: DummyBot.instances[-1].last.upper(),
    )

    def raise_fnf(*a, **k):
        raise FileNotFoundError

    monkeypatch.setattr(process_epub.subprocess, 'run', raise_fnf)

    from click.testing import CliRunner
    runner = CliRunner()
    result = runner.invoke(cli, ['--input', str(in_path), '--output', str(out_path)])
    assert result.exit_code != 0
    assert 'epubcheck executable not found' in result.output.lower()


def test_copies_response_per_chunk(tmp_path, monkeypatch):
    in_path = tmp_path / "sample.epub"
    out_path = tmp_path / "out.epub"
    create_sample_epub(in_path)

    DummyBot.instances.clear()
    monkeypatch.setattr(process_epub, 'ChatGPTAutomation', DummyBot)
    from langchain.text_splitter import CharacterTextSplitter
    monkeypatch.setattr(CharacterTextSplitter, 'from_tiktoken_encoder', stub_from_tiktoken_encoder)

    monkeypatch.setattr(
        process_epub,
        'prompt_factory',
        types.SimpleNamespace(
            build_system_prompt=lambda: 'SYS',
            build_user_prompt=lambda *a, **k: 'USER',
        ),
    )

    read_calls = {'n': 0}

    def fake_read_response():
        read_calls['n'] += 1
        return DummyBot.instances[-1].last.upper()

    monkeypatch.setattr(process_epub, 'read_response', fake_read_response)

    monkeypatch.setattr(
        process_epub.subprocess, 'run', lambda *a, **k: types.SimpleNamespace(returncode=0, stdout='', stderr='')
    )

    expected = 0
    with zipfile.ZipFile(in_path, 'r') as zin:
        for info in zin.infolist():
            ext = Path(info.filename).suffix.lower()
            if ext in {'.xhtml', '.opf', '.ncx', '.css'}:
                text = zin.read(info.filename).decode('utf-8')
                expected += sum(1 for _ in process_epub.split_text(text))

    from click.testing import CliRunner
    runner = CliRunner()
    result = runner.invoke(cli, ['--input', str(in_path), '--output', str(out_path)])
    assert result.exit_code == 0

    assert read_calls['n'] == expected


def test_total_failures_limit(tmp_path, monkeypatch):
    in_path = tmp_path / "sample.epub"
    out_path = tmp_path / "out.epub"
    create_sample_epub(in_path)

    DummyBot.instances.clear()
    monkeypatch.setattr(process_epub, 'ChatGPTAutomation', DummyBot)
    from langchain.text_splitter import CharacterTextSplitter
    monkeypatch.setattr(CharacterTextSplitter, 'from_tiktoken_encoder', stub_from_tiktoken_encoder)

    monkeypatch.setattr(
        process_epub,
        'prompt_factory',
        types.SimpleNamespace(
            build_system_prompt=lambda: 'SYS',
            build_user_prompt=lambda *a, **k: 'USER',
        ),
    )

    def failing(*a, **k):
        return process_epub.GPTResult('BAD', failed=True)

    monkeypatch.setattr(process_epub, 'ask_gpt', failing)

    monkeypatch.setattr(
        process_epub.subprocess, 'run', lambda *a, **k: types.SimpleNamespace(returncode=0, stdout='', stderr='')
    )

    from click.testing import CliRunner
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ['--input', str(in_path), '--output', str(out_path), '--max-total-failures', '2'],
    )
    assert result.exit_code != 0
    assert 'after processing 3 chunks' in result.output.lower()


def test_non_utf8_entry(tmp_path, monkeypatch, caplog):
    in_path = tmp_path / "bad.epub"
    out_path = tmp_path / "out.epub"
    create_sample_epub(in_path)

    # Add a file encoded with cp1252 to trigger decode error
    with zipfile.ZipFile(in_path, "a") as z:
        z.writestr(
            "OEBPS/bad.xhtml",
            "<html><body><p>caf\xe9</p></body></html>".encode("cp1252"),
            compress_type=zipfile.ZIP_DEFLATED,
        )

    DummyBot.instances.clear()
    monkeypatch.setattr(process_epub, 'ChatGPTAutomation', DummyBot)
    from langchain.text_splitter import CharacterTextSplitter
    monkeypatch.setattr(CharacterTextSplitter, 'from_tiktoken_encoder', stub_from_tiktoken_encoder)

    monkeypatch.setattr(
        process_epub,
        'prompt_factory',
        types.SimpleNamespace(
            build_system_prompt=lambda: 'SYS',
            build_user_prompt=lambda *a, **k: 'USER',
        ),
    )

    monkeypatch.setattr(
        process_epub,
        'read_response',
        lambda: DummyBot.instances[-1].last.upper(),
    )

    monkeypatch.setattr(
        process_epub.subprocess, 'run', lambda *a, **k: types.SimpleNamespace(returncode=0, stdout='', stderr='')
    )

    from click.testing import CliRunner
    runner = CliRunner()
    with caplog.at_level(logging.WARNING):
        result = runner.invoke(cli, ['--input', str(in_path), '--output', str(out_path)])
    assert result.exit_code == 0
    assert 'failed to decode' in caplog.text.lower()

    with zipfile.ZipFile(out_path, 'r') as z:
        assert 'OEBPS/bad.xhtml' in z.namelist()


def test_preserves_compression(tmp_path, monkeypatch):
    in_path = tmp_path / "sample.epub"
    out_path = tmp_path / "out.epub"
    create_sample_epub(in_path)

    DummyBot.instances.clear()
    monkeypatch.setattr(process_epub, 'ChatGPTAutomation', DummyBot)
    from langchain.text_splitter import CharacterTextSplitter
    monkeypatch.setattr(CharacterTextSplitter, 'from_tiktoken_encoder', stub_from_tiktoken_encoder)

    monkeypatch.setattr(
        process_epub,
        'prompt_factory',
        types.SimpleNamespace(
            build_system_prompt=lambda: 'SYS',
            build_user_prompt=lambda *a, **k: 'USER',
        ),
    )

    monkeypatch.setattr(
        process_epub,
        'read_response',
        lambda: DummyBot.instances[-1].last.upper(),
    )

    monkeypatch.setattr(
        process_epub.subprocess, 'run', lambda *a, **k: types.SimpleNamespace(returncode=0, stdout='', stderr='')
    )

    from click.testing import CliRunner
    runner = CliRunner()
    result = runner.invoke(cli, ['--input', str(in_path), '--output', str(out_path)])
    assert result.exit_code == 0

    with zipfile.ZipFile(in_path, 'r') as zin, zipfile.ZipFile(out_path, 'r') as zout:
        assert zin.getinfo('OEBPS/content.opf').compress_type == zout.getinfo('OEBPS/content.opf').compress_type


def test_stop_on_login_required(tmp_path, monkeypatch):
    in_path = tmp_path / "sample.epub"
    out_path = tmp_path / "out.epub"
    create_sample_epub(in_path)

    DummyBot.instances.clear()
    monkeypatch.setattr(process_epub, 'ChatGPTAutomation', DummyBot)
    from langchain.text_splitter import CharacterTextSplitter
    monkeypatch.setattr(CharacterTextSplitter, 'from_tiktoken_encoder', stub_from_tiktoken_encoder)

    monkeypatch.setattr(
        process_epub,
        'prompt_factory',
        types.SimpleNamespace(
            build_system_prompt=lambda: 'SYS',
            build_user_prompt=lambda *a, **k: 'USER',
        ),
    )

    def raise_login(*a, **k):
        raise process_epub.LoginRequiredError('login needed')

    monkeypatch.setattr(process_epub, 'ask_gpt', raise_login)

    monkeypatch.setattr(
        process_epub.subprocess, 'run', lambda *a, **k: types.SimpleNamespace(returncode=0, stdout='', stderr='')
    )

    from click.testing import CliRunner
    runner = CliRunner()
    result = runner.invoke(cli, ['--input', str(in_path), '--output', str(out_path)])

    assert result.exit_code != 0
    assert 'login needed' in result.output.lower()
