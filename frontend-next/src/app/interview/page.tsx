'use client';

import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { createClient } from '@/utils/supabase/client';

export default function InterviewPage() {
  const [jobDescription, setJobDescription] = useState('');
  const [questions, setQuestions] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [activeQuestion, setActiveQuestion] = useState(0);

  const generateQuestions = async () => {
    if (!jobDescription) return;
    setIsLoading(true);

    const provider = localStorage.getItem('ai_provider') || 'gemini';
    const model = localStorage.getItem('ai_model') || 'gemini-2.5-flash';
    const apiKey = localStorage.getItem('ai_api_key') || localStorage.getItem('gemini_api_key') || '';

    try {
      const response = await fetch('/api/ai/interview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ jobDescription, provider, model, apiKey })
      });
      const data = await response.json();
      if (response.status !== 200) {
        throw new Error(data.error || 'Failed to generate');
      }
      setQuestions(data.questions);
      setActiveQuestion(0);
    } catch (e) {
      console.error(e);
      alert('Failed to generate questions.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <header className="h-20 border-b border-[#ffffff10] bg-[#120F1A]/80 backdrop-blur-md px-8 flex items-center sticky top-0 z-10 shrink-0">
        <h2 className="text-2xl font-black text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400">AI Interview Assistant</h2>
      </header>

      <div className="flex-1 overflow-y-auto p-8 bg-[#0A0710]">
        <div className="max-w-4xl mx-auto">
          {!questions.length ? (
            <div className="bg-[#15121E] border border-[#ffffff10] p-8 rounded-3xl shadow-2xl">
              <div className="mb-8 text-center">
                <div className="w-20 h-20 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-6 shadow-[0_0_30px_rgba(99,102,241,0.4)]">
                  <span className="text-4xl">🎙️</span>
                </div>
                <h3 className="text-2xl font-bold text-gray-100 mb-2">Practice for your next role</h3>
                <p className="text-gray-400">Paste the job description below, and I will act as the hiring manager and grill you with 5 realistic interview questions!</p>
              </div>

              <textarea 
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                placeholder="Paste the full job description here..."
                className="w-full h-64 bg-[#0A0710] border border-[#ffffff10] rounded-xl p-4 text-gray-300 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none resize-none mb-6"
              />

              <button 
                onClick={generateQuestions}
                disabled={isLoading || !jobDescription}
                className="w-full py-4 bg-indigo-600 hover:bg-indigo-500 disabled:bg-[#ffffff05] disabled:text-gray-500 text-white font-bold rounded-xl transition-colors shadow-[0_0_15px_rgba(79,70,229,0.4)] flex justify-center items-center gap-2"
              >
                {isLoading ? (
                  <>
                    <div className="w-5 h-5 border-2 border-t-white border-white/20 rounded-full animate-spin"></div>
                    Analyzing Job Requirements...
                  </>
                ) : (
                  'Generate Interview Questions ✨'
                )}
              </button>
            </div>
          ) : (
            <div className="space-y-8 animate-in fade-in slide-in-from-bottom-8 duration-500">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-xl font-bold text-gray-200">Mock Interview Session</h3>
                <button 
                  onClick={() => setQuestions([])}
                  className="px-4 py-2 bg-[#ffffff05] hover:bg-[#ffffff10] border border-[#ffffff10] rounded-lg text-sm text-gray-300 transition-colors"
                >
                  End Session
                </button>
              </div>

              {questions.map((q, idx) => (
                <div 
                  key={idx} 
                  className={`bg-[#15121E] border ${idx === activeQuestion ? 'border-indigo-500 shadow-[0_0_20px_rgba(99,102,241,0.2)]' : 'border-[#ffffff10] opacity-60'} p-8 rounded-3xl transition-all cursor-pointer`}
                  onClick={() => setActiveQuestion(idx)}
                >
                  <div className="flex items-start gap-4">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold shrink-0 ${idx === activeQuestion ? 'bg-indigo-600 text-white' : 'bg-[#ffffff05] text-gray-500'}`}>
                      {idx + 1}
                    </div>
                    <div>
                      <h4 className={`text-lg ${idx === activeQuestion ? 'text-gray-100 font-bold' : 'text-gray-400 font-medium'}`}>{q}</h4>
                      {idx === activeQuestion && (
                        <div className="mt-6">
                          <textarea 
                            placeholder="Type your answer here, or practice answering out loud..."
                            className="w-full h-32 bg-[#0A0710] border border-[#ffffff10] rounded-xl p-4 text-gray-300 outline-none resize-none"
                          />
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
