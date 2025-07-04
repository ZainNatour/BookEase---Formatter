import importlib

import src.prompt_factory as prompt_factory

EXPECTED_SYSTEM = """You are BookEase Formatter — an EPUB repair assistant.
• Keep original meaning; correct spelling, XHTML validity, CSS syntax.
• Never invent missing content.
• Output SAME element you received, nothing more, nothing less.
• Do not add commentary.
"""


def test_system_prompt():
    assert prompt_factory.build_system_prompt() == EXPECTED_SYSTEM


def test_user_prompt():
    user = prompt_factory.build_user_prompt('path.xhtml', 1, 3, '<p>hi</p>')
    assert user == "<file>path.xhtml</file>\n<chunk id='1/3'>\n<p>hi</p>\n</chunk>"
