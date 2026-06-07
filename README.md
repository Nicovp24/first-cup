# First Cup ☕

**First Cup** es un diario tech autónomo en español. Un agente de IA rastrea cientos de fuentes cada día, redacta artículos de 700-1000 palabras con Claude y los publica automáticamente en [first-cup.es](https://first-cup.es). Los suscriptores reciben el digest por email. Hay un plan gratuito y uno Premium con Stripe.

---

## Cómo funciona — visión general

```
GitHub Actions (cron 07:00 y 15:00 Madrid)
              │
              ▼
   ┌──────────────────────────────┐
   │       LangGraph Pipeline     │
   │                              │
   │  scrape → write → publish    │
   │       → notify → email       │
   └──────────────────────────────┘
        │          │         │
        ▼          ▼         ▼
   Supabase    blog/src/   Telegram
   (posts,     content/    (canal)
   scraped,    posts/*.md
   subs)           │
                   ▼
             git push → Vercel
             (redeploy automático)
                   │
                   ▼
            first-cup.es 🌐
```

---

## Stack

| Capa | Tecnología |
|------|-----------|
| Orquestación | LangGraph 0.2 |
| LLM principal | Groq (`llama-3.3-70b-versatile`, gratuito y rápido) |
| LLM fallback | Claude Sonnet 4.6 → Gemini |
| Scraping | feedparser · httpx · BeautifulSoup4 · lxml |
| Base de datos | Supabase (PostgreSQL) |
| Blog | Astro 4 · `output: hybrid` · Vercel serverless |
| Publicación | GitPython → GitHub → Vercel redeploy |
| Email | Resend (confirmación + digest diario) |
| Pagos | Stripe Checkout + webhooks |
| Notificaciones | Telegram Bot API |
| Scheduling | GitHub Actions cron |
| Config | pydantic-settings |
| Logs | structlog (JSON estructurado) |
| Runtime | Python 3.12 |

---

## Pipeline paso a paso

### 1. `scrape` — Rastreo paralelo

Ejecuta todos los scrapers en paralelo con `asyncio.gather`. Fuentes:

| Scraper | Fuente | Qué obtiene |
|---------|--------|-------------|
| `HackerNewsScraper` | HN Algolia API | Top stories del día |
| `GitHubTrendingScraper` | github.com/trending | Repos trending (HTML) |
| `GitHubAPIScraper` | GitHub Search API | Repos con más stars recientes |
| `RSSScraper` | 7 feeds (Simon Willison, HuggingFace, TechCrunch…) | Artículos del día |
| `RedditScraper` | Reddit OAuth2 | Posts top de r/MachineLearning, r/LocalLLaMA, r/Python… |
| `ArXivScraper` | ArXiv Atom | Papers de cs.AI, cs.LG recientes |
| `DevToScraper` | Dev.to API | Artículos trending |
| `ProductHuntScraper` | Product Hunt GraphQL | Productos del día |

**Deduplicación:** Se compara cada URL contra la tabla `published_posts` de Supabase. URLs ya publicadas se descartan. Dentro del mismo run, duplicados entre scrapers también se eliminan.

### 2. `write` — Redacción con IA

`DigestWriter` hace dos llamadas al LLM:

1. **Selección editorial**: El LLM recibe todos los items scrapeados en JSON (con título, resumen, fuente, score, stars de GitHub, lenguaje, forks, topics) y selecciona los N mejores según relevancia e impacto (N = `STORIES_PER_RUN`, por defecto 6).

2. **Redacción por artículo**: Por cada item seleccionado, escribe un artículo en español de 700-1000 palabras con esta estructura:
   - Hook periodístico (1 párrafo)
   - Contexto y antecedentes
   - Análisis técnico en profundidad
   - Implicaciones para la industria
   - Limitaciones y puntos críticos
   - Blockquote destacado
   - "Ver también" con 2-3 enlaces relevantes
   - Bottom line (1 frase)

   También genera: título SEO, descripción meta, tags en español, imagen de portada (OG image de GitHub para repos, o imagen del artículo original).

**Prioridad de cliente IA:** Groq (gratis, rápido) → Claude (pago) → Gemini (pago).

### 3. `publish` — Publicación en el blog

`GitPublisher` escribe cada artículo como un archivo `.md` en `blog/src/content/posts/` con frontmatter Astro-compatible:

```yaml
---
title: "Título del artículo"
description: "Meta description SEO"
date: 2026-06-07T07:00:00Z
tags: ["IA", "GitHub", "Python"]
cover: "https://opengraph.github.com/repo/owner/repo"
source_urls: ["https://github.com/owner/repo"]
---
```

Luego hace `git add`, `git commit` y `git push` al repositorio. Vercel detecta el push y redespliega automáticamente. Los posts también se guardan en Supabase (`posts` table).

### 4. `notify` — Telegram

Envía un mensaje por cada post al canal de Telegram configurado. No-op si `TELEGRAM_BOT_TOKEN` no está definido.

### 5. `email` — Newsletter

`EmailNewsletter` consulta la tabla `subscribers` (solo `confirmed=true` y `unsubscribed_at IS NULL`), construye un email HTML estilo periódico por cada post y los envía vía **Resend batch API**. Cada email incluye un enlace de cancelación personalizado con el `confirm_token` del suscriptor.

---

## Blog (Astro)

El blog en `blog/` es una aplicación Astro 4 con:

- **`output: hybrid`**: páginas estáticas + rutas API serverless en Vercel
- **Tema dual**: Latte (crema) / Espresso (oscuro) con toggle
- **Ediciones**: los posts se agrupan por día. Cada día es una edición numerada (`#001`, `#002`…). La home muestra la última; `/edicion/N` las anteriores.
- **API routes** (todas serverless en Vercel):
  - `POST /api/subscribe` — guarda email en Supabase, envía email de confirmación con token único
  - `GET /api/confirm?token=...` — marca `confirmed=true`
  - `GET /api/unsubscribe?token=...` — marca `unsubscribed_at=now()`
  - `POST /api/checkout` — crea Stripe Checkout Session y devuelve URL
  - `POST /api/stripe-webhook` — verifica firma HMAC-SHA256, actualiza tier en Supabase

---

## Estructura del proyecto

```
nexus-digest/
├── agent/
│   ├── config.py                  # Settings singleton (pydantic-settings)
│   ├── main.py                    # Entry point: run_agent() + run_breaking_news()
│   ├── graph/
│   │   ├── graph.py               # LangGraph pipeline (scrape→write→publish→notify→email)
│   │   └── nodes.py               # Nodos del pipeline + AgentState TypedDict
│   ├── scraper/
│   │   ├── base.py                # ScraperBase + ScrapedItem dataclass
│   │   ├── hackernews.py          # HN Algolia API
│   │   ├── github_trending.py     # GitHub trending (HTML scraping)
│   │   ├── github_api.py          # GitHub Search API
│   │   ├── arxiv.py               # ArXiv Atom feed
│   │   ├── reddit.py              # Reddit OAuth2
│   │   ├── rss.py                 # feedparser multi-feed
│   │   ├── devto.py               # Dev.to API
│   │   └── producthunt.py         # Product Hunt GraphQL
│   ├── writer/
│   │   ├── groq_client.py         # Groq API (prioritario, gratuito)
│   │   ├── claude_client.py       # Anthropic SDK wrapper
│   │   ├── gemini_client.py       # Google Gemini wrapper
│   │   ├── prompts.py             # Prompts en español (editor + artículo)
│   │   └── writer.py              # DigestWriter: selección + redacción
│   ├── publisher/
│   │   ├── markdown.py            # Genera frontmatter Astro
│   │   └── git_publisher.py       # GitPython: commit + push
│   ├── notifier/
│   │   ├── telegram.py            # Telegram Bot API
│   │   └── email_newsletter.py    # Resend batch + HTML template
│   └── db/
│       ├── posts.py               # CRUD: posts + scraped_items
│       └── subscribers.py         # CRUD: subscribers (confirm, tier, unsubscribe)
├── blog/                          # Astro 4 blog
│   ├── src/
│   │   ├── pages/
│   │   │   ├── index.astro        # Homepage con ediciones
│   │   │   ├── [slug].astro       # Post individual
│   │   │   ├── edicion/[num].astro # Ediciones anteriores
│   │   │   ├── subscribe.astro    # Página de suscripción (free + premium)
│   │   │   ├── confirmed.astro    # Página post-confirmación
│   │   │   ├── unsubscribed.astro # Página post-cancelación
│   │   │   ├── success.astro      # Página post-pago Stripe
│   │   │   └── api/
│   │   │       ├── subscribe.ts   # POST: guarda suscriptor + email confirmación
│   │   │       ├── confirm.ts     # GET: confirma suscriptor
│   │   │       ├── unsubscribe.ts # GET: cancela suscriptor
│   │   │       ├── checkout.ts    # POST: crea Stripe Checkout Session
│   │   │       └── stripe-webhook.ts # POST: webhook Stripe (HMAC verify)
│   │   ├── components/
│   │   │   ├── Header.astro       # Dateline bar + masthead + tema toggle
│   │   │   ├── PostCard.astro     # Card de post para el grid
│   │   │   ├── SubscribeForm.astro # Formulario de suscripción inline
│   │   │   └── SEO.astro          # Meta tags + OG + JSON-LD
│   │   ├── content/
│   │   │   └── posts/*.md         # Posts generados por el agente
│   │   └── styles/global.css      # Tokens CSS oklch + temas latte/espresso
│   └── astro.config.mjs
├── supabase/
│   └── schema.sql                 # Tablas: scraped_items, posts, subscribers
├── .github/
│   └── workflows/
│       └── daily-agent.yml        # Cron 07:00 + 15:00 Madrid · manual dispatch
├── requirements.txt
└── .env.example
```

---

## Base de datos (Supabase)

Tres tablas principales:

```sql
scraped_items   -- URLs vistas por el agente (deduplicación)
  id, url, title, source, scraped_at

posts           -- Posts publicados
  id, title, slug, description, content, tags, source_urls, cover, published_at

subscribers     -- Lista de suscriptores
  id, email, name, tier (free|premium), confirmed, confirm_token,
  stripe_id, subscribed_at, unsubscribed_at
```

RLS activado. El agente usa `SUPABASE_SERVICE_KEY` (bypassa RLS). El blog usa `SUPABASE_SERVICE_KEY` también desde las API routes.

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

# 5. Ejecutar el agente una vez
python -m agent.main

# 6. Blog local
cd blog && npm install && npm run dev
```

---

## Variables de entorno

| Variable | Requerida | Descripción |
|----------|-----------|-------------|
| `GROQ_API_KEY` | ✅ (o Anthropic/Gemini) | LLM principal (gratuito) |
| `ANTHROPIC_API_KEY` | — | Fallback LLM |
| `GEMINI_API_KEY` | — | Fallback LLM |
| `SUPABASE_URL` | ✅ | `https://xxxx.supabase.co` |
| `SUPABASE_KEY` | ✅ | Anon key de Supabase |
| `SUPABASE_SERVICE_KEY` | ✅ | Service role key (escribe en DB) |
| `BLOG_GITHUB_REPO` | ✅ | `Nicovp24/first-cup` |
| `BLOG_GITHUB_TOKEN` | ✅ | PAT con permisos Contents: Write |
| `BLOG_REPO_PATH` | — | Ruta local al repo (CI: workspace) |
| `BLOG_POSTS_SUBDIR` | — | `blog/src/content/posts` |
| `RESEND_API_KEY` | ✅ | Envío de emails |
| `EMAIL_FROM` | ✅ | `First Cup <hola@first-cup.es>` |
| `STRIPE_SECRET_KEY` | ✅ | Clave secreta de Stripe |
| `STRIPE_WEBHOOK_SECRET` | ✅ | Signing secret del webhook |
| `STRIPE_PREMIUM_PRICE_ID` | ✅ | `price_...` del plan Premium |
| `REDDIT_CLIENT_ID` | — | OAuth2 Reddit |
| `REDDIT_CLIENT_SECRET` | — | OAuth2 Reddit |
| `TELEGRAM_BOT_TOKEN` | — | Token de @BotFather |
| `TELEGRAM_CHANNEL_ID` | — | ID del canal público |
| `STORIES_PER_RUN` | — | Posts por ejecución (default: 6) |
| `TIMEZONE` | — | `Europe/Madrid` |

---

## GitHub Actions secrets necesarios

Los mismos que las variables de entorno, más:

| Secret | Valor |
|--------|-------|
| `GH_TOKEN` | PAT clásico con scope `repo` |
| `BLOG_GITHUB_TOKEN` | PAT fino con Contents: Write en el repo |
| `BLOG_GITHUB_REPO` | `Nicovp24/first-cup` |

---

## Deployment

| Servicio | URL | Para qué |
|----------|-----|----------|
| Vercel | `first-cup.es` | Hosting del blog (serverless) |
| Supabase | `xxxx.supabase.co` | Base de datos |
| Resend | resend.com | Envío de emails desde `@first-cup.es` |
| Stripe | dashboard.stripe.com | Pagos del plan Premium (5€/mes) |
| GitHub Actions | `.github/workflows/` | Ejecuta el agente a las 07:00 y 15:00 Madrid |

El cron de GitHub Actions está en UTC:
- `0 5 * * *` → 07:00 Madrid (UTC+2 verano)
- `0 13 * * *` → 15:00 Madrid

---

## Flujo de suscripción

```
Usuario introduce email
        │
        ▼
POST /api/subscribe
  → Guarda en Supabase (confirmed=false, confirm_token=uuid)
  → Envía email de confirmación con link único
        │
        ▼ (usuario hace clic en el link)
GET /api/confirm?token=...
  → PATCH Supabase: confirmed=true
  → Redirige a /confirmed
        │
        ▼ (agente ejecuta email_node)
EmailNewsletter.send_digest()
  → Consulta subscribers WHERE confirmed=true AND unsubscribed_at IS NULL
  → Envía digest por Resend a cada suscriptor
  → Link personalizado de cancelación por email
```

## Flujo Premium (Stripe)

```
Usuario introduce email en plan Premium
        │
        ▼
POST /api/checkout
  → Crea Stripe Checkout Session (mode=subscription, 5€/mes)
  → Devuelve URL de Stripe
        │
        ▼ (usuario completa el pago)
POST /api/stripe-webhook
  → Verifica firma HMAC-SHA256 (Web Crypto API, sin SDK)
  → checkout.session.completed → tier='premium' en Supabase
  → customer.subscription.deleted → tier='free' en Supabase
```

---

## Licencia

MIT
