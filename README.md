# First Cup ☕

First Cup is an autonomous AI agent that scrapes the latest AI and developer news from Hacker News, GitHub, ArXiv, Reddit, RSS feeds, Dev.to and Product Hunt, synthesises it into a clean daily digest using Claude, and publishes it to a blog. Telegram notifications are sent automatically after each run.

---

## Stack

| Layer | Technology |
|---|---|
| Agent orchestration | LangGraph 0.2 |
| LLM | Claude Sonnet 4.6 (`claude-sonnet-4-6`) via `anthropic` |
| Scraping | feedparser, httpx, BeautifulSoup4, lxml |
| Database | Supabase (Postgres) |
| Blog | Astro 4 · static site on Vercel |
| Publishing | GitPython → GitHub → Vercel deploy hook |
| Notifications | Telegram Bot API |
| Email (Phase 2) | Resend |
| Payments (Phase 3) | Stripe |
| Scheduling | APScheduler · GitHub Actions cron |
| Config / validation | pydantic-settings |
| Logging | structlog |
| Runtime | Python 3.12 |

---

## Architecture

```
APScheduler  /  GitHub Actions (Mon–Fri 07:00 Madrid)
                          │
                          ▼
            ┌─────────────────────────┐
            │     LangGraph Pipeline  │
            │                         │
            │  scrape → write →       │
            │  publish → notify       │
            └─────────────────────────┘
                 │           │
                 ▼           ▼
           Supabase      blog/src/
           (posts,        content/
           scraped_       posts/*.md
           items)              │
                               ▼
                         git push → Vercel
                         deploy hook
                               │
                               ▼
                        Telegram channel
```

### Pipeline nodes

| Node | What it does |
|---|---|
| `scrape` | Fetches in parallel from HN Algolia API, GitHub Trending (HTML), GitHub Search API, ArXiv Atom feed, Reddit OAuth2 API, RSS feeds, Dev.to API, Product Hunt GraphQL. Deduplicates against Supabase. |
| `write` | Groups items by theme with Claude, drafts one Markdown post per group (350–550 words in Spanish), generates SEO title + description + Spanish tags + cover keywords. |
| `publish` | Writes `.md` files to `blog/src/content/posts/`, commits and pushes to GitHub (triggers Vercel redeploy). Persists posts to Supabase. |
| `notify` | Sends a Telegram message per post to the configured channel. No-op when `TELEGRAM_BOT_TOKEN` is not set. |

---

## Local Setup

### 1. Clone

```bash
git clone https://github.com/your-username/first-cup.git
cd first-cup
```

### 2. Virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure

```bash
cp .env.example .env
# Fill in every required value — see Environment Variables below
```

### 5. Set up the database

Run `supabase/schema.sql` against your Supabase project (SQL editor or `supabase db push`).

### 6. Run once

```bash
python3 -m agent.main
```

### 7. Start the scheduler (keeps running daily)

```bash
python3 -m agent.scheduler
```

Logs are written to stdout in structured JSON via structlog.

---

## Docker

```bash
# Build and run (scheduler mode)
docker compose up --build

# One-off run
docker compose run --rm agent python -m agent.main
```

The blog directory is mounted as a volume so the agent can write posts to `blog/src/content/posts/` and the git push picks them up.

---

## GitHub Actions

Two workflows are included in `.github/workflows/`:

| Workflow | Trigger | What it does |
|---|---|---|
| `daily-agent.yml` | Cron Mon–Fri 05:00 UTC (07:00 Madrid) · manual dispatch | Runs `agent.main`, commits new posts, pushes |
| `deploy.yml` | Push to `main` touching `blog/src/content/posts/**` | Builds Astro, triggers Vercel deploy hook |

Add these secrets to your GitHub repository:

