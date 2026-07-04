-- Add email column to user_settings table to support multi-user email digests
ALTER TABLE public.user_settings ADD COLUMN IF NOT EXISTS email TEXT;
