# First Cup

**First Cup** es un diario tech autónomo en español. Un agente de IA rastrea fuentes cada día, redacta artículos editoriales con LLMs y los publica automáticamente en [first-cup.es](https://first-cup.es). Los suscriptores reciben el digest por email; hay un plan gratuito y uno Premium.

---

## Arquitectura

```
cron (07:00 Madrid)
        │
        ▼
┌─────────────────────────────────┐
│        LangGraph Pipeline       │
│                                 │
│  scrape → write → publish       │
│         → notify → email        │
└─────────────────────────────────┘
      │           │           │
      ▼           ▼           ▼
  Supabase    blog/src/    Telegram
  (posts,     content/     (canal)
  scraped,    posts/*.md
  subs)           │
                  ▼
            git push → Vercel
            (redeploy automático)
                  │
                  ▼
           first-cup.es
```

---

## Stack

| Capa | Tecnología |
|------|-----------|
| Orquestación | LangGraph |
| LLM primario | Groq (`llama-3.3-70b-versatile`) |
| LLM fallback 1 | Google Gemini 2.0 Flash |
| LLM fallback 2 | Anthropic Claude Sonnet |
| Scraping | httpx · feedparser · BeautifulSoup4 · lxml |
| Base de datos | Supabase (PostgreSQL) |
| Blog | Astro · `output: hybrid` · Vercel serverless |
| Publicación | subprocess git → GitHub → Vercel redeploy |
| Email | Resend (confirmación + digest diario) |
| Pagos | Stripe Checkout + webhooks |
| Notificaciones | Telegram Bot API |
| Config | pydantic-settings |
| Logs | structlog |
| Runtime | Python 3.12 |

---

## Pipeline

### 1. `scrape` — Rastreo paralelo

Todos los scrapers corren en paralelo con `asyncio.gather`:

| Scraper | Fuente | Contenido |
|---------|--------|-----------|
| `HackerNewsScraper` | HN Algolia API | Top stories del día (≥50 puntos) |
| `GitHubTrendingScraper` | github.com/trending | Repos trending diarios |
| `GitHubAPIScraper` | GitHub Search API | Repos con actividad reciente |
| `RSSScraper` | TechCrunch AI, The Verge AI, VentureBeat, Ars Technica, Wired, HuggingFace Blog, Simon Willison | Artículos de las últimas 24h |
| `RedditScraper` | Reddit OAuth2 | Posts top de r/MachineLearning, r/LocalLLaMA, r/Python… |
| `ArXivScraper` | ArXiv Atom | Papers cs.AI / cs.LG recientes |
| `DevToScraper` | Dev.to API | Artículos trending |
| `ProductHuntScraper` | Product Hunt GraphQL | Productos del día |

**Deduplicación en dos capas:**

- **GitHub repos** (`github_trending`, `github_api`): bloqueados permanentemente después del primer scrape via tabla `scraped_items`. Los repos trendan todos los días — una vez cubiertos, nunca vuelven a entrar.
- **Noticias** (resto de fuentes): nunca bloqueadas permanentemente. Rotan de forma natural; sólo se deduplican dentro del mismo run.

### 2. `write` — Redacción con IA

`DigestWriter` hace dos llamadas al LLM:

**Selección editorial** — el LLM recibe los items en JSON y elige los 8 mejores. Regla absoluta en código y en prompt:
- Máximo 2 repositorios de GitHub por run, sin excepción
- Mínimo 6 artículos de fuentes de noticias reales
- Prioridad 1: lanzamientos de modelos de IA (siempre breaking)

El límite de 2 repos se aplica en dos puntos del código: antes de serializar los items (el LLM solo ve 2 repos en el pool) y después de la selección (cualquier repo adicional que el LLM elija se descarta).

**Redacción** — por cada item seleccionado, escribe un artículo en español de ~600 palabras:
- Apertura periodística (hecho más importante primero)
- 3-4 secciones con `##` headers
- Blockquote con cita real del README, paper o release notes
- Bottom line en negrita
- "Ver también" con enlaces

También genera: título SEO, descripción meta, tags en español, y keywords para imagen de portada.

### 3. `publish` — Publicación

`GitPublisher` escribe cada artículo como `.md` en `blog/src/content/posts/` con frontmatter Astro-compatible, luego hace `git pull --rebase` + `git add` + `git commit` + `git push`. Vercel detecta el push y redespliega. Los posts también se guardan en Supabase.

Frontmatter ejemplo:
```yaml
---
title: "Claude Fable 5: el modelo más proactivo de Anthropic"
description: "Anthropic lanza Fable 5, su modelo con razonamiento extendido..."
date: 2026-06-12T07:00:00Z
tags: ["IA", "Anthropic", "LLMs"]
cover: "https://images.unsplash.com/photo-..."
source_urls: ["https://www.anthropic.com/news/fable-5"]
---
```

### 4. `notify` — Telegram

Envía un mensaje por post al canal configurado. No-op si `TELEGRAM_BOT_TOKEN` no está definido.

### 5. `email` — Newsletter

Envía el digest a suscriptores confirmados vía Resend. Incluye los artículos completos más "shots" (items scrapeados no seleccionados para artículo). Cada email lleva un enlace de baja personalizado.

---

## Estructura del proyecto

```
nexus-digest/
├── agent/
│   ├── config.py                  # Settings singleton (pydantic-settings)
│   ├── main.py                    # Entry point
│   ├── graph/
│   │   ├── graph.py               # LangGraph: scrape→write→publish→notify→email
│   │   └── nodes.py               # Nodos del pipeline + AgentState
│   ├── scraper/
│   │   ├── base.py                # ScraperBase + ScrapedItem dataclass
│   │   ├── hackernews.py
│   │   ├── github_trending.py
│   │   ├── github_api.py
│   │   ├── arxiv.py
│   │   ├── reddit.py
│   │   ├── rss.py                 # feedparser multi-feed (8 fuentes)
│   │   ├── devto.py
│   │   └── producthunt.py
│   ├── writer/
│   │   ├── composite_client.py    # Groq → Gemini → Claude fallback
│   │   ├── groq_client.py
│   │   ├── gemini_client.py
│   │   ├── claude_client.py
│   │   ├── prompts.py             # Prompts en español
│   │   └── writer.py             # DigestWriter: selección + redacción + límite repos
│   ├── publisher/
│   │   ├── markdown.py            # Genera frontmatter Astro
│   │   └── git_publisher.py       # subprocess git commit + push
│   ├── notifier/
│   │   ├── telegram.py
│   │   ├── email_newsletter.py    # Resend batch + HTML template
│   │   └── linkedin.py
│   └── db/
│       ├── posts.py               # CRUD: posts + scraped_items + dedup
│       └── subscribers.py         # CRUD: subscribers
├── blog/                          # Astro blog
│   └── src/
│       ├── pages/                 # index, [slug], edicion/[num], api/*
│       ├── components/            # Header, PostCard, SubscribeForm, SEO
│       ├── content/posts/         # .md generados por el agente
│       └── styles/global.css      # Tokens oklch + temas latte/espresso
├── supabase/
│   └── schema.sql
├── requirements.txt
└── .env.example
```

---

## Base de datos (Supabase)

```sql
scraped_items   -- URLs vistas por el agente (deduplicación repos)
  id, url, title, source, scraped_at

posts           -- Posts publicados
  id, title, slug, description, content, tags, source_urls, cover, published_at

subscribers     -- Lista de suscriptores
  id, email, name, tier (free|premium), confirmed, confirm_token,
  stripe_id, subscribed_at, unsubscribed_at
```

RLS activado. El agente y las API routes usan `SUPABASE_SERVICE_KEY`.

---

## Setup local

```bash
# 1. Clonar
git clone https://github.com/Nicovp24/first-cup.git
cd first-cup

# 2. Entorno Python
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Variables de entorno
cp .env.example .env
# Rellenar los valores (ver tabla abajo)

# 4. Base de datos
# Ejecutar supabase/schema.sql en el SQL editor de Supabase

# 5. Ejecutar el agente
python -m agent.main

# 6. Blog local
cd blog && npm install && npm run dev
```

---

## Variables de entorno

| Variable | Requerida | Descripción |
|----------|-----------|-------------|
| `GROQ_API_KEY` | ✅ (o Gemini/Anthropic) | LLM primario — gratis en [console.groq.com](https://console.groq.com) |
| `GEMINI_API_KEY` | — | LLM fallback 1 — gratis en [aistudio.google.com](https://aistudio.google.com) |
| `ANTHROPIC_API_KEY` | — | LLM fallback 2 |
| `SUPABASE_URL` | ✅ | `https://xxxx.supabase.co` |
| `SUPABASE_KEY` | ✅ | Anon key |
| `SUPABASE_SERVICE_KEY` | ✅ | Service role key (escribe en DB) |
| `BLOG_GITHUB_REPO` | ✅ | `Nicovp24/first-cup` |
| `BLOG_GITHUB_TOKEN` | ✅ | PAT con Contents: Write |
| `BLOG_REPO_PATH` | — | Ruta local al repo (default: `/app/blog`) |
| `BLOG_POSTS_SUBDIR` | — | `blog/src/content/posts` |
| `REDDIT_CLIENT_ID` | — | OAuth2 Reddit |
| `REDDIT_CLIENT_SECRET` | — | OAuth2 Reddit |
| `RESEND_API_KEY` | — | Envío de emails |
| `EMAIL_FROM` | — | `First Cup <hola@first-cup.es>` |
| `TELEGRAM_BOT_TOKEN` | — | Token de @BotFather |
| `TELEGRAM_CHANNEL_ID` | — | ID del canal (ej. `@firstcup_dev`) |
| `STRIPE_SECRET_KEY` | — | Plan Premium |
| `STRIPE_WEBHOOK_SECRET` | — | Signing secret del webhook |
| `STRIPE_PREMIUM_PRICE_ID` | — | `price_...` del plan Premium |
| `STORIES_PER_RUN` | — | Posts por ejecución (default: `8`) |
| `TIMEZONE` | — | `Europe/Madrid` |

---

## Deployment

| Servicio | Para qué |
|----------|----------|
| Vercel | Hosting del blog (serverless, redeploy automático en push) |
| Supabase | Base de datos |
| Resend | Emails desde `@first-cup.es` |
| Stripe | Pagos plan Premium |
| cron-job.org | Disparo diario del agente vía HTTP trigger |

---

## Flujo de suscripción

```
email introducido en /subscribe
        │
        ▼
POST /api/subscribe
  → Supabase: confirmed=false, genera confirm_token
  → Resend: email de confirmación con link único
        │
        ▼ (clic en el link)
GET /api/confirm?token=...
  → Supabase: confirmed=true
  → Redirige a /confirmed
        │
        ▼ (agente ejecuta email_node)
EmailNewsletter.send_digest()
  → subscribers WHERE confirmed=true AND unsubscribed_at IS NULL
  → Resend batch: digest HTML + link de baja personalizado
```

## Flujo Premium

```
email introducido en plan Premium
        │
        ▼
POST /api/checkout
  → Stripe Checkout Session (mode=subscription)
  → Devuelve URL de pago
        │
        ▼ (pago completado)
POST /api/stripe-webhook
  → Verifica firma HMAC-SHA256
  → checkout.session.completed → tier='premium'
  → customer.subscription.deleted → tier='free'
```

---

## Licencia

MIT
