import { NextResponse } from 'next/server';
import { createGoogleGenerativeAI } from '@ai-sdk/google';
import { createOpenAI } from '@ai-sdk/openai';
import { createAnthropic } from '@ai-sdk/anthropic';
import { generateText, generateObject } from 'ai';
import { z } from 'zod';

export async function POST(request: Request) {
  try {
    const { type, jobDescription, jobTitle, provider = 'gemini', model = 'gemini-2.5-flash', apiKey } = await request.json();

    if (!jobDescription || !jobTitle) {
      return NextResponse.json({ error: 'Missing job details' }, { status: 400 });
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

    if (type === 'score') {
      const { object } = await generateObject({
        model: aiModel,
        schema: z.object({
          score: z.number().describe('A score from 0 to 100 indicating how well a typical Mid/Senior Software Engineer matches this job.'),
          analysis: z.string().describe('A short 2-3 sentence explanation of the score, highlighting key skills required.')
        }),
        prompt: `You are a Senior Technical Recruiter and Hiring Manager with 30+ years of elite industry experience. Your ultimate goal is to assist the user in landing this job. Think logically, don't waste words, and be highly strategic. 
        
        Evaluate this job posting for a candidate:
        Job Title: ${jobTitle}
        
        Job Description:
        ${jobDescription}
        
        (Note: The user has not uploaded a custom resume yet, so assume they are a strong, highly capable mid-level candidate with modern tech stack experience.)`
      });

      return NextResponse.json(object);
    } 
    
    if (type === 'cover_letter') {
      const { text } = await generateText({
        model: aiModel,
        system: "You are a Senior Executive Career Coach with 30+ years of experience placing candidates at top-tier companies. Your writing is persuasive, deeply strategic, highly professional, and devoid of fluff.",
        prompt: `Write a concise, modern cover letter for the following job that will guarantee the candidate an interview.
        Job Title: ${jobTitle}
        
        Job Description:
        ${jobDescription}
        
        Assume the applicant is highly capable. Do not use generic buzzwords. Think logically about what the hiring manager actually cares about based on the job description. Keep it under 3 punchy paragraphs.`
      });

      return NextResponse.json({ coverLetter: text });
    }

    return NextResponse.json({ error: 'Invalid type' }, { status: 400 });
  } catch (error: any) {
    console.error('AI API Error:', error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
