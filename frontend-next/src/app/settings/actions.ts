'use server'

import { createClient } from '@/utils/supabase/server'
import { revalidatePath } from 'next/cache'

export async function saveSettings(formData: FormData) {
  const supabase = await createClient()
  
  const { data: { user }, error: userError } = await supabase.auth.getUser()
  if (userError || !user) throw new Error('Not authenticated')

  const aiProvider = formData.get('ai_provider') as string
  const aiApiKey = formData.get('ai_api_key') as string

  const { error } = await supabase
    .from('user_settings')
    .upsert({ 
      user_id: user.id, 
      ai_provider: aiProvider, 
      ai_api_key: aiApiKey,
      updated_at: new Date().toISOString()
    }, { 
      onConflict: 'user_id' 
    })

  if (error) {
    console.error('Error saving settings:', error)
    throw new Error('Failed to save settings')
  }

  revalidatePath('/settings')
}
