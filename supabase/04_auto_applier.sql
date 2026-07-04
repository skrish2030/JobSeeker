-- Create the applications table to track auto-apply progress
CREATE TABLE public.applications (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    job_id UUID REFERENCES public.jobs(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'pending', -- 'pending', 'applied', 'failed'
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE public.applications ENABLE ROW LEVEL SECURITY;

-- Create policies for applications
CREATE POLICY "Users can view their own applications" 
ON public.applications FOR SELECT 
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own applications" 
ON public.applications FOR INSERT 
WITH CHECK (auth.uid() = user_id);

-- Storage bucket for resumes
INSERT INTO storage.buckets (id, name, public) 
VALUES ('resumes', 'resumes', false)
ON CONFLICT (id) DO NOTHING;

-- Policies for resume storage
CREATE POLICY "Users can upload their own resumes"
ON storage.objects FOR INSERT
WITH CHECK (
    bucket_id = 'resumes' AND 
    auth.uid()::text = (storage.foldername(name))[1]
);

CREATE POLICY "Users can read their own resumes"
ON storage.objects FOR SELECT
USING (
    bucket_id = 'resumes' AND 
    auth.uid()::text = (storage.foldername(name))[1]
);

-- Service role can read everything (for the auto applier github action)
CREATE POLICY "Service role can read all resumes"
ON storage.objects FOR SELECT
USING (
    bucket_id = 'resumes' AND 
    current_setting('request.jwt.claim.role', true) = 'service_role'
);
