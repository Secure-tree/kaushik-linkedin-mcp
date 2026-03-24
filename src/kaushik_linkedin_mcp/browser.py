  """
browser.py — Browser session manager
Handles Playwright browser lifecycle, LinkedIn authentication,
and persistent session storage so login is only needed once.
"""

import os
import asyncio
import logging
from pathlib import Path
from typing import Optional

from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    Playwright,
)
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

SESSION_DIR = Path(os.getenv("SESSION_DIR", "~/.kaushik-linkedin-mcp/session")).expanduser()
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
SLOW_MO = int(os.getenv("SLOW_MO", "0"))
TIMEOUT = int(os.getenv("TIMEOUT", "15000"))

LINKEDIN_FEED = "https://www.linkedin.com/feed/"


class BrowserSession:
    """
    Manages a persistent Playwright browser session for LinkedIn.
    Saves cookies and localStorage after login so subsequent runs
    skip the login screen entirely.
    """

    def __init__(self):
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

    async def start(self) -> "BrowserSession":
        """Launch browser and restore session if available."""
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=HEADLESS,
            slow_mo=SLOW_MO,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        context_args = {
            "viewport": {"width": 1280, "height": 720},
            "user_agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
        }
        storage_file = SESSION_DIR / "storage.json"
        if storage_file.exists():
            context_args["storage_state"] = str(storage_file)
        self._context = await self._browser.new_context(**context_args)
        self._context.set_default_timeout(TIMEOUT)
        self._page = await self._context.new_page()
        return self

    async def stop(self):
        """Close browser and save session."""
        if self._context:
            await self._save_session()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def login(self) -> str:
        """Open a visible browser window for manual LinkedIn login."""
        login_playwright = await async_playwright().start()
        login_browser = await login_playwright.chromium.launch(headless=False, slow_mo=200)
        login_context = await login_browser.new_context(viewport={"width": 1280, "height": 720})
        login_page = await login_context.new_page()
        await login_page.goto("https://www.linkedin.com/login")
        print("\n✅ Browser opened. Please log in to LinkedIn.")
        print("   Waiting for you to reach the feed page...")
        try:
            await login_page.wait_for_url("**/feed/**", timeout=120000)
        except Exception:
            await login_page.wait_for_url("**/in/**", timeout=30000)
        SESSION_DIR.mkdir(parents=True, exist_ok=True)
        storage_file = SESSION_DIR / "storage.json"
        await login_context.storage_state(path=str(storage_file))
        await login_browser.close()
        await login_playwright.stop()
        print(f"✅ Session saved to {storage_file}")
        return f"Login successful. Session saved to {storage_file}"

    async def logout(self) -> str:
        """Clear saved session data."""
        storage_file = SESSION_DIR / "storage.json"
        if storage_file.exists():
            storage_file.unlink()
            return "Session cleared. You will need to log in again."
        return "No active session found."

    async def status(self) -> dict:
        """Check if current session is valid by visiting LinkedIn."""
        storage_file = SESSION_DIR / "storage.json"
        if not storage_file.exists():
            return {"status": "No session", "authenticated": False}
        try:
            await self._page.goto(LINKEDIN_FEED, wait_until="domcontentloaded")
            url = self._page.url
            if "feed" in url or "/in/" in url:
                return {"status": "Valid", "authenticated": True, "url": url}
            elif "login" in url or "authwall" in url:
                return {"status": "Expired/Invalid", "authenticated": False}
            else:
                return {"status": "Unknown", "authenticated": False, "url": url}
        except Exception as e:
            return {"status": f"Error: {str(e)}", "authenticated": False}

    async def goto(self, url: str) -> Page:
        await self._page.goto(url, wait_until="domcontentloaded")
        await self._page.wait_for_timeout(1500)
        return self._page

    async def get_page(self) -> Page:
        return self._page

    async def _save_session(self):
        SESSION_DIR.mkdir(parents=True, exist_ok=True)
        storage_file = SESSION_DIR / "storage.json"
        await self._context.storage_state(path=str(storage_file))


_session: Optional[BrowserSession] = None


async def get_session() -> BrowserSession:
    """Get or create the global browser session."""
    global _session
    if _session is None:
        _session = await BrowserSession().start()
    return _session
