import click
import zipfile
import subprocess
from pathlib import Path
import json
import logging

from src import prompt_factory

from utils.chunking import split_text
from src.automation import ChatGPTAutomation, read_response
import language_tool_python


def ask_gpt(
    bot: ChatGPTAutomation,
    file_path: str,
    chunk_id: int,
    total: int,
    chunk: str,
    tool: language_tool_python.LanguageTool,
    focus_retries: int = 3,
    max_language_failures: int = 2,
) -> str:
    """Send a chunk to ChatGPT and validate the response with LanguageTool."""
    language_failures = 0
    last_reply = ""
    while True:
        for attempt in range(focus_retries):
            try:
                bot._focus()
            except Exception:
                if attempt == focus_retries - 1:
                    raise
            else:
                break
        user_msg = prompt_factory.build_user_prompt(file_path, chunk_id, total, chunk)
        bot._paste(user_msg, hit_enter=True)
        try:
            reply = read_response()
        except RuntimeError:
            # Retry the prompt if clipboard retrieval failed
            continue

        last_reply = reply

        matches = tool.check(reply)
        if len(matches) > 3:
            language_failures += 1
            if language_failures >= max_language_failures:
                logging.warning("Too many language issues in reply")
                return last_reply
            continue

        return reply


@click.command()
@click.option('--input', 'input_path', required=True, type=click.Path(exists=True))
@click.option('--output', 'output_path', required=True, type=click.Path())
@click.option('--ignore-language-issues', '--max-language-failures',
              'max_language_failures', type=int, default=2, show_default=True,
              help='Maximum LanguageTool failures before accepting the reply')
def main(input_path: str, output_path: str, max_language_failures: int) -> None:
    bot = ChatGPTAutomation("You are a helpful assistant.")
    bot.bootstrap()
    bot._paste(prompt_factory.build_system_prompt(), hit_enter=True)
    tool = language_tool_python.LanguageTool("en-US")

    filenames: list[str] = []
    contents: dict[str, bytes] = {}

    progress_path = Path(output_path).with_suffix('.progress.json')
    if progress_path.exists():
        with open(progress_path, 'r') as f:
            progress: dict[str, list[int]] = json.load(f)
    else:
        progress = {}

    with zipfile.ZipFile(input_path, 'r') as zin:
        for info in zin.infolist():
            name = info.filename
            filenames.append(name)
            data = zin.read(name)
            ext = Path(name).suffix.lower()
            if ext in {'.xhtml', '.opf', '.ncx', '.css'}:
                text = data.decode('utf-8')
                new_parts = []
                done = set(progress.get(name, []))
                chunks = list(split_text(text))
                total = len(chunks)
                for idx, chunk in enumerate(chunks):
                    if idx in done:
                        new_parts.append(chunk)
                        continue
                    new_parts.append(
                        ask_gpt(
                            bot,
                            name,
                            idx + 1,
                            total,
                            chunk,
                            tool,
                            max_language_failures=max_language_failures,
                        )
                    )
                    done.add(idx)
                    progress[name] = sorted(done)
                    with open(progress_path, 'w') as f:
                        json.dump(progress, f)
                text = ''.join(new_parts)
                data = text.encode('utf-8')
            contents[name] = data

    with zipfile.ZipFile(output_path, 'w') as zout:
        zout.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)
        for name in filenames:
            if name == 'mimetype':
                continue
            zout.writestr(name, contents[name], compress_type=zipfile.ZIP_DEFLATED)

    try:
        result = subprocess.run(
            ['epubcheck', output_path], capture_output=True, text=True
        )
    except FileNotFoundError:
        raise SystemExit(
            'epubcheck executable not found; install from https://github.com/w3c/epubcheck'
        )
    if result.returncode != 0:
        raise SystemExit(result.stdout + result.stderr)

    if progress_path.exists():
        progress_path.unlink()


if __name__ == '__main__':
    main()
