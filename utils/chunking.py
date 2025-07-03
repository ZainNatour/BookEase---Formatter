from langchain.text_splitter import CharacterTextSplitter


def split_text(text: str, size: int = 1500, overlap: int = 200) -> list[str]:
    """Split ``text`` into chunks using a tiktoken-based splitter."""
    splitter = CharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=size,
        chunk_overlap=overlap,
        separators=["</p>", "\n\n"],
    )
    return splitter.split_text(text)
