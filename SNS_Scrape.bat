@echo off
cd /d "%~dp0"
call venv\Scripts\activate.bat
python gui\tkinter_app.py
pause