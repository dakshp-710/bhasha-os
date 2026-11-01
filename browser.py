import subprocess
import urllib.parse

class BrowserController:
    """
    Lightweight browser controller using macOS 'open' command.
    No Playwright, no Chromium download — just opens your default browser.
    """

    def open_url(self, url: str) -> str:
        if not url.startswith("http"):
            url = "https://" + url
        subprocess.Popen(["open", url])
        return f"Opened in browser: {url}"

    def search(self, query: str) -> str:
        encoded = urllib.parse.quote_plus(query)
        url = f"https://www.google.com/search?q={encoded}"
        subprocess.Popen(["open", url])
        return f"Searched Google for: {query}"

    def download(self, url: str, save_as: str) -> str:
        import os
        save_path = os.path.expanduser(f"~/Downloads/{save_as}")
        result = subprocess.run(["curl", "-L", "-o", save_path, url],
                                capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return f"Downloaded to ~/Downloads/{save_as}"
        return f"Download failed: {result.stderr[:100]}"

    def close(self):
        pass  # nothing to close
