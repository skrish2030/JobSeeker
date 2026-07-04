-- Create Market Intelligence table
CREATE TABLE public.intelligence_feed (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    source_type TEXT NOT NULL, -- 'reddit', 'youtube', 'github'
    author TEXT NOT NULL,
    content_summary TEXT NOT NULL,
    trending_skills_detected TEXT[], -- Array of tech skills mentioned
    url TEXT,
    sentiment TEXT, -- 'Positive', 'Neutral', 'Negative'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE public.intelligence_feed ENABLE ROW LEVEL SECURITY;

-- Allow anyone to read intelligence feeds (public data)
CREATE POLICY "Public can read intelligence feeds"
ON public.intelligence_feed FOR SELECT
USING (true);

-- Only service role can insert
CREATE POLICY "Service role can insert intelligence feeds"
ON public.intelligence_feed FOR INSERT
WITH CHECK (current_setting('request.jwt.claim.role', true) = 'service_role');