```
ANTHROPIC_API_KEY
SUPABASE_URL
SUPABASE_KEY
GH_TOKEN              # classic PAT with repo scope
BLOG_GITHUB_REPO      # owner/repo
BLOG_GITHUB_TOKEN     # write access to blog repo
REDDIT_CLIENT_ID
REDDIT_CLIENT_SECRET
VERCEL_DEPLOY_HOOK_URL
```

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | ✅ | — | `sk-ant-...` |
| `SUPABASE_URL` | ✅ | — | `https://xxxx.supabase.co` |
| `SUPABASE_KEY` | ✅ | — | Service-role key |
| `GITHUB_TOKEN` | ✅ | — | PAT with `repo` scope |
| `BLOG_GITHUB_REPO` | ✅ | — | `owner/repo` |
| `BLOG_GITHUB_TOKEN` | ✅ | — | Write access to blog repo |
| `BLOG_REPO_PATH` | | `/app/blog` | Local path to blog clone |
| `REDDIT_CLIENT_ID` | ✅ | — | Reddit OAuth2 client ID |
| `REDDIT_CLIENT_SECRET` | ✅ | — | Reddit OAuth2 client secret |
| `REDDIT_USER_AGENT` | | `first-cup/1.0` | Reddit API user-agent |
| `TELEGRAM_BOT_TOKEN` | | — | Token from @BotFather (optional) |
| `TELEGRAM_CHANNEL_ID` | | `@firstcup` | Public channel or numeric ID |
| `TELEGRAM_PREMIUM_GROUP_ID` | | — | Premium supergroup numeric ID |
| `RESEND_API_KEY` | | — | Phase 2: email delivery |
| `EMAIL_FROM` | | `hola@firstcup.dev` | Sender address |
| `STRIPE_SECRET_KEY` | | — | Phase 3: payments |
| `STRIPE_WEBHOOK_SECRET` | | — | Phase 3: webhook signing |
| `STRIPE_PREMIUM_PRICE_ID` | | — | Phase 3: premium plan price |
| `DAILY_RUN_HOUR` | | `7` | Hour to run (0–23) |
| `DAILY_RUN_MINUTE` | | `0` | Minute to run (0–59) |
| `TIMEZONE` | | `Europe/Madrid` | IANA timezone |

---

## Project Structure

```
first-cup/
├── agent/
│   ├── config.py          # pydantic-settings singleton
│   ├── main.py            # one-shot entry point
│   ├── scheduler.py       # APScheduler daily loop
│   ├── graph/
│   │   ├── graph.py       # LangGraph pipeline assembly
│   │   └── nodes.py       # scrape / write / publish / notify nodes
│   ├── scraper/
│   │   ├── base.py        # ScraperBase + ScrapedItem dataclass
│   │   ├── hackernews.py  # HN Algolia API
│   │   ├── github_trending.py  # GitHub trending (HTML)
│   │   ├── github_api.py  # GitHub Search API
│   │   ├── arxiv.py       # ArXiv Atom feed
│   │   ├── reddit.py      # Reddit OAuth2 API
│   │   ├── rss.py         # feedparser multi-feed
│   │   ├── devto.py       # Dev.to public API
│   │   └── producthunt.py # Product Hunt GraphQL + HTML fallback
│   ├── writer/
│   │   ├── claude_client.py  # AsyncAnthropic wrapper with retry
│   │   ├── prompts.py        # Spanish prompt templates
│   │   └── writer.py         # DigestWriter orchestrator
│   ├── publisher/
│   │   ├── markdown.py    # Astro-compatible frontmatter generator
│   │   └── git_publisher.py  # GitPython commit + push
│   ├── notifier/
│   │   └── telegram.py    # Telegram Bot API notifier
│   └── db/
│       ├── supabase_client.py  # Singleton client
│       └── posts.py            # CRUD: posts + scraped_items
├── blog/                  # Astro 4 blog (src/content/posts/*.md)
├── supabase/
│   └── schema.sql         # Run once to create tables
├── .github/
│   └── workflows/
│       ├── daily-agent.yml   # Runs the agent on schedule
│       └── deploy.yml        # Builds and deploys blog to Vercel
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

---

## License

MIT
