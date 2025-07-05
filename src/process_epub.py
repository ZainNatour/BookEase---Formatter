import click
import zipfile
import subprocess
from pathlib import Path
import json
import logging
import os

from src import prompt_factory

from utils.chunking import split_text
from src.automation import ChatGPTAutomation, read_response, LoginRequiredError
import language_tool_python


class GPTResult(str):
    """String subclass that carries a failure flag."""

    def __new__(cls, text: str, failed: bool = False):
        obj = str.__new__(cls, text)
        obj.failed = failed
        return obj


def ask_gpt(
    bot: ChatGPTAutomation,
    file_path: str,
    chunk_id: int,
    total: int,
    chunk: str,
    tool: language_tool_python.LanguageTool,
    focus_retries: int = 3,
    max_language_failures: int = 2,
    max_read_failures: int = 5,
) -> GPTResult:
    """Send a chunk to ChatGPT and validate the response with LanguageTool."""
    language_failures = 0
    read_failures = 0
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
        user_msg = prompt_factory.build_user_prompt(
            file_path, chunk_id, total, chunk
        )
        bot._paste(user_msg, hit_enter=True)
        try:
            reply = read_response()
        except LoginRequiredError as e:
            prompt = f"{e} Press Enter to retry or type 'q' to quit: "
            try:
                ans = input(prompt)
            except EOFError:
                ans = 'q'
            if ans.strip().lower().startswith('q'):
                raise
            continue
        except RuntimeError:
            read_failures += 1
            if read_failures >= max_read_failures:
                logging.warning(
                    "Too many read_response failures for %s chunk %d/%d",
                    file_path,
                    chunk_id,
                    total,
                )
                # now returns a GPTResult with failed=True
                return GPTResult(last_reply, failed=True)
            # Retry the prompt if clipboard retrieval failed
            continue

        read_failures = 0
        last_reply = reply

        matches = tool.check(reply)
        if len(matches) > 3:
            language_failures += 1
            if language_failures >= max_language_failures:
                logging.warning(
                    "Too many language issues in %s chunk %d/%d",
                    file_path,
                    chunk_id,
                    total,
                )
                # also return a failure here
                return GPTResult(last_reply, failed=True)
            continue

        return GPTResult(reply)


@click.command()
@click.option(
    '--input', 'input_path', required=True, type=click.Path(exists=True)
)
@click.option('--output', 'output_path', required=True, type=click.Path())
@click.option(
    '--ignore-language-issues', '--max-language-failures',
    'max_language_failures', type=int, default=2, show_default=True,
    help='Maximum LanguageTool failures before accepting the reply'
)
@click.option(
    '--max-read-failures', type=int, default=5, show_default=True,
    help='Maximum consecutive read_response failures before giving up'
)
@click.option(
    '--max-total-failures', type=int, default=10, show_default=True,
    help='Maximum total GPT failures before stopping processing'
)
def main(
    input_path: str,
    output_path: str,
    max_language_failures: int,
    max_read_failures: int,
    max_total_failures: int,
) -> None:
    logging.basicConfig(level=logging.INFO)
    bot = ChatGPTAutomation(prompt_factory.build_system_prompt())
    bot.bootstrap()

    lt_path = os.getenv("LANGTOOL_PATH")
    if lt_path and Path(lt_path).exists():
        tool = language_tool_python.LanguageTool("en-US", path=lt_path)
    else:
        tool = language_tool_python.LanguageTool("en-US")

    filenames: list[str] = []
    contents: dict[str, bytes] = {}
    infos: dict[str, zipfile.ZipInfo] = {}

    total_failures = 0
    processed_chunks = 0

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
            infos[name] = info
            data = zin.read(name)
            ext = Path(name).suffix.lower()
            if ext in {'.xhtml', '.opf', '.ncx', '.css'}:
                try:
                    text = data.decode('utf-8')
                except UnicodeDecodeError:
                    logging.warning(
                        "Failed to decode %s with UTF-8; using replacement", name
                    )
                    text = data.decode('utf-8', errors='replace')
                new_parts = []
                done = set(progress.get(name, []))
                total = sum(1 for _ in split_text(text))
                for idx, chunk in enumerate(split_text(text)):
                    if idx in done:
                        new_parts.append(chunk)
                        continue
                    try:
                        result = ask_gpt(
                            bot,
                            name,
                            idx + 1,
                            total,
                            chunk,
                            tool,
                            max_language_failures=max_language_failures,
                            max_read_failures=max_read_failures,
                        )
                    except LoginRequiredError as e:
                        raise SystemExit(str(e))
                    new_parts.append(result)
                    processed_chunks += 1
                    if getattr(result, 'failed', False):
                        total_failures += 1
                        if total_failures > max_total_failures:
                            raise SystemExit(
                                "Maximum total failures exceeded after "
                                f"processing {processed_chunks} chunks"
                            )
                    done.add(idx)
                    progress[name] = sorted(done)
                    with open(progress_path, 'w') as f:
                        json.dump(progress, f)
                text = ''.join(new_parts)
                data = text.encode('utf-8')
            contents[name] = data

    with zipfile.ZipFile(output_path, 'w') as zout:
        for name in filenames:
            info = infos[name]
            zout.writestr(info, contents[name], compress_type=info.compress_type)

    try:
        result = subprocess.run(
            ['epubcheck', output_path], capture_output=True, text=True
        )
    except FileNotFoundError:
        raise SystemExit(
            'epubcheck executable not found; install from '
            'https://github.com/w3c/epubcheck'
        )
    if result.returncode != 0:
        raise SystemExit(result.stdout + result.stderr)

    if progress_path.exists():
        progress_path.unlink()


if __name__ == '__main__':
    main()
