'use client';

import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { createClient } from '@/utils/supabase/client';

interface JobDetailProps {
  job: any;
  isSaved: boolean;
  onToggleSave: (jobId: string, isSaved: boolean) => void;
  onBack: () => void;
}

export default function JobDetail({ job, isSaved, onToggleSave, onBack }: JobDetailProps) {
  
  // AI States
  const [matchScore, setMatchScore] = useState<number | null>(null);
  const [aiAnalysis, setAiAnalysis] = useState<string | null>(null);
  const [coverLetter, setCoverLetter] = useState<string | null>(null);
  const [isAiLoading, setIsAiLoading] = useState(false);

  // Auto Apply State
  const [isAutoApplying, setIsAutoApplying] = useState(false);
  const [autoApplyStatus, setAutoApplyStatus] = useState<string | null>(null);

  const supabase = createClient();

  const handleGenerateAI = async (type: 'score' | 'cover_letter') => {
    setIsAiLoading(true);
    
    const provider = localStorage.getItem('ai_provider') || 'gemini';
    const model = localStorage.getItem('ai_model') || 'gemini-2.5-flash';
    const apiKey = localStorage.getItem('ai_api_key') || localStorage.getItem('gemini_api_key') || '';
    
    try {
      const response = await fetch('/api/ai', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          type, 
          jobDescription: job.description, 
          jobTitle: job.title,
          provider,
          model,
          apiKey
        })
      });
      
      const data = await response.json();
      if (response.status !== 200) {
        throw new Error(data.error || 'Failed to generate');
      }
      
      if (type === 'score') {
        setMatchScore(data.score);
        setAiAnalysis(data.analysis);
      } else {
        setCoverLetter(data.coverLetter);
      }
    } catch (e: any) {
      console.error(e);
      alert(`AI Generation failed: ${e.message}`);
    } finally {
      setIsAiLoading(false);
    }
  };

  const handleAutoApply = async () => {
    setIsAutoApplying(true);
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) {
      alert("Please log in to use Auto Apply");
      setIsAutoApplying(false);
      return;
    }

    try {
      const { error } = await supabase.from('applications').insert({
        user_id: user.id,
        job_id: job.id,
        status: 'pending'
      });

      if (error) throw error;
      setAutoApplyStatus('Queued for Auto-Apply');
    } catch (e: any) {
      console.error(e);
      if (e.message?.includes("does not exist")) {
        setAutoApplyStatus("Database setup required (SQL Migration).");
      } else {
        setAutoApplyStatus('Failed to queue.');
      }
    } finally {
      setIsAutoApplying(false);
    }
  };

  const displayDate = job.posted_date 
    ? new Date(job.posted_date).toLocaleDateString() 
    : (job.created_at ? new Date(job.created_at).toLocaleDateString() : 'Recent');

  return (
    <div className="bg-[#0A0710]">
      {/* Header Banner */}
      <div className="bg-[#15121E] border-b border-[#ffffff10] sticky top-0 z-20 shadow-2xl backdrop-blur-md">
        <div className="max-w-4xl mx-auto px-8 py-6">
          <button 
            onClick={onBack}
            className="flex items-center gap-2 text-indigo-400 hover:text-indigo-300 font-semibold mb-6 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
            Back to Jobs
          </button>

          <div className="flex justify-between items-start gap-4">
            <div>
              <h1 className="text-3xl font-black text-white mb-2">{job.title}</h1>
              <div className="flex items-center gap-4 text-lg">
                <span className="font-bold text-indigo-300">{job.company}</span>
                <span className="text-gray-500">•</span>
                <span className="text-gray-400">{job.location || 'Location Not Specified'}</span>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {job.score >= 80 && (
                <div className="px-4 py-2 bg-green-500/20 text-green-400 font-bold rounded-xl border border-green-500/30">
                  {job.score}% Match
                </div>
              )}
              <button 
                onClick={() => onToggleSave(job.id, isSaved)}
                className={`p-3 rounded-xl transition-all border shadow-lg ${isSaved ? 'bg-indigo-600 text-white border-indigo-500' : 'bg-[#1A1625] text-gray-400 border-[#ffffff15] hover:bg-[#ffffff10] hover:text-white'}`}
                title={isSaved ? "Saved" : "Save Job"}
              >
                <svg className="w-6 h-6" fill={isSaved ? "currentColor" : "none"} stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={isSaved ? 1 : 2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" /></svg>
              </button>
            </div>
          </div>

          <div className="flex flex-wrap gap-3 mt-6">
            <span className="bg-[#ffffff05] px-3 py-1.5 rounded-lg border border-[#ffffff0a] text-sm text-gray-400 capitalize">{job.source_site}</span>
            <span className="bg-[#ffffff05] px-3 py-1.5 rounded-lg border border-[#ffffff0a] text-sm text-gray-400 flex items-center gap-1">
              <svg className="w-4 h-4 opacity-70" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
              Posted: {displayDate}
            </span>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="max-w-4xl mx-auto px-8 py-10 grid grid-cols-3 gap-10">
        
        {/* Left Column: Job Description */}
        <div className="col-span-2">
          <h2 className="text-xl font-bold text-gray-200 mb-6 border-b border-[#ffffff10] pb-4">Job Description</h2>
          <div className="prose prose-invert max-w-none text-gray-300 font-sans leading-relaxed">
            <ReactMarkdown>{job.description || 'No description provided.'}</ReactMarkdown>
          </div>
        </div>

        {/* Right Column: AI Tools & Actions */}
        <div className="col-span-1 space-y-6">
          <div className="bg-[#15121E] p-6 rounded-2xl border border-[#ffffff10] sticky top-64 shadow-xl">
            <h3 className="text-sm font-bold text-gray-400 uppercase tracking-widest mb-4">Take Action</h3>
            
            <a href={job.job_url} target="_blank" rel="noreferrer" className="w-full flex justify-center items-center gap-2 px-4 py-3 bg-transparent border border-indigo-500 hover:bg-indigo-500/10 text-indigo-400 font-bold rounded-xl transition-colors mb-4">
              Apply on {job.source_site} ↗
            </a>

            <button 
              onClick={handleAutoApply} 
              disabled={isAutoApplying || !!autoApplyStatus} 
              className="w-full flex justify-center items-center gap-2 px-4 py-3 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-xl transition-colors shadow-[0_0_15px_rgba(79,70,229,0.3)] disabled:opacity-50 disabled:shadow-none mb-4"
            >
              🚀 {autoApplyStatus || '1-Click Auto Apply'}
            </button>

            <div className="border-t border-[#ffffff10] my-4"></div>

            <h3 className="text-sm font-bold text-gray-400 uppercase tracking-widest mb-4">AI Assistant</h3>
            <button 
              onClick={() => handleGenerateAI('cover_letter')} 
              disabled={isAiLoading} 
              className="w-full flex justify-center items-center gap-2 px-4 py-3 bg-[#2A2438] hover:bg-[#342D45] border border-[#ffffff10] text-gray-200 font-semibold rounded-xl transition-colors disabled:opacity-50"
            >
              📝 Draft Cover Letter
            </button>

            {isAiLoading && (
              <div className="mt-4 p-4 rounded-xl bg-purple-900/20 border border-purple-500/30 flex items-center gap-3">
                <div className="w-5 h-5 border-2 border-t-purple-400 border-purple-400/20 rounded-full animate-spin shrink-0"></div>
                <span className="text-purple-300 text-xs font-medium animate-pulse">AI is thinking...</span>
              </div>
            )}
          </div>
        </div>

      </div>

      {/* Cover Letter Modal Overlay (if generated) */}
      {coverLetter && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-8 bg-black/80 backdrop-blur-sm">
          <div className="bg-[#15121E] w-full max-w-3xl max-h-[80vh] rounded-2xl border border-[#ffffff20] shadow-2xl flex flex-col">
            <div className="flex justify-between items-center p-6 border-b border-[#ffffff10]">
              <h2 className="text-xl font-bold text-white flex items-center gap-2"><span>📝</span> AI Cover Letter</h2>
              <button onClick={() => setCoverLetter(null)} className="text-gray-400 hover:text-white p-2">✕</button>
            </div>
            <div className="p-8 overflow-y-auto font-serif text-gray-300 leading-relaxed text-lg whitespace-pre-wrap">
              {coverLetter}
            </div>
            <div className="p-6 border-t border-[#ffffff10] bg-[#1A1625] flex justify-end">
              <button 
                onClick={() => { navigator.clipboard.writeText(coverLetter); alert('Copied to clipboard!'); }}
                className="px-6 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-xl transition-colors"
              >
                Copy to Clipboard
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
