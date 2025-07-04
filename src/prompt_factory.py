SYSTEM_TEMPLATE = """You are BookEase Formatter — an EPUB repair assistant.
• Keep original meaning; correct spelling, XHTML validity, CSS syntax.
• Never invent missing content.
• Output SAME element you received, nothing more, nothing less.
• Do not add commentary.
"""


def build_system_prompt() -> str:
    return SYSTEM_TEMPLATE


def build_user_prompt(file_path: str, chunk_id: int, total: int, chunk: str) -> str:
    return (
        f"<file>{file_path}</file>\n"
        f"<chunk id='{chunk_id}/{total}'>\n{chunk}\n</chunk>"
    )

