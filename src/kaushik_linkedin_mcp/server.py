"""
server.py — Main FastMCP server entry point
Registers all LinkedIn tools and handles CLI commands:
  --login   : Open browser for LinkedIn authentication
  --logout  : Clear saved session
  --status  : Check if session is active
  (default) : Start MCP server
"""

import os
import sys
import asyncio
import logging
from typing import Optional, Literal

from fastmcp import FastMCP
from dotenv import load_dotenv

from .browser import BrowserSession, get_session
from .tools.profile import scrape_profile
from .tools.jobs import search_jobs, get_job_details
from .tools.posts import create_post
from .tools.search import search_people, get_company_profile

load_dotenv()

log_level = os.getenv("LOG_LEVEL", "WARNING").upper()
logging.basicConfig(level=getattr(logging, log_level, logging.WARNING))
logger = logging.getLogger(__name__)

mcp = FastMCP(
    name="kaushik-linkedin-mcp",
    instructions=(
        "LinkedIn MCP server built from scratch by Kaushik Muthukumaran. "
        "Tools: get_person_profile, search_linkedin_people, search_linkedin_jobs, "
        "get_linkedin_job_details, get_linkedin_company, publish_linkedin_post, "
        "check_session_status, close_browser. "
        "Requires --login before first use."
    ),
)


@mcp.tool()
async def get_person_profile(
    linkedin_username: str,
    sections: Optional[list[str]] = None,
) -> dict:
    """
    Get a LinkedIn profile by username.
    Sections: 'main', 'experience', 'education', 'skills', 'posts', 'contact'
    Default: ['main', 'experience', 'education']
    """
    if sections is None:
        sections = ["main", "experience", "education"]
    session = await get_session()
    page = await session.get_page()
    return await scrape_profile(page, linkedin_username, sections)


@mcp.tool()
async def search_linkedin_people(
    keywords: str,
    location: str = "",
    max_results: int = 10,
) -> dict:
    """Search for LinkedIn profiles by keywords and optional location."""
    session = await get_session()
    page = await session.get_page()
    return await search_people(page, keywords, location, max_results)


@mcp.tool()
async def search_linkedin_jobs(
    keywords: str,
    location: str = "",
    date_posted: Optional[Literal["past_hour", "past_24_hours", "past_week", "past_month"]] = None,
    experience_level: Optional[Literal["entry", "associate", "mid_senior", "director", "executive"]] = None,
    job_type: Optional[Literal["full_time", "part_time", "contract", "temporary", "internship"]] = None,
    work_type: Optional[Literal["on_site", "remote", "hybrid"]] = None,
    easy_apply: bool = False,
    max_pages: int = 1,
) -> dict:
    """Search LinkedIn jobs with optional filters."""
    session = await get_session()
    page = await session.get_page()
    return await search_jobs(
        page, keywords, location,
        date_posted or "", experience_level or "",
        job_type or "", work_type or "",
        easy_apply, max_pages,
    )


@mcp.tool()
async def get_linkedin_job_details(job_id: str) -> dict:
    """Get full details of a LinkedIn job posting by job ID."""
    session = await get_session()
    page = await session.get_page()
    return await get_job_details(page, job_id)


@mcp.tool()
async def get_linkedin_company(
    company_name: str,
    sections: Optional[list[str]] = None,
) -> dict:
    """Get a LinkedIn company profile. Sections: 'about', 'posts', 'jobs'"""
    if sections is None:
        sections = ["about"]
    session = await get_session()
    page = await session.get_page()
    return await get_company_profile(page, company_name, sections)


@mcp.tool()
async def publish_linkedin_post(text: str) -> dict:
    """Publish a post to LinkedIn. Use \\n for line breaks."""
    session = await get_session()
    page = await session.get_page()
    return await create_post(page, text)


@mcp.tool()
async def check_session_status() -> dict:
    """Check if the LinkedIn session is active and authenticated."""
    storage_file = os.path.expanduser("~/.kaushik-linkedin-mcp/session/storage.json")
    if not os.path.exists(storage_file):
        return {"status": "No session", "authenticated": False, "message": "Run --login to authenticate"}
    session = await get_session()
    return await session.status()


@mcp.tool()
async def close_browser() -> str:
    """Close the Playwright browser to free up memory."""
    from . import browser as _browser_module
    if _browser_module._session:
        await _browser_module._session.stop()
        _browser_module._session = None
        return "Browser closed successfully."
    return "No active browser session."


def main():
    """
    CLI entry point:
        kaushik-linkedin-mcp              → Start MCP server (stdio)
        kaushik-linkedin-mcp --login      → Authenticate with LinkedIn
        kaushik-linkedin-mcp --logout     → Clear saved session
        kaushik-linkedin-mcp --status     → Check session status
        kaushik-linkedin-mcp --transport streamable-http → HTTP server
    """
    args = sys.argv[1:]
    transport = os.getenv("TRANSPORT", "stdio")

    if "--login" in args:
        async def do_login():
            result = await BrowserSession().login()
            print(result)
        asyncio.run(do_login())
        return

    if "--logout" in args:
        async def do_logout():
            result = await BrowserSession().logout()
            print(result)
        asyncio.run(do_logout())
        return

    if "--status" in args:
        async def do_status():
            session = await BrowserSession().start()
            result = await session.status()
            await session.stop()
            for k, v in result.items():
                print(f"  {k.capitalize()}: {v}")
        asyncio.run(do_status())
        return

    if "--transport" in args:
        idx = args.index("--transport")
        if idx + 1 < len(args):
            transport = args[idx + 1]

    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))

    if "--host" in args:
        idx = args.index("--host")
        if idx + 1 < len(args):
            host = args[idx + 1]

    if "--port" in args:
        idx = args.index("--port")
        if idx + 1 < len(args):
            port = int(args[idx + 1])

    if transport == "streamable-http":
        mcp.run(transport="streamable-http", host=host, port=port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
