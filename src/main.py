"""Keyboard shortcuts for running the EPUB formatter."""

import sys

import keyboard
import tkinter as tk
from tkinter import filedialog

from src.automation import ChatGPTAutomation
from src.process_epub import main as process_epub


def choose_epub() -> None:
    """Open file dialogs to process an EPUB."""
    root = tk.Tk()
    root.withdraw()

    in_path = filedialog.askopenfilename(
        title="Select EPUB", filetypes=[("EPUB files", "*.epub")]
    )
    if not in_path:
        return

    out_path = filedialog.asksaveasfilename(
        title="Save Processed EPUB",
        defaultextension=".epub",
        filetypes=[("EPUB files", "*.epub")],
    )
    if not out_path:
        return

    process_epub(in_path, out_path)


def quit_program() -> None:
    """Unhook hotkeys and exit."""
    keyboard.unhook_all_hotkeys()
    sys.exit(0)

if __name__ == "__main__":
    bot = ChatGPTAutomation("You are a helpful assistant.")
    bot.bootstrap()

    keyboard.add_hotkey("ctrl+shift+e", choose_epub)
    keyboard.add_hotkey("ctrl+shift+q", quit_program)

    keyboard.wait()
