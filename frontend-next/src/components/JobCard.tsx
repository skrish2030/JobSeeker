'use client';

import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { createClient } from '@/utils/supabase/client';

interface JobCardProps {
  job: any;
  isSaved: boolean;
  onToggleSave: (jobId: string, isSaved: boolean) => void;
}

export default function JobCard({ job, isSaved, onToggleSave }: JobCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  
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
    
    // Retrieve AI Settings
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
      // Create a pending application in the database
      const { error } = await supabase.from('applications').insert({
        user_id: user.id,
        job_id: job.id,
        status: 'pending'
      });

      if (error) throw error;
      setAutoApplyStatus('Queued for Auto-Apply');
    } catch (e: any) {
      console.error(e);
      // Fallback gracefully if table doesn't exist yet
      if (e.message?.includes("does not exist")) {
        setAutoApplyStatus("Database setup required (SQL Migration).");
      } else {
        setAutoApplyStatus('Failed to queue.');
      }
    } finally {
      setIsAutoApplying(false);
    }
  };

  return (
    <div className={`bg-[#15121E] border border-[#ffffff10] ${isExpanded ? 'border-indigo-500/50 shadow-[0_8px_30px_rgb(0,0,0,0.5)]' : 'hover:border-indigo-500/50 hover:shadow-[0_8px_30px_rgb(0,0,0,0.5)]'} p-6 rounded-2xl transition-all relative overflow-hidden group`}>
      <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/10 rounded-full blur-3xl group-hover:bg-indigo-500/20 transition-all opacity-0 group-hover:opacity-100 pointer-events-none"></div>
      
      <div className="flex justify-between items-start mb-4 relative z-10 cursor-pointer" onClick={() => setIsExpanded(!isExpanded)}>
        <div className="flex-1 pr-4">
          <h3 className="text-xl font-bold text-gray-100 mb-1 group-hover:text-indigo-400 transition-colors">{job.title}</h3>
          <div className="text-indigo-300 font-medium">{job.company}</div>
        </div>
        
        <div className="flex items-center gap-2">
          {job.score >= 80 && (
            <div className="px-3 py-1 bg-green-500/20 text-green-400 text-xs font-bold rounded-lg border border-green-500/30">
              {job.score}% Match
            </div>
          )}
          
          <button 
            onClick={(e) => { e.stopPropagation(); onToggleSave(job.id, isSaved); }}
            className={`p-2 rounded-lg transition-colors border ${isSaved ? 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30' : 'bg-[#ffffff05] text-gray-500 border-[#ffffff10] hover:bg-[#ffffff10] hover:text-gray-300'}`}
            title={isSaved ? "Saved" : "Save Job"}
          >
            <svg className="w-5 h-5" fill={isSaved ? "currentColor" : "none"} stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={isSaved ? 1 : 2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" /></svg>
          </button>
        </div>
      </div>
      
      <div className="flex flex-wrap gap-2 text-sm text-gray-400 relative z-10 mb-4 cursor-pointer" onClick={() => setIsExpanded(!isExpanded)}>
        <span className="bg-[#ffffff05] px-2 py-1 rounded-md border border-[#ffffff0a]">{job.location || 'Location Not Specified'}</span>
        <span className="bg-[#ffffff05] px-2 py-1 rounded-md border border-[#ffffff0a] capitalize">{job.source_site}</span>
        {job.posted_date && (
          <span className="bg-[#ffffff05] px-2 py-1 rounded-md border border-[#ffffff0a] flex items-center gap-1">
            <svg className="w-3.5 h-3.5 opacity-70" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
            Posted: {new Date(job.posted_date).toLocaleDateString()}
          </span>
        )}
        
        {(() => {
          if (!job.description) return null;
          const desc = job.description.toLowerCase();
          const noSponsor = ["no visa sponsorship", "will not sponsor", "does not sponsor", "unable to sponsor", "no h1b", "no c2c", "us citizen or green card", "us citizens only", "no sponsorship"];
          const yesSponsor = ["h1b", "h-1b", "visa sponsorship", "sponsor visa", "sponsorship available", "will sponsor"];
          
          if (noSponsor.some(kw => desc.includes(kw))) {
             return <span className="bg-red-500/10 text-red-400 px-2 py-1 rounded-md border border-red-500/20 font-medium">No H-1B Sponsorship</span>;
          }
          if (yesSponsor.some(kw => desc.includes(kw))) {
             return <span className="bg-green-500/10 text-green-400 px-2 py-1 rounded-md border border-green-500/20 font-medium flex items-center gap-1"><svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg> H-1B Sponsorship</span>;
          }
          return null;
        })()}
      </div>
      
      {!isExpanded ? (
        <p className="text-gray-400 text-sm line-clamp-2 relative z-10 cursor-pointer" onClick={() => setIsExpanded(true)}>
          {job.description?.replace(/<[^>]*>?/gm, '') || 'No description provided.'}
        </p>
      ) : (
        <div className="relative z-10 mt-6 pt-6 border-t border-[#ffffff10] animate-in fade-in slide-in-from-top-4 duration-300">
          
          {/* AI Features Bar */}
          <div className="flex flex-wrap gap-3 mb-6">
            <button onClick={() => handleGenerateAI('cover_letter')} disabled={isAiLoading} className="flex items-center gap-2 px-4 py-2 bg-[#2A2438] hover:bg-[#342D45] border border-[#ffffff10] text-gray-200 text-sm font-semibold rounded-xl transition-colors disabled:opacity-50">
              📝 Draft Cover Letter
            </button>
            <button onClick={handleAutoApply} disabled={isAutoApplying || !!autoApplyStatus} className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-bold rounded-xl transition-colors shadow-lg disabled:opacity-50 ml-auto">
              🚀 {autoApplyStatus || 'Auto Apply'}
            </button>
            <a href={job.job_url} target="_blank" rel="noreferrer" className="flex items-center gap-2 px-4 py-2 bg-transparent border border-indigo-500/30 hover:bg-indigo-500/10 text-indigo-400 text-sm font-semibold rounded-xl transition-colors">
              Manual Apply ↗
            </a>
          </div>

          {isAiLoading && (
            <div className="mb-6 p-4 rounded-xl bg-purple-900/20 border border-purple-500/30 flex items-center gap-3">
              <div className="w-5 h-5 border-2 border-t-purple-400 border-purple-400/20 rounded-full animate-spin"></div>
              <span className="text-purple-300 text-sm animate-pulse">AI is drafting your cover letter...</span>
            </div>
          )}

          {coverLetter && (
            <div className="mb-6 p-6 rounded-2xl bg-[#1A1625] border border-[#ffffff10]">
              <h4 className="text-sm font-bold text-gray-300 mb-3 uppercase tracking-wider flex items-center gap-2">
                <span>📝</span> AI Cover Letter
              </h4>
              <div className="prose prose-invert prose-sm max-w-none text-gray-400">
                <div className="whitespace-pre-wrap font-serif leading-relaxed bg-[#120F1A] p-6 rounded-xl border border-[#ffffff05] shadow-inner">{coverLetter}</div>
              </div>
            </div>
          )}

          <div className="prose prose-invert prose-sm max-w-none text-gray-300 mt-6">
            <h4 className="text-lg font-bold text-gray-200 mb-4 border-b border-[#ffffff10] pb-2">Full Job Description</h4>
            <ReactMarkdown>{job.description || 'No description provided.'}</ReactMarkdown>
          </div>
          
        </div>
      )}
    </div>
  );
}
