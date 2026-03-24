"""
tools/jobs.py — LinkedIn job search and job detail tools
"""

import logging
from urllib.parse import urlencode
from playwright.async_api import Page

logger = logging.getLogger(__name__)

DATE_FILTERS = {"past_hour": "r3600", "past_24_hours": "r86400", "past_week": "r604800", "past_month": "r2592000"}
EXPERIENCE_FILTERS = {"entry": "1", "associate": "2", "mid_senior": "3", "director": "4", "executive": "5"}
JOB_TYPE_FILTERS = {"full_time": "F", "part_time": "P", "contract": "C", "temporary": "T", "internship": "I", "other": "O"}
WORK_TYPE_FILTERS = {"on_site": "1", "remote": "2", "hybrid": "3"}


async def search_jobs(
    page: Page,
    keywords: str,
    location: str = "",
    date_posted: str = "",
    experience_level: str = "",
    job_type: str = "",
    work_type: str = "",
    easy_apply: bool = False,
    max_pages: int = 1,
) -> dict:
    params = {"keywords": keywords}
    if location:
        params["location"] = location
    if date_posted in DATE_FILTERS:
        params["f_TPR"] = DATE_FILTERS[date_posted]
    if experience_level in EXPERIENCE_FILTERS:
        params["f_E"] = EXPERIENCE_FILTERS[experience_level]
    if job_type in JOB_TYPE_FILTERS:
        params["f_JT"] = JOB_TYPE_FILTERS[job_type]
    if work_type in WORK_TYPE_FILTERS:
        params["f_WT"] = WORK_TYPE_FILTERS[work_type]
    if easy_apply:
        params["f_LF"] = "f_AL"

    search_url = f"https://www.linkedin.com/jobs/search/?{urlencode(params)}"
    await page.goto(search_url, wait_until="domcontentloaded")
    await page.wait_for_timeout(2500)

    all_jobs = []
    for page_num in range(max_pages):
        if page_num > 0:
            offset_params = {**params, "start": str(page_num * 25)}
            await page.goto(
                f"https://www.linkedin.com/jobs/search/?{urlencode(offset_params)}",
                wait_until="domcontentloaded"
            )
            await page.wait_for_timeout(2000)

        jobs = await page.evaluate("""() => {
            const results = [];
            document.querySelectorAll('.jobs-search__results-list li').forEach(item => {
                const title = item.querySelector('.base-search-card__title')?.innerText?.trim();
                const company = item.querySelector('.base-search-card__subtitle')?.innerText?.trim();
                const location = item.querySelector('.job-search-card__location')?.innerText?.trim();
                const listed = item.querySelector('.job-search-card__listdate')?.getAttribute('datetime');
                const link = item.querySelector('a.base-card__full-link')?.href;
                const jobId = link ? link.match(/view\/(\d+)/)?.[1] : null;
                if (title) results.push({ title, company, location, listed, link, job_id: jobId });
            });
            return results;
        }""")
        all_jobs.extend(jobs)

    return {
        "search_url": search_url,
        "keywords": keywords,
        "location": location,
        "total_found": len(all_jobs),
        "jobs": all_jobs,
    }


async def get_job_details(page: Page, job_id: str) -> dict:
    url = f"https://www.linkedin.com/jobs/view/{job_id}/"
    await page.goto(url, wait_until="domcontentloaded")
    await page.wait_for_timeout(2000)
    try:
        show_more = await page.query_selector(".jobs-description__footer-button")
        if show_more:
            await show_more.click()
            await page.wait_for_timeout(500)
    except Exception:
        pass

    return await page.evaluate("""() => {
        const g = (sel) => { const el = document.querySelector(sel); return el ? el.innerText.trim() : null; };
        const title = g('.job-details-jobs-unified-top-card__job-title h1') || g('.jobs-unified-top-card__job-title');
        const company = g('.job-details-jobs-unified-top-card__company-name') || g('.jobs-unified-top-card__company-name');
        const location = g('.job-details-jobs-unified-top-card__bullet') || g('.jobs-unified-top-card__bullet');
        const posted = g('.job-details-jobs-unified-top-card__posted-date');
        const salary = g('.job-details-jobs-unified-top-card__job-insight--highlight') || g('.compensation__salary');
        const description = g('.jobs-description__content') || g('.jobs-description-content__text');
        const criteria = [];
        document.querySelectorAll('.description__job-criteria-item').forEach(item => {
            const label = item.querySelector('.description__job-criteria-subheader')?.innerText?.trim();
            const value = item.querySelector('.description__job-criteria-text')?.innerText?.trim();
            if (label && value) criteria.push({ label, value });
        });
        return { title, company, location, posted, salary, description: description ? description.slice(0, 3000) : null, criteria, url: window.location.href };
    }""")
