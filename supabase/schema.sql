-- ============================================================
-- First Cup — Supabase schema
-- Run this once against your Supabase project via the SQL editor
-- or: supabase db push (if using the Supabase CLI)
-- ============================================================

-- ─── Extensions ──────────────────────────────────────────────────────────────
create extension if not exists "uuid-ossp";

-- ─── scraped_items ────────────────────────────────────────────────────────────
-- Deduplication table: every URL the agent has ever seen is recorded here.
-- On each run the agent checks this table before processing an item.

create table if not exists scraped_items (
    id          uuid primary key default uuid_generate_v4(),
    url         text not null unique,
    title       text not null default '',
    source      text not null default '',
    scraped_at  timestamptz not null default now()
);

create index if not exists scraped_items_url_idx      on scraped_items (url);
create index if not exists scraped_items_scraped_at_idx on scraped_items (scraped_at desc);

comment on table scraped_items is
    'Deduplication log: every URL the digest agent has fetched.';

-- ─── posts ───────────────────────────────────────────────────────────────────
-- Published digest posts persisted to Supabase for analytics and future
-- subscriber email delivery.

create table if not exists posts (
    id           uuid primary key default uuid_generate_v4(),
    title        text        not null,
    slug         text        not null unique,
    description  text        not null default '',
    content      text        not null default '',
    tags         jsonb       not null default '[]',
    source_urls  jsonb       not null default '[]',
    cover        text,
    published_at timestamptz not null default now(),
    created_at   timestamptz not null default now()
);

create index if not exists posts_slug_idx         on posts (slug);
create index if not exists posts_published_at_idx on posts (published_at desc);
create index if not exists posts_tags_idx         on posts using gin (tags);

comment on table posts is
    'Published First Cup digest posts, mirrored from the blog git repo.';

-- ─── subscribers ─────────────────────────────────────────────────────────────
-- Email subscriber list for the newsletter (Phase 2).
-- The tier column distinguishes free vs premium subscribers.

create table if not exists subscribers (
    id             uuid primary key default uuid_generate_v4(),
    email          text not null unique,
    name           text,
    tier           text not null default 'free' check (tier in ('free', 'premium')),
    confirmed      boolean not null default false,
    confirm_token  text unique,
    stripe_id      text unique,
    subscribed_at  timestamptz not null default now(),
    unsubscribed_at timestamptz
);

create index if not exists subscribers_email_idx on subscribers (email);
create index if not exists subscribers_tier_idx  on subscribers (tier);

comment on table subscribers is
    'First Cup email subscribers. confirmed=false until they click the verification link.';

-- ─── Row Level Security ───────────────────────────────────────────────────────
-- Agent uses the service-role key (bypasses RLS).
-- Anon / authenticated users can only read published posts.

alter table scraped_items enable row level security;
alter table posts          enable row level security;
alter table subscribers    enable row level security;

-- posts: public read
create policy "posts_public_read"
    on posts for select
    using (true);

-- scraped_items: service-role only (no public policy)

-- subscribers: each subscriber can read their own row only
create policy "subscribers_self_read"
    on subscribers for select
    using (auth.uid()::text = id::text);

-- ─── Helper function ─────────────────────────────────────────────────────────
-- Returns the next edition number (max existing + 1).
-- Used by the blog frontend to display "#001", "#002", etc.

create or replace function next_edition_number()
returns integer
language sql stable
as $$
    select count(*)::integer + 1 from posts;
$$;
