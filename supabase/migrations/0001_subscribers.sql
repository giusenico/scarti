-- Scarti subscriber list with double opt-in.
-- Run in Supabase SQL editor or via `supabase db push`.

create extension if not exists pgcrypto;

create table if not exists public.subscribers (
  email             text primary key,
  locale            text not null default 'it' check (locale in ('it', 'en')),
  confirm_token     uuid not null default gen_random_uuid(),
  confirmed_at      timestamptz,
  unsub_token       uuid not null default gen_random_uuid(),
  created_at        timestamptz not null default now(),
  last_sent_at      timestamptz
);

create index if not exists subscribers_confirmed_idx
  on public.subscribers (confirmed_at)
  where confirmed_at is not null;

-- Row-level security: no one can read via anon key. All access goes through
-- the service-role key used by the pipeline and the Astro API routes.
alter table public.subscribers enable row level security;

-- No permissive policies defined on purpose: anon/authenticated users cannot
-- see or modify this table. The server must use the service role.
