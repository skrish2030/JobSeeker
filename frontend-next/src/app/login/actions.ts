'use server'

import { createClient } from '@/utils/supabase/server'

export async function login(email: string, password: string, captchaToken?: string) {
  const supabase = await createClient()

  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
    options: { captchaToken }
  })

  if (error) {
    return { error: error.message }
  }

  // We will handle MFA routing on the client side since it requires checking AAL level
  return { success: true, user: data.user, session: data.session }
}

export async function signup(email: string, password: string, captchaToken?: string) {
  const supabase = await createClient()

  const { data, error } = await supabase.auth.signUp({
    email,
    password,
    options: { captchaToken }
  })

  if (error) {
    return { error: error.message }
  }

  // Prevent auto-login: Sign out immediately if a session was created
  if (data.session) {
    await supabase.auth.signOut()
  }

  return { success: true }
}
