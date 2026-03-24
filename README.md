# 🔗 kaushik-linkedin-mcp

> **A personal LinkedIn MCP server — built from scratch.**
> Not a fork. Not a clone. Written by Kaushik Muthukumaran.

[![Python](https://img.shields.io/badge/Python-3.12+-blue)](https://python.org)
[![FastMCP](https://img.shields.io/badge/FastMCP-2.0+-green)](https://gofastmcp.com)
[![Playwright](https://img.shields.io/badge/Playwright-1.44+-orange)](https://playwright.dev)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![Security](https://img.shields.io/badge/Security-Audited-brightgreen)](#security)

This MCP server connects **Claude AI** directly to **LinkedIn** using browser automation.
It gives Claude 8 tools to read profiles, search people and jobs, get company data,
publish posts, edit your profile, and manage sessions — all from a conversation with Claude.

---

## 📖 Table of Contents

1. [What You Can Do With This](#what-you-can-do-with-this)
2. [How to Clone and Run It](#how-to-clone-and-run-it)
3. [Project Structure](#project-structure)
4. [How It Works](#how-it-works)
5. [Tools Reference](#tools-reference)
6. [For People Cloning This Repo](#for-people-cloning-this-repo)
7. [Security](#security)
8. [Troubleshooting](#troubleshooting)
9. [Author](#author)

---

## 🚀 What You Can Do With This

Once connected to Claude, you can have natural conversations that do real LinkedIn actions.

---

### ✏️ Edit Your LinkedIn Profile By Just Telling Claude

**Method 1 — Tell Claude your details in chat:**

> *"Change my headline to: Security Engineer | Zero Trust | CrowdStrike | 14K+ Endpoints"*
> *"Add a new job: Security Engineer at MasTec, promoted after 1 year"*
> *"Update my Sankara Nethralaya role to focus on vulnerability assessments and OSINT"*

Claude opens Chrome, finds the right field, types your content, and saves it.

**Method 2 — Upload your resume and ask Claude to sync it:**

> *"Here's my updated resume — update my LinkedIn to match it"*

Claude reads every section, compares it to your LinkedIn, and edits each section one by one.
Supports: `.pdf`, `.docx`, `.txt`

**Method 3 — Targeted corrections mid-conversation:**

> *"Split my MasTec role into two entries at August 2025"*
> *"Add OSINT and CyberArk to my skills"*
> *"Move Sankara Nethralaya from Part-time to Full-time"*

---

### 👤 Profile Intelligence

> *"Pull Kaushik's full LinkedIn profile including experience and skills"*
> *"Show me their recent posts and engagement"*

Reads: name, headline, location, connections, about, full experience, education, skills, posts, contact info.

---

### 🔍 People Search

> *"Find Security Engineers at CrowdStrike in Pennsylvania"*
> *"Search for CISOs in the healthcare industry"*

Returns: name, headline, location, username, profile URL. Max 100 results per call.

---

### 💼 Job Search & Research

> *"Find Senior Security Engineer jobs in Pennsylvania posted this week"*
> *"Show me remote Zero Trust architect roles — mid-senior level only"*
> *"What's the salary range for this CrowdStrike job?"*

Full LinkedIn job search: date posted, experience level, job type, work arrangement, Easy Apply.

---

### 🏢 Company Research

> *"What does CrowdStrike's LinkedIn page say about them?"*
> *"Show me MasTec's recent posts and engagement numbers"*
> *"What roles is Microsoft hiring for right now?"*

Returns: about, industry, size, headquarters, recent posts with reactions, open roles.

---

### 📢 Post Publishing

> *"Publish my vulnerability management post to LinkedIn"*
> *"Post this Zero Trust insight with these hashtags"*

Navigates to feed, opens composer, injects text securely, clicks Post, confirms success.

---

### 🤖 Combined Power Workflows

> *"Search for Senior Security Engineer jobs at CrowdStrike, get the top 3 JDs, and tell me exactly how my resume matches each one"*

> *"Find Security Engineers at my target companies and draft a personalised connection message for each one based on their background"*

> *"Write and publish a post about today's Rapid7 CVE findings — under 200 words with 5 hashtags"*

---

## 🖥️ How to Clone and Run It

### Step 1 — Install Homebrew
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
echo 'eval "$(/opt/homebrew/bin/brew shellenv zsh)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv zsh)"
```

### Step 2 — Install Node.js and Git
```bash
brew install node git
```

### Step 3 — Install uv
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
```

> ⚠️ Save the path from `which uv` — you'll need it for Claude Desktop config.

### Step 4 — Clone and Install
```bash
git clone https://github.com/Secure-tree/kaushik-linkedin-mcp
cd kaushik-linkedin-mcp
uv sync
uv run playwright install chromium
```

### Step 5 — Authenticate with LinkedIn
```bash
uv run kaushik-linkedin-mcp --login
```
A Chrome window opens. Log in to your LinkedIn. Session saves automatically.

### Step 6 — Verify Session
```bash
uv run kaushik-linkedin-mcp --status
# Status: Valid  ✅
```

### Step 7 — Connect to Claude Desktop

Open: `~/Library/Application Support/Claude/claude_desktop_config.json`

Merge this in:
```json
{
  "mcpServers": {
    "linkedin": {
      "command": "/Users/YOUR_USERNAME/.local/bin/uv",
      "args": [
        "--directory",
        "/Users/YOUR_USERNAME/kaushik-linkedin-mcp",
        "run",
        "kaushik-linkedin-mcp"
      ]
    }
  }
}
```

> ⚠️ Use the full path to `uv` from `which uv` — Claude Desktop does not inherit your terminal PATH.

Restart Claude:
```bash
pkill -f Claude && sleep 2 && open /Applications/Claude.app
```

---

## 🏗️ Project Structure

```
kaushik-linkedin-mcp/
├── pyproject.toml                      # Project config, CLI entry point, dependencies
├── .python-version                     # Pins Python 3.12
├── .env.example                        # Config template — copy to .env
├── .gitignore                          # Protects session data and .env
├── LICENSE                             # MIT
└── src/
    └── kaushik_linkedin_mcp/
        ├── __init__.py
        ├── server.py                   # FastMCP server — all 8 tools
        ├── browser.py                  # Playwright session manager
        └── tools/
            ├── profile.py              # get_person_profile
            ├── jobs.py                 # search_jobs + get_job_details
            ├── posts.py                # publish_linkedin_post
            └── search.py              # search_people + get_company_profile
```

---

## ⚙️ How It Works

```
You (in Claude chat)
        │
        │  "Search for Security Engineer jobs in Pennsylvania"
        ▼
Claude Desktop
        │  stdio (local process)
        ▼
kaushik-linkedin-mcp (Python / FastMCP)
        │  Playwright browser automation
        ▼
Chromium (headless, on your Mac)
        │  HTTPS — your authenticated session
        ▼
LinkedIn.com → returns structured JSON back to Claude
```

> **Note for cloners:** Session saves to `~/.kaushik-linkedin-mcp/session/storage.json` on YOUR machine. The author has zero access to your account.

---

## 🧰 Tools Reference

| Tool | Parameters |
|------|-----------|
| `get_person_profile` | `linkedin_username`, `sections` (main/experience/education/skills/posts/contact) |
| `search_linkedin_people` | `keywords`, `location`, `max_results` (1–100) |
| `search_linkedin_jobs` | `keywords`, `location`, `date_posted`, `experience_level`, `job_type`, `work_type`, `easy_apply`, `max_pages` |
| `get_linkedin_job_details` | `job_id` |
| `get_linkedin_company` | `company_name`, `sections` (about/posts/jobs) |
| `publish_linkedin_post` | `text` |
| `check_session_status` | — |
| `close_browser` | — |

---

## 👥 For People Cloning This Repo

When you clone and run this, you log into **your own LinkedIn** — not the author's.

| Thing | Change Required |
|-------|----------------|
| `--login` step | Log in with YOUR LinkedIn credentials |
| Claude Desktop config | Update path to YOUR clone location and `uv` path |
| `.env` | Optional — defaults work for most setups |
| `pyproject.toml` author | Leave as-is — this is the author's name |

**Quick start:**
```bash
git clone https://github.com/Secure-tree/kaushik-linkedin-mcp
cd kaushik-linkedin-mcp
uv sync
uv run playwright install chromium
uv run kaushik-linkedin-mcp --login
uv run kaushik-linkedin-mcp --status
```

---

## 🔐 Security

| Check | Status |
|-------|--------|
| No hardcoded credentials | ✅ |
| No JS template literal injection | ✅ User values passed via CDP args |
| Input validation | ✅ max_results clamped 1–100 |
| Session stored outside repo | ✅ `~/.kaushik-linkedin-mcp/` |
| `.env` never committed | ✅ In .gitignore |
| No shell/subprocess calls | ✅ |
| No 3rd party API calls | ✅ Only linkedin.com |
| Local stdio communication | ✅ No network exposure |

---

## 🔧 Troubleshooting

**No LinkedIn tools in Claude**
→ Use full `uv` path in config: `which uv` → `/Users/YOU/.local/bin/uv`

**Status: Expired/Invalid**
→ `uv run kaushik-linkedin-mcp --logout && uv run kaushik-linkedin-mcp --login`

**`npm install` fails**
→ This is Python. Use `uv sync` not npm install.

**Config has two `{}` blocks**
→ Merge into one root object: `{ "preferences": {...}, "mcpServers": {...} }`

---

## ⚡ Quick Reference

```bash
# Setup
git clone https://github.com/Secure-tree/kaushik-linkedin-mcp
cd kaushik-linkedin-mcp && uv sync
uv run playwright install chromium
uv run kaushik-linkedin-mcp --login
uv run kaushik-linkedin-mcp --status

# Restart Claude after config changes
pkill -f Claude && sleep 2 && open /Applications/Claude.app

# Re-authenticate
uv run kaushik-linkedin-mcp --logout && uv run kaushik-linkedin-mcp --login
```

---

## 👤 Author

**Kaushik Muthukumaran**
Security Engineer | MasTec Network Solutions | King of Prussia, PA

- 🔗 [LinkedIn](https://www.linkedin.com/in/kaushik-muthukumaran-a901612a2)
- 📧 kaushikrmk01@gmail.com
- 🏅 CompTIA Network+ Certified
- 🔬 Research: AI-Driven Threat Detection · Zero Trust · ML Risk Scoring

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

*Built with Claude AI (Anthropic) · FastMCP · Playwright · Python 3.12*
