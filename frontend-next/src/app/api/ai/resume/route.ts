import { NextResponse } from 'next/server';
import { createGoogleGenerativeAI } from '@ai-sdk/google';
import { createOpenAI } from '@ai-sdk/openai';
import { createAnthropic } from '@ai-sdk/anthropic';
import { generateText } from 'ai';

export async function POST(request: Request) {
  try {
    const { text, provider = 'gemini', model = 'gemini-2.5-flash', apiKey } = await request.json();

    if (!text) {
      return NextResponse.json({ error: 'Missing text to polish' }, { status: 400 });
    }
    if (!apiKey) {
      return NextResponse.json({ error: 'Missing API Key in Settings' }, { status: 400 });
    }

    let aiModel;
    if (provider === 'openai') {
      const openai = createOpenAI({ apiKey });
      aiModel = openai(model);
    } else if (provider === 'anthropic') {
      const anthropic = createAnthropic({ apiKey });
      aiModel = anthropic(model);
    } else {
      const google = createGoogleGenerativeAI({ apiKey });
      aiModel = google(model);
    }

    const { text: polishedText } = await generateText({
      model: aiModel,
      system: "You are an elite Resume Writer and Career Coach. Your job is to take a rough bullet point or description and rewrite it to be highly professional, impactful, and optimized for Applicant Tracking Systems (ATS). Use strong action verbs and emphasize metrics and results. Output ONLY the polished text, with no conversational filler.",
      prompt: `Please rewrite the following resume bullet point to make it sound incredibly professional and impactful:\n\n${text}`
    });

    return NextResponse.json({ result: polishedText });
  } catch (error: any) {
    console.error('AI Resume Error:', error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
