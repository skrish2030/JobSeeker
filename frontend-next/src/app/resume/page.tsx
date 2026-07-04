'use client';

import { useState } from 'react';
import { generateResume } from './actions';
import Link from 'next/link';
import ReactMarkdown from 'react-markdown';

export default function ResumePage() {
  const [jobDescription, setJobDescription] = useState('');
  const [currentResume, setCurrentResume] = useState('');
  const [generatedDraft, setGeneratedDraft] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setGeneratedDraft('');

    try {
      const response = await generateResume(jobDescription, currentResume);
      setGeneratedDraft(response.text);
    } catch (err: any) {
      if (err.message.includes('API_KEY_MISSING')) {
        setError('Please configure your Gemini API Key in the Settings tab first.');
      } else {
        setError(err.message);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <header className="h-20 border-b border-[#ffffff10] bg-[#120F1A]/80 backdrop-blur-md px-8 flex items-center sticky top-0 z-10 shrink-0">
        <h2 className="text-2xl font-black text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400 flex items-center gap-2">
          <svg className="w-6 h-6 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
          AI Resume Builder
        </h2>
      </header>

      <div className="flex-1 overflow-y-auto p-8 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-indigo-900/10 via-[#0A0710] to-[#0A0710]">
        <div className="max-w-6xl mx-auto flex flex-col lg:flex-row gap-6">
          {/* Input Section */}
          <div className="flex-1 bg-[#120F1A]/80 backdrop-blur-xl border border-[#ffffff15] p-6 rounded-3xl shadow-[0_8px_32px_rgba(0,0,0,0.5)]">
            <form onSubmit={handleGenerate} className="flex flex-col gap-6 h-full">
              <div className="flex flex-col gap-2 flex-1">
                <label className="text-sm font-medium text-gray-300 ml-1 flex justify-between">
                  <span>Job Description</span>
                  <span className="text-gray-500 text-xs">Paste the target job description</span>
                </label>
                <textarea
                  required
                  value={jobDescription}
                  onChange={(e) => setJobDescription(e.target.value)}
                  className="w-full flex-1 min-h-[150px] p-4 bg-[#1A1625] border border-[#ffffff10] rounded-xl outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/50 text-gray-100 placeholder-gray-600 transition-all resize-none shadow-inner"
                  placeholder="Responsibilities, requirements, keywords..."
                />
              </div>

              <div className="flex flex-col gap-2 flex-1">
                <label className="text-sm font-medium text-gray-300 ml-1 flex justify-between">
                  <span>Current Resume</span>
                  <span className="text-gray-500 text-xs">Paste your base resume text</span>
                </label>
                <textarea
                  required
                  value={currentResume}
                  onChange={(e) => setCurrentResume(e.target.value)}
                  className="w-full flex-1 min-h-[150px] p-4 bg-[#1A1625] border border-[#ffffff10] rounded-xl outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/50 text-gray-100 placeholder-gray-600 transition-all resize-none shadow-inner"
                  placeholder="Experience, education, skills..."
                />
              </div>

              {error && (
                <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-xl text-sm">
                  {error}
                  {error.includes('Settings tab') && (
                    <Link href="/settings" className="block mt-2 underline font-bold">Go to Settings</Link>
                  )}
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full py-4 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-bold rounded-xl transition-all shadow-[0_0_20px_rgba(79,70,229,0.4)] disabled:opacity-50 disabled:cursor-not-allowed flex justify-center items-center gap-2"
              >
                {loading ? (
                  <>
                    <svg className="animate-spin h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Optimizing Resume...
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                    Generate ATS Resume
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Output Section */}
          <div className="flex-1 bg-[#120F1A]/80 backdrop-blur-xl border border-[#ffffff15] p-6 rounded-3xl shadow-[0_8px_32px_rgba(0,0,0,0.5)] flex flex-col h-[700px]">
            <h3 className="text-xl font-bold text-gray-100 mb-4 flex items-center gap-2 border-b border-[#ffffff10] pb-4">
              <svg className="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
              Optimized Draft
            </h3>
            
            <div className="flex-1 overflow-y-auto bg-[#1A1625] border border-[#ffffff10] rounded-xl p-6 text-gray-300 prose prose-invert max-w-none">
              {generatedDraft ? (
                <ReactMarkdown>{generatedDraft}</ReactMarkdown>
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-gray-500 opacity-50">
                  <svg className="w-16 h-16 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                  <p>Your optimized resume will appear here.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
