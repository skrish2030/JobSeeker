'use server'

import { createClient } from '@/utils/supabase/server'
import { generateText } from 'ai'
import { createGoogleGenerativeAI } from '@ai-sdk/google'
import { createOpenAI } from '@ai-sdk/openai'
import { createAnthropic } from '@ai-sdk/anthropic'

export async function generateResume(jobDescription: string, currentResume: string) {
  const supabase = await createClient()
  
  const { data: { user }, error: userError } = await supabase.auth.getUser()
  if (userError || !user) throw new Error('Not authenticated')

  // Fetch the user's API key and provider
  const { data: settings } = await supabase
    .from('user_settings')
    .select('ai_api_key, ai_provider')
    .eq('user_id', user.id)
    .single()

  if (!settings || !settings.ai_api_key) {
    throw new Error('API_KEY_MISSING')
  }

  const provider = settings.ai_provider || 'gemini'
  let model;

  if (provider === 'gemini') {
    const google = createGoogleGenerativeAI({ apiKey: settings.ai_api_key })
    model = google('gemini-2.5-flash')
  } else if (provider === 'openai') {
    const openai = createOpenAI({ apiKey: settings.ai_api_key })
    model = openai('gpt-4o-mini')
  } else if (provider === 'anthropic') {
    const anthropic = createAnthropic({ apiKey: settings.ai_api_key })
    model = anthropic('claude-3-5-haiku-20241022')
  } else {
    throw new Error('Invalid AI provider')
  }

  const prompt = `You are an expert ATS Resume Optimizer.
I am applying for a job. Here is the job description:
${jobDescription}

Here is my current resume text:
${currentResume}

Please generate a highly tailored, ATS-friendly resume draft that highlights the experiences from my resume that best match the job description. Do not invent any fake experience. Format it cleanly in Markdown.`

  try {
    const { text } = await generateText({
      model,
      prompt,
    })
    return { text }
  } catch (e: any) {
    console.error('AI error:', e)
    throw new Error('Failed to generate resume: ' + e.message)
  }
}
