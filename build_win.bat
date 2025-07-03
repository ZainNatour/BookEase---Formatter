@echo off
py -m pip install pyinstaller
py -m PyInstaller --onefile src\main.py --name BookEaseFormatter
