import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.chunking import split_text


class DummySplitter:
    def __init__(self, chunk_size, chunk_overlap, *_, **__):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.sep = "</p>"

    def split_text(self, text):
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
    return DummySplitter(chunk_size, chunk_overlap)


def test_html_paragraph_split(monkeypatch):
    from langchain.text_splitter import CharacterTextSplitter
    monkeypatch.setattr(CharacterTextSplitter, "from_tiktoken_encoder", stub_from_tiktoken_encoder)
    text = "<p>one</p><p>two</p>"
    chunks = split_text(text, size=50, overlap=0)
    assert len(chunks) == 2 and chunks[0].strip() == "<p>one</p>" and chunks[1].strip() == "<p>two</p>"


def test_overlap(monkeypatch):
    from langchain.text_splitter import CharacterTextSplitter
    monkeypatch.setattr(CharacterTextSplitter, "from_tiktoken_encoder", stub_from_tiktoken_encoder)
    text = "abcdefghi"
    chunks = split_text(text, size=5, overlap=2)
    assert chunks[1].startswith(chunks[0][-2:])
