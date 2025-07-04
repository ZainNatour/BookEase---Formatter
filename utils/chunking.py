from html.parser import HTMLParser


class _ParagraphParser(HTMLParser):
    """Collect ``<p>`` elements while preserving their original tags."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.paragraphs: list[str] = []
        self._buf: list[str] | None = None
        self._p_case: str = "p"

    # ``HTMLParser`` already lowercases tag names, so we inspect the raw
    # start tag text to recover the original letter case for ``p``.
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str]]) -> None:  # type: ignore[override]
        raw = self.get_starttag_text()
        if tag.lower() == "p":
            self._p_case = "P" if raw and raw[1].isupper() else "p"
            self._buf = [raw]
        elif self._buf is not None:
            self._buf.append(raw)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str]]) -> None:  # type: ignore[override]
        raw = self.get_starttag_text()
        if self._buf is not None:
            self._buf.append(raw)

    def handle_endtag(self, tag: str) -> None:  # type: ignore[override]
        if self._buf is None:
            return
        closing = f"</{self._p_case if tag.lower() == 'p' else tag}>"
        self._buf.append(closing)
        if tag.lower() == "p":
            self.paragraphs.append("".join(self._buf))
            self._buf = None

    def handle_data(self, data: str) -> None:  # type: ignore[override]
        if self._buf is not None:
            self._buf.append(data)


def split_text(text: str, size: int = 1500, overlap: int = 200) -> list[str]:
    """Split ``text`` into overlapping chunks without external dependencies."""

    parser = _ParagraphParser()
    parser.feed(text)
    pieces = parser.paragraphs or [text]

    chunks: list[str] = []
    for piece in pieces:
        start = 0
        first = True
        while True:
            end = start + size
            chunk = piece[start:end]
            if first and chunks and overlap > 0:
                chunk = chunks[-1][-overlap:] + chunk
            chunks.append(chunk)
            if end >= len(piece):
                break
            start = end - overlap
            first = False

    return chunks
