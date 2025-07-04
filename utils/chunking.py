def split_text(text: str, size: int = 1500, overlap: int = 200) -> list[str]:
    """Split ``text`` into overlapping chunks without external dependencies."""

    raw_parts = text.split("</p>")
    pieces = []
    for i, part in enumerate(raw_parts):
        if not part:
            continue
        if i < len(raw_parts) - 1:
            pieces.append(part + "</p>")
        else:
            pieces.append(part)
    chunks: list[str] = []
    for piece in pieces:
        start = 0
        while start < len(piece):
            end = start + size
            chunks.append(piece[start:end])
            start = end - overlap
    return chunks
