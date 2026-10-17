"""One-command launcher for the diagnostics app on Windows, macOS and Linux.

First run creates .venv and installs requirements.txt; later runs start at once.
Any arguments (for example --port COM5) are passed to the app.
"""
import os
import subprocess
import sys
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV = ROOT / '.venv'
PYTHON = VENV / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')


def stop(message):
    print('\n' + message + '\n', file=sys.stderr)
    sys.exit(1)


def check_python():
    if sys.version_info < (3, 9):
        stop('Python 3.9 or newer is needed. Get it from https://www.python.org/downloads/')
    try:
        import tkinter
    except ImportError:
        stop('Tkinter is missing.\n'
             '  Ubuntu/Debian: sudo apt install python3-tk\n'
             '  Fedora:        sudo dnf install python3-tkinter\n'
             '  macOS/Windows: install Python from https://www.python.org/downloads/')
    if sys.platform == 'darwin' and tkinter.TkVersion < 8.6:
        stop("This is Apple's built-in Python, whose old Tk freezes.\n"
             'Install Python from https://www.python.org/downloads/ and run:\n'
             '  python3 run_diagnostics.py')


def setup():
    if not PYTHON.exists():
        print('First run: setting up (about a minute)...', flush=True)
        try:
            venv.create(VENV, with_pip=True)
        except Exception as exc:
            stop(f'Could not create .venv ({exc}).\n  Ubuntu/Debian: sudo apt install python3-venv')
    if subprocess.run([str(PYTHON), '-c', 'import serial'], capture_output=True).returncode:
        if subprocess.run([str(PYTHON), '-m', 'pip', 'install', '-q', '--disable-pip-version-check', '-r', str(ROOT / 'requirements.txt')]).returncode:
            stop('Installing requirements failed. Check your internet connection and try again.')


if __name__ == '__main__':
    check_python()
    setup()
    sys.exit(subprocess.run([str(PYTHON), '-m', 'diagnostics', *sys.argv[1:]], cwd=ROOT).returncode)
