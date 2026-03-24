"""
tools/profile.py — LinkedIn profile scraping tools
"""

import logging
from playwright.async_api import Page

logger = logging.getLogger(__name__)

LINKEDIN_BASE = "https://www.linkedin.com"


async def scrape_profile(page: Page, username: str, sections: list) -> dict:
    url = f"{LINKEDIN_BASE}/in/{username}/"
    await page.goto(url, wait_until="domcontentloaded")
    await page.wait_for_timeout(2000)

    result = {"url": url, "username": username}

    if "main" in sections or not sections:
        result["main"] = await _scrape_main(page)
    if "experience" in sections:
        result["experience"] = await _scrape_experience(page)
    if "education" in sections:
        result["education"] = await _scrape_education(page)
    if "skills" in sections:
        result["skills"] = await _scrape_skills(page)
    if "posts" in sections:
        result["posts"] = await _scrape_posts(page, username)
    if "contact" in sections:
        result["contact"] = await _scrape_contact(page, username)

    return result


async def _scrape_main(page: Page) -> dict:
    try:
        return await page.evaluate("""() => {
            const g = (sel) => { const el = document.querySelector(sel); return el ? el.innerText.trim() : null; };
            return {
                name: g('h1.text-heading-xlarge') || g('.pv-text-details__left-panel h1'),
                headline: g('.text-body-medium.break-words'),
                location: g('.text-body-small.inline.t-black--light.break-words'),
                connections: g('.pvs-header__subtitle span'),
                about: g('#about ~ .pvs-list .visually-hidden'),
            };
        }""")
    except Exception as e:
        logger.error("Error scraping main: %s", e)
        return {}


async def _scrape_experience(page: Page) -> list:
    try:
        await page.evaluate("""() => {
            const el = document.getElementById('experience');
            if (el) el.scrollIntoView({ behavior: 'smooth' });
        }""")
        await page.wait_for_timeout(1000)
        return await page.evaluate("""() => {
            const section = document.getElementById('experience');
            if (!section) return [];
            const items = [];
            section.parentElement.querySelectorAll('.pvs-list__paged-list-item').forEach(entry => {
                const title = entry.querySelector('.t-bold span[aria-hidden]')?.innerText?.trim();
                const company = entry.querySelector('.t-14.t-normal span[aria-hidden]')?.innerText?.trim();
                const dates = entry.querySelector('.t-14.t-normal.t-black--light span[aria-hidden]')?.innerText?.trim();
                if (title) items.push({ title, company, dates });
            });
            return items;
        }""")
    except Exception as e:
        logger.error("Error scraping experience: %s", e)
        return []


async def _scrape_education(page: Page) -> list:
    try:
        await page.evaluate("""() => {
            const el = document.getElementById('education');
            if (el) el.scrollIntoView({ behavior: 'smooth' });
        }""")
        await page.wait_for_timeout(1000)
        return await page.evaluate("""() => {
            const section = document.getElementById('education');
            if (!section) return [];
            const items = [];
            section.parentElement.querySelectorAll('.pvs-list__paged-list-item').forEach(entry => {
                const school = entry.querySelector('.t-bold span[aria-hidden]')?.innerText?.trim();
                const degree = entry.querySelector('.t-14.t-normal span[aria-hidden]')?.innerText?.trim();
                const dates = entry.querySelector('.t-14.t-normal.t-black--light span[aria-hidden]')?.innerText?.trim();
                if (school) items.push({ school, degree, dates });
            });
            return items;
        }""")
    except Exception as e:
        logger.error("Error scraping education: %s", e)
        return []


async def _scrape_skills(page: Page) -> list:
    try:
        await page.evaluate("""() => {
            const el = document.getElementById('skills');
            if (el) el.scrollIntoView({ behavior: 'smooth' });
        }""")
        await page.wait_for_timeout(1000)
        return await page.evaluate("""() => {
            const section = document.getElementById('skills');
            if (!section) return [];
            const skills = [];
            section.parentElement.querySelectorAll('.pvs-list__paged-list-item').forEach(entry => {
                const name = entry.querySelector('.t-bold span[aria-hidden]')?.innerText?.trim();
                if (name) skills.push(name);
            });
            return skills;
        }""")
    except Exception as e:
        logger.error("Error scraping skills: %s", e)
        return []


async def _scrape_posts(page: Page, username: str) -> list:
    try:
        await page.goto(
            f"https://www.linkedin.com/in/{username}/recent-activity/all/",
            wait_until="domcontentloaded"
        )
        await page.wait_for_timeout(2500)
        return await page.evaluate("""() => {
            const posts = [];
            document.querySelectorAll('.occludable-update.ember-view').forEach((item, i) => {
                if (i >= 10) return;
                const text = item.querySelector('.feed-shared-update-v2__description-wrapper')?.innerText?.trim();
                const time = item.querySelector('time')?.getAttribute('datetime');
                const reactions = item.querySelector('.social-details-social-counts__reactions-count')?.innerText?.trim();
                if (text) posts.push({ text: text.slice(0, 300), time, reactions });
            });
            return posts;
        }""")
    except Exception as e:
        logger.error("Error scraping posts: %s", e)
        return []


async def _scrape_contact(page: Page, username: str) -> dict:
    try:
        await page.goto(
            f"https://www.linkedin.com/in/{username}/overlay/contact-info/",
            wait_until="domcontentloaded"
        )
        await page.wait_for_timeout(1500)
        return await page.evaluate("""() => {
            const g = (sel) => { const el = document.querySelector(sel); return el ? el.innerText.trim() : null; };
            return {
                email: g('.ci-email .pv-contact-info__contact-link'),
                phone: g('.ci-phone .pv-contact-info__contact-link'),
                linkedin: g('.ci-vanity-url .pv-contact-info__contact-link'),
                website: g('.ci-websites .pv-contact-info__contact-link'),
            };
        }""")
    except Exception as e:
        logger.error("Error scraping contact: %s", e)
        return {}
