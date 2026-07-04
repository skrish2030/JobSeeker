'use server'

import { createClient } from '@/utils/supabase/server'
import { revalidatePath } from 'next/cache'

export async function toggleSavedJob(jobId: string, isSaved: boolean) {
  const supabase = await createClient()
  
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) throw new Error('Not authenticated')

  if (isSaved) {
    // Unsave it
    await supabase
      .from('user_saved_jobs')
      .delete()
      .match({ user_id: user.id, job_id: jobId })
  } else {
    // Save it
    await supabase
      .from('user_saved_jobs')
      .insert({ user_id: user.id, job_id: jobId })
  }

  revalidatePath('/')
  revalidatePath('/interested')
}
