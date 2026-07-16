-- 5. Analytics Insights
create table public.analytics_insights (
    id uuid primary key default uuid_generate_v4(),
    generated_at timestamp with time zone default now(),
    total_jobs_analyzed integer not null,
    trending_skills jsonb, -- e.g., [{"skill": "Python", "count": 120}, ...]
    trending_titles jsonb, -- e.g., [{"title": "Software Engineer", "count": 50}, ...]
    ai_market_summary text, -- AI generated summary (if AI is enabled)
    is_latest boolean default true -- Easy way to fetch the most recent run
);

-- Enable RLS
alter table public.analytics_insights enable row level security;

-- Public can read analytics
create policy "Allow public read-only access to analytics" on public.analytics_insights for select using (true);
