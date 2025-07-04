# BookEase Formatter

[![CI](https://github.com/<owner>/BookEase---Formatter/actions/workflows/ci.yml/badge.svg)](https://github.com/<owner>/BookEase---Formatter/actions/workflows/ci.yml)

BookEase Formatter uses ChatGPT to proofread and clean up EPUB files.

## Quick start
1. Create a virtual environment and activate it:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use .venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the formatter:
   ```bash
   python -m src.main
   ```

## Usage

### Hot keys
| Shortcut | Action |
|----------|--------|
| **Ctrl+Shift+E** | Choose an EPUB and output location |
| **Ctrl+Shift+Q** | Exit the application |
### Adding new EPUBs

Press **Ctrl+Shift+E** while the app is running and pick your EPUB.
You can also run the CLI directly:
```bash
python -m src.process_epub --input mybook.epub --output cleaned.epub
```

### Environment variables

The application searches for a ChatGPT Desktop window whose title contains
`ChatGPT` and caches the handle once found. The search pattern can be
customised with a regular expression. You can override the defaults with the
following variables:

- `CHATGPT_EXE` – full path to `ChatGPT.exe`.
- `CHATGPT_WINDOW_TITLE` – substring or regular expression used to locate the
  ChatGPT window.

Once detected, the window handle is reused so changing the title later will not
interrupt automation.

BookEase will automatically start ChatGPT Desktop if it's not already
running, so you can safely close the app between runs.

## Development workflow
1. Take or open a Codex task for the change you want to make.
2. Run `git pull` to ensure `main` is up to date.
3. Commit your changes on the `main` branch.
4. `git push` to run the CI tests and open a PR.
