import subprocess
import os
import platform
import webbrowser
from browser import BrowserController

browser = BrowserController()

def execute(action: dict) -> str:
    """Route an action dict to the right handler. Returns a result string."""
    kind = action.get("action", "")

    if kind == "shell":
        return _run_shell(action.get("command", ""))

    elif kind == "browser_open":
        return browser.open_url(action.get("url", ""))

    elif kind == "browser_search":
        return browser.search(action.get("query", ""))

    elif kind == "browser_download":
        return browser.download(action.get("url", ""), action.get("save_as", "download"))

    elif kind == "open_app":
        return _open_app(action.get("app", ""))

    elif kind == "open_folder":
        return _open_folder(action.get("path", "~"))

    elif kind == "answer":
        return action.get("text", "")

    else:
        return f"Unknown action: {kind}"


def _run_shell(command: str) -> str:
    """Run a shell command and return stdout or stderr."""
    # Safety: block obviously destructive commands
    blocked = ["rm -rf", "rmdir", "format", "mkfs", "dd if=", "shutdown", "reboot", ":(){"]
    for b in blocked:
        if b in command.lower():
            return f"Blocked: '{b}' is not allowed for safety."

    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=10
        )
        output = result.stdout.strip() or result.stderr.strip()
        return output if output else "Command ran with no output."
    except subprocess.TimeoutExpired:
        return "Command timed out after 10 seconds."
    except Exception as e:
        return f"Error running command: {e}"


def _open_app(app_name: str) -> str:
    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.Popen(["open", "-a", app_name])
            return f"Opened {app_name}."
        elif system == "Linux":
            subprocess.Popen([app_name.lower()])
            return f"Launched {app_name}."
        elif system == "Windows":
            os.startfile(app_name)
            return f"Opened {app_name}."
    except Exception as e:
        return f"Could not open {app_name}: {e}"


def _open_folder(path: str) -> str:
    path = os.path.expanduser(path)
    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.Popen(["open", path])
        elif system == "Linux":
            subprocess.Popen(["xdg-open", path])
        elif system == "Windows":
            subprocess.Popen(["explorer", path])
        return f"Opened folder: {path}"
    except Exception as e:
        return f"Could not open folder: {e}"
