'use server'

import { createClient } from '@/utils/supabase/server'
import { generateText } from 'ai'
import { createGoogleGenerativeAI } from '@ai-sdk/google'
import { createOpenAI } from '@ai-sdk/openai'
import { createAnthropic } from '@ai-sdk/anthropic'

export async function chatWithInterviewer(messages: {role: string, content: string}[], jobDescription: string) {
  const supabase = await createClient()
  
  const { data: { user }, error: userError } = await supabase.auth.getUser()
  if (userError || !user) throw new Error('Not authenticated')

  // Fetch the user's API key
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

  const systemPrompt = `You are an expert technical interviewer. 
The candidate is applying for a job with this description:
${jobDescription || 'Software Engineer'}

Conduct a realistic technical and behavioral interview. 
Ask one question at a time. Evaluate their answer, provide brief feedback, and then ask the next question.`

  try {
    const coreMessages: any[] = messages.map(msg => ({
      role: msg.role === 'user' ? 'user' : 'assistant',
      content: msg.content
    }))

    const { text } = await generateText({
      model,
      system: systemPrompt,
      messages: coreMessages,
    })

    return { text }
  } catch (e: any) {
    console.error('AI error:', e)
    throw new Error('Failed to chat: ' + e.message)
  }
}
