from langchain_text_splitters import RecursiveCharacterTextSplitter


def split_text(text: str, size: int = 1500, overlap: int = 200) -> list[str]:
    """Split ``text`` into chunks using a tiktoken-based splitter."""
    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=size,
        chunk_overlap=overlap,
        keep_separator=False,
    )
    return splitter.split_text(text)
