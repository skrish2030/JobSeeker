import { NextResponse } from 'next/server';
import { google } from '@ai-sdk/google';
import { generateObject } from 'ai';
import { z } from 'zod';

export async function POST(request: Request) {
  try {
    const { jobDescription } = await request.json();

    if (!jobDescription) {
      return NextResponse.json({ error: 'Missing job description' }, { status: 400 });
    }

    const { object } = await generateObject({
      model: google('gemini-2.5-flash'),
      schema: z.object({
        questions: z.array(z.string()).describe('A list of exactly 5 interview questions based on the job description.')
      }),
      prompt: `You are an expert hiring manager preparing to interview a candidate for the following job description:
      
      ${jobDescription}
      
      Generate exactly 5 highly realistic, challenging interview questions you would ask them. 
      Mix technical questions (if it's a technical role) with behavioral questions specific to the challenges implied by the job description.`
    });

    return NextResponse.json(object);
  } catch (error: any) {
    console.error('AI Interview Error:', error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
