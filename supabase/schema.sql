-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- 1. Jobs Table
create table public.jobs (
    id uuid primary key default uuid_generate_v4(),
    job_hash text unique not null, -- Unique hash based on URL/title/company to avoid duplicates
    title text not null,
    company text not null,
    location text,
    source_site text,
    job_url text not null,
    description text,
    min_amount numeric,
    max_amount numeric,
    currency text,
    interval text, -- e.g., 'yearly', 'hourly'
    posted_date timestamp with time zone,
    scraped_at timestamp with time zone default now(),
    score integer default 0,
    ai_classification jsonb,
    is_active boolean default true
);

-- Indexes for fast querying
create index idx_jobs_posted_date on public.jobs(posted_date desc);
create index idx_jobs_score on public.jobs(score desc);
create index idx_jobs_company on public.jobs(company);
create index idx_jobs_location on public.jobs(location);

-- 2. Target Companies (For corporate portal scraping)
create table public.companies (
    id uuid primary key default uuid_generate_v4(),
    name text unique not null,
    portal_url text,
    added_at timestamp with time zone default now()
);

-- 3. Scrape Log (To monitor GH Actions)
create table public.scrape_log (
    id uuid primary key default uuid_generate_v4(),
    run_id text,
    started_at timestamp with time zone default now(),
    finished_at timestamp with time zone,
    jobs_inserted integer default 0,
    errors_count integer default 0,
    notes text
);

-- 4. Settings (Global Settings for AI / Scraper / Email)
create table public.settings (
    id text primary key, -- e.g., 'global'
    ai_provider text,
    ai_model text,
    min_relevance_score integer default 50,
    email_sender text,
    email_recipient text,
    resume_text text
);

-- INITIAL CONFIGURATION
-- Row Level Security (RLS)
alter table public.jobs enable row level security;
alter table public.companies enable row level security;
alter table public.scrape_log enable row level security;
alter table public.settings enable row level security;

-- Public can read Jobs and Companies
create policy "Allow public read-only access to jobs" on public.jobs for select using (true);
create policy "Allow public read-only access to companies" on public.companies for select using (true);

-- Only authenticated users (Service Role) can insert/update jobs, companies, settings, and logs
-- (The service_role key bypasses RLS entirely, so we technically don't need policies for the scraper, 
-- but this secures the database from public unauthorized writes).
