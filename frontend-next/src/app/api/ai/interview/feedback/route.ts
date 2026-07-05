import { NextResponse } from 'next/server';
import { createGoogleGenerativeAI } from '@ai-sdk/google';
import { createOpenAI } from '@ai-sdk/openai';
import { createAnthropic } from '@ai-sdk/anthropic';
import { generateObject } from 'ai';
import { z } from 'zod';

export async function POST(request: Request) {
  try {
    const { question, userAnswer, jobDescription, provider = 'gemini', model = 'gemini-2.5-flash', apiKey } = await request.json();

    if (!question || !userAnswer || !jobDescription) {
      return NextResponse.json({ error: 'Missing parameters' }, { status: 400 });
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

    const { object } = await generateObject({
      model: aiModel,
      schema: z.object({
        score: z.number().describe('A score from 1 to 10 evaluating the quality, relevance, and delivery of the user\'s answer.'),
        feedback: z.string().describe('Exactly 2-3 sentences of highly constructive, strategic feedback from a senior hiring manager. Speak directly to the candidate (e.g. "You did well on X, but you need to improve Y by...").')
      }),
      system: "You are an elite Senior Interview Panel with 30+ years of industry experience. Your absolute priority is to train, assist, and build the confidence of the user so they can successfully place in this job. Be smart, think logically, and do not burn tokens with unnecessary fluff.",
      prompt: `Based on your 30+ years of hiring experience, evaluate this candidate's answer.
      
      Job Description Context:
      ${jobDescription}
      
      Interview Question Asked:
      ${question}
      
      Candidate's Answer:
      ${userAnswer}
      
      Provide a brutal but fair score out of 10, and give exactly 2-3 sentences of highly actionable feedback on how they can improve their answer.`
    });

    return NextResponse.json(object);
  } catch (error: any) {
    console.error('AI Feedback Error:', error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
