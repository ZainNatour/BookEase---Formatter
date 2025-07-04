import os
import sys

# Make src/ importable when running tests directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.chunking import split_text


class DummySplitter:
    """Simple splitter stub that mimics the lang-chain interface."""

    def __init__(self, chunk_size, chunk_overlap, *_, **__):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.sep = "</p>"

    def split_text(self, text: str):
        # Very naive paragraph split → chunking logic, good enough for unit tests
        pieces = [p + self.sep for p in text.split(self.sep) if p]
        chunks = []
        for piece in pieces:
            start = 0
            while start < len(piece):
                end = start + self.chunk_size
                chunks.append(piece[start:end])
                start = end - self.chunk_overlap
        return chunks


def stub_from_tiktoken_encoder(chunk_size=1500, chunk_overlap=200, **_):
    """Monkey-patch target that returns a dummy splitter."""
    return DummySplitter(chunk_size, chunk_overlap)


def test_html_paragraph_split(monkeypatch):
    # Patch RecursiveCharacterTextSplitter so utils.chunking uses the stub
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    monkeypatch.setattr(
        RecursiveCharacterTextSplitter,
        "from_tiktoken_encoder",
        stub_from_tiktoken_encoder,
    )

    text = "<p>one</p><p>two</p>"
    chunks = split_text(text, size=50, overlap=0)

    assert len(chunks) == 2
    assert chunks[0].strip() == "<p>one</p>"
    assert chunks[1].strip() == "<p>two</p>"


def test_nested_and_uppercase_tags(monkeypatch):
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    monkeypatch.setattr(
        RecursiveCharacterTextSplitter,
        "from_tiktoken_encoder",
        stub_from_tiktoken_encoder,
    )

    text = "<P>ONE <b>two <i>THREE</i></b></P><p>four</p>"
    chunks = split_text(text, size=100, overlap=0)

    assert chunks[0].strip() == "<P>ONE <b>two <i>THREE</i></b></P>"
    assert chunks[1].strip() == "<p>four</p>"


def test_overlap(monkeypatch):
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    monkeypatch.setattr(
        RecursiveCharacterTextSplitter,
        "from_tiktoken_encoder",
        stub_from_tiktoken_encoder,
    )

    text = "abcdefghi"
    chunks = split_text(text, size=5, overlap=2)

    # Ensure second chunk starts with the last 2 chars of the first chunk
    assert chunks[1].startswith(chunks[0][-2:])
