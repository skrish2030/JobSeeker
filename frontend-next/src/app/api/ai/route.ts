import { NextResponse } from 'next/server';
import { google } from '@ai-sdk/google';
import { generateText, generateObject } from 'ai';
import { z } from 'zod';

export async function POST(request: Request) {
  try {
    const { type, jobDescription, jobTitle } = await request.json();

    if (!jobDescription || !jobTitle) {
      return NextResponse.json({ error: 'Missing job details' }, { status: 400 });
    }

    if (type === 'score') {
      const { object } = await generateObject({
        model: google('gemini-2.5-flash'),
        schema: z.object({
          score: z.number().describe('A score from 0 to 100 indicating how well a typical Mid/Senior Software Engineer matches this job.'),
          analysis: z.string().describe('A short 2-3 sentence explanation of the score, highlighting key skills required.')
        }),
        prompt: `You are an expert technical recruiter. Evaluate this job posting for a Software Engineer candidate.
        Job Title: ${jobTitle}
        
        Job Description:
        ${jobDescription}
        
        (Note: The user has not uploaded a custom resume yet, so assume they are a strong mid-level Full Stack Developer with React, Node.js, Python, and SQL experience.)`
      });

      return NextResponse.json(object);
    } 
    
    if (type === 'cover_letter') {
      const { text } = await generateText({
        model: google('gemini-2.5-flash'),
        prompt: `Write a concise, professional, and modern cover letter for the following job.
        Job Title: ${jobTitle}
        
        Job Description:
        ${jobDescription}
        
        Assume the applicant is a passionate Software Engineer. Do not use generic buzzwords; make it punchy and highlight eagerness to learn their specific tech stack. Keep it under 3 paragraphs.`
      });

      return NextResponse.json({ coverLetter: text });
    }

    return NextResponse.json({ error: 'Invalid type' }, { status: 400 });
  } catch (error: any) {
    console.error('AI API Error:', error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
