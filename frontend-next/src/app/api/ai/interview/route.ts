import { NextResponse } from 'next/server';
import { createGoogleGenerativeAI } from '@ai-sdk/google';
import { createOpenAI } from '@ai-sdk/openai';
import { createAnthropic } from '@ai-sdk/anthropic';
import { generateObject } from 'ai';
import { z } from 'zod';

export async function POST(request: Request) {
  try {
    const { jobDescription, provider = 'gemini', model = 'gemini-2.5-flash', apiKey } = await request.json();

    if (!jobDescription) {
      return NextResponse.json({ error: 'Missing job description' }, { status: 400 });
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
        questions: z.array(z.string()).describe('A list of exactly 5 interview questions based on the job description.')
      }),
      system: "You are an elite Senior Interview Panel with 30+ years of industry experience. Your absolute priority is to train, assist, and build the confidence of the user so they can successfully place in this job. Be smart, think logically, and do not burn tokens with unnecessary fluff.",
      prompt: `Based on your 30+ years of hiring experience, analyze this job description:
      
      ${jobDescription}
      
      Generate exactly 5 highly realistic, challenging, and strategic interview questions you would ask them to train them effectively. 
      Mix technical questions (if applicable) with behavioral questions specific to the core challenges of this role.`
    });

    return NextResponse.json(object);
  } catch (error: any) {
    console.error('AI Interview Error:', error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
