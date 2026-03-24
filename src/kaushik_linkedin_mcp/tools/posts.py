"""
tools/posts.py — LinkedIn post creation tools

SECURITY: Post text is passed as a CDP argument to page.evaluate —
never string-interpolated into JavaScript to prevent template literal injection.
"""

import logging
from playwright.async_api import Page

logger = logging.getLogger(__name__)


async def create_post(page: Page, text: str) -> dict:
    """
    Create and publish a new LinkedIn post.

    Args:
        page: Active Playwright page
        text: Post content (plain text, supports line breaks)

    Returns:
        Status dict with success/failure info
    """
    await page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")
    await page.wait_for_timeout(2000)

    try:
        await page.click('text=Start a post')
    except Exception:
        start_post = await page.query_selector('[placeholder="Start a post"]')
        if start_post:
            await start_post.click()

    await page.wait_for_timeout(1500)

    editor = (
        await page.query_selector('.ql-editor') or
        await page.query_selector('[contenteditable="true"][data-placeholder]')
    )

    if not editor:
        return {"success": False, "error": "Could not find post editor"}

    await editor.click()
    await page.wait_for_timeout(500)

    # SECURE: Pass text as CDP argument — never f-string inject into JS
    result = await page.evaluate(
        """(postText) => {
            const editor = document.querySelector('.ql-editor') ||
                           document.querySelector('[contenteditable="true"]');
            if (!editor) return 'editor not found';
            editor.focus();
            document.execCommand('insertText', false, postText);
            return 'ok - ' + editor.innerText.length + ' chars';
        }""",
        text,
    )

    if "not found" in str(result):
        return {"success": False, "error": "Post editor not found after opening"}

    await page.wait_for_timeout(500)

    post_btn = (
        await page.query_selector('.share-actions__primary-action') or
        await page.query_selector('button.share-box_actions button:last-child')
    )
    if not post_btn:
        buttons = await page.query_selector_all('button')
        for btn in buttons:
            txt = await btn.inner_text()
            if txt.strip() == 'Post':
                post_btn = btn
                break

    if not post_btn:
        return {
            "success": False,
            "error": "Post button not found. Text was entered but not published.",
            "text_entered": text[:100],
        }

    await post_btn.click()
    await page.wait_for_timeout(2000)

    return {
        "success": True,
        "message": "Post published successfully",
        "text_preview": text[:150] + ("..." if len(text) > 150 else ""),
    }
