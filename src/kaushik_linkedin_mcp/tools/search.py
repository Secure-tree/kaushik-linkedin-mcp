"""
tools/search.py — LinkedIn people and company search tools

SECURITY: All user-controlled values passed to page.evaluate() are serialized
via Playwright CDP argument passing — never string-interpolated into JavaScript.
"""

import logging
from urllib.parse import urlencode
from playwright.async_api import Page

logger = logging.getLogger(__name__)


async def search_people(
    page: Page,
    keywords: str,
    location: str = "",
    max_results: int = 10,
) -> dict:
    """
    Search for LinkedIn profiles by keyword and optional location.
    max_results is clamped between 1–100 for safety.
    """
    params = {"keywords": keywords, "origin": "GLOBAL_SEARCH_HEADER"}
    if location:
        params["geoUrn"] = location

    url = f"https://www.linkedin.com/search/results/people/?{urlencode(params)}"
    await page.goto(url, wait_until="domcontentloaded")
    await page.wait_for_timeout(2500)

    # Validate and clamp — pass as CDP argument, never f-string inject
    limit = max(1, min(int(max_results), 100))

    people = await page.evaluate(
        """(limit) => {
            const results = [];
            const items = document.querySelectorAll('.reusable-search__result-container');
            items.forEach((item, i) => {
                if (i >= limit) return;
                const name = item.querySelector(
                    '.entity-result__title-text a span[aria-hidden]'
                )?.innerText?.trim();
                const headline = item.querySelector(
                    '.entity-result__primary-subtitle'
                )?.innerText?.trim();
                const location = item.querySelector(
                    '.entity-result__secondary-subtitle'
                )?.innerText?.trim();
                const profileUrl = item.querySelector(
                    '.entity-result__title-text a'
                )?.href;
                const username = profileUrl
                    ? profileUrl.match(/\/in\/([^/?]+)/)?.[1]
                    : null;
                if (name) {
                    results.push({ name, headline, location, username, profile_url: profileUrl });
                }
            });
            return results;
        }""",
        limit,
    )

    return {
        "search_url": url,
        "keywords": keywords,
        "location": location,
        "total_found": len(people),
        "people": people,
    }


async def get_company_profile(page: Page, company_name: str, sections: list) -> dict:
    search_url = f"https://www.linkedin.com/search/results/companies/?keywords={company_name}"
    await page.goto(search_url, wait_until="domcontentloaded")
    await page.wait_for_timeout(2000)

    company_url = await page.evaluate("""() => {
        const first = document.querySelector(
            '.reusable-search__result-container .entity-result__title-text a'
        );
        return first ? first.href : null;
    }""")

    if not company_url:
        return {"error": f"Company '{company_name}' not found"}

    await page.goto(company_url, wait_until="domcontentloaded")
    await page.wait_for_timeout(2000)

    result = {"url": company_url, "company_name": company_name}

    if "about" in sections or not sections:
        result["about"] = await page.evaluate("""() => {
            const g = (sel) => { const el = document.querySelector(sel); return el ? el.innerText.trim() : null; };
            return {
                name: g('.org-top-card-summary__title'),
                tagline: g('.org-top-card-summary__tagline'),
                industry: g('.org-top-card-summary-info-list__info-item:nth-child(1)'),
                size: g('.org-top-card-summary-info-list__info-item:nth-child(2)'),
                headquarters: g('.org-top-card-summary-info-list__info-item:nth-child(3)'),
                about: g('.org-about-us-organization-description__text'),
                followers: g('.org-top-card-summary-info-list .t-normal'),
            };
        }""")

    if "posts" in sections:
        await page.goto(company_url + "posts/", wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)
        result["posts"] = await page.evaluate("""() => {
            const posts = [];
            document.querySelectorAll('.feed-shared-update-v2').forEach((p, i) => {
                if (i >= 5) return;
                const text = p.querySelector('.feed-shared-update-v2__description')?.innerText?.trim();
                const reactions = p.querySelector('.social-details-social-counts__reactions-count')?.innerText?.trim();
                const time = p.querySelector('time')?.getAttribute('datetime');
                if (text) posts.push({ text: text.slice(0, 300), reactions, time });
            });
            return posts;
        }""")

    if "jobs" in sections:
        await page.goto(company_url + "jobs/", wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)
        result["jobs"] = await page.evaluate("""() => {
            const jobs = [];
            document.querySelectorAll('.jobs-job-board-list__item').forEach((j, i) => {
                if (i >= 10) return;
                const title = j.querySelector('.job-card-list__title')?.innerText?.trim();
                const location = j.querySelector('.job-card-container__metadata-item')?.innerText?.trim();
                const link = j.querySelector('a')?.href;
                const jobId = link ? link.match(/view\/(\d+)/)?.[1] : null;
                if (title) jobs.push({ title, location, job_id: jobId, link });
            });
            return jobs;
        }""")

    return result
