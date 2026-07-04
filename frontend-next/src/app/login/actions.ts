'use server'

import { createClient } from '@/utils/supabase/server'

export async function login(email: string, password: string) {
  const supabase = await createClient()

  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
  })

  if (error) {
    return { error: error.message }
  }

  return { success: true }
}

export async function signup(email: string, password: string) {
  const supabase = await createClient()

  const { data, error } = await supabase.auth.signUp({
    email,
    password,
  })

  if (error) {
    return { error: error.message }
  }

  // If Supabase has email confirmation ON, data.session will be null
  if (data.user && !data.session) {
    return { success: true, message: "Please check your email to confirm your account!" }
  }

  return { success: true }
}
