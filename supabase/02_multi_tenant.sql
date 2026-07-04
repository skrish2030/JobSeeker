-- Create user_settings table
CREATE TABLE IF NOT EXISTS public.user_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    ai_provider TEXT DEFAULT 'gemini',
    ai_api_key TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id)
);

-- Enable RLS on user_settings
ALTER TABLE public.user_settings ENABLE ROW LEVEL SECURITY;

-- Create policy for user_settings (Users can only see/edit their own settings)
CREATE POLICY "Users can manage their own settings" 
ON public.user_settings 
FOR ALL 
USING (auth.uid() = user_id) 
WITH CHECK (auth.uid() = user_id);

-- Create user_saved_jobs table (Junction table)
CREATE TABLE IF NOT EXISTS public.user_saved_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    job_id TEXT NOT NULL REFERENCES public.jobs(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, job_id)
);

-- Enable RLS on user_saved_jobs
ALTER TABLE public.user_saved_jobs ENABLE ROW LEVEL SECURITY;

-- Create policy for user_saved_jobs (Users can only see/edit their own saved jobs)
CREATE POLICY "Users can manage their own saved jobs" 
ON public.user_saved_jobs 
FOR ALL 
USING (auth.uid() = user_id) 
WITH CHECK (auth.uid() = user_id);
