import click
import zipfile
import subprocess
from pathlib import Path

from utils.chunking import split_text
from src.automation import ChatGPTAutomation, read_response


def ask_gpt(bot: ChatGPTAutomation, text: str) -> str:
    bot._focus()
    bot._paste(text, hit_enter=True)
    return read_response()


@click.command()
@click.option('--input', 'input_path', required=True, type=click.Path(exists=True))
@click.option('--output', 'output_path', required=True, type=click.Path())
def main(input_path: str, output_path: str) -> None:
    bot = ChatGPTAutomation("You are a helpful assistant.")
    bot.bootstrap()

    filenames: list[str] = []
    contents: dict[str, bytes] = {}

    with zipfile.ZipFile(input_path, 'r') as zin:
        for info in zin.infolist():
            name = info.filename
            filenames.append(name)
            data = zin.read(name)
            ext = Path(name).suffix.lower()
            if ext in {'.xhtml', '.opf', '.ncx', '.css'}:
                text = data.decode('utf-8')
                new_parts = []
                for chunk in split_text(text):
                    new_parts.append(ask_gpt(bot, chunk))
                text = ''.join(new_parts)
                data = text.encode('utf-8')
            contents[name] = data

    with zipfile.ZipFile(output_path, 'w') as zout:
        zout.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)
        for name in filenames:
            if name == 'mimetype':
                continue
            zout.writestr(name, contents[name], compress_type=zipfile.ZIP_DEFLATED)

    result = subprocess.run(['epubcheck', output_path], capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(result.stdout + result.stderr)


if __name__ == '__main__':
    main()
