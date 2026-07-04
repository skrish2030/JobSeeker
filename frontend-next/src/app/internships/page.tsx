'use client';

import { useEffect, useState } from 'react';
import { createClient } from '@/utils/supabase/client';
import { toggleSavedJob } from '../actions';

export default function InternshipsPage() {
  const [jobs, setJobs] = useState<any[]>([]);
  const [savedJobIds, setSavedJobIds] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const supabase = createClient();

  useEffect(() => {
    fetchJobs();
    fetchSavedStatus();
  }, []);

  async function fetchSavedStatus() {
    const { data: { user } } = await supabase.auth.getUser();
    if (user) {
      const { data } = await supabase.from('user_saved_jobs').select('job_id').eq('user_id', user.id);
      if (data) {
        setSavedJobIds(new Set(data.map(d => d.job_id)));
      }
    }
  }

  async function fetchJobs() {
    setLoading(true);
    // Find jobs that have "intern" or "internship" in the title
    const { data, error } = await supabase
      .from('jobs')
      .select('*')
      .ilike('title', '%intern%')
      .order('posted_date', { ascending: false })
      .limit(50);
    
    if (error) {
      console.error('Error fetching internships:', error);
    } else {
      setJobs(data || []);
    }
    setLoading(false);
  }

  const handleToggleSave = async (jobId: string, isSaved: boolean) => {
    // Optimistic UI update
    const newSaved = new Set(savedJobIds);
    if (isSaved) newSaved.delete(jobId);
    else newSaved.add(jobId);
    setSavedJobIds(newSaved);
    
    try {
      await toggleSavedJob(jobId, isSaved);
    } catch (e) {
      // Revert if error
      const revertSaved = new Set(savedJobIds);
      if (isSaved) revertSaved.add(jobId);
      else revertSaved.delete(jobId);
      setSavedJobIds(revertSaved);
    }
  }

  return (
    <>
      <header className="h-20 border-b border-[#ffffff10] bg-[#120F1A]/80 backdrop-blur-md px-8 flex items-center sticky top-0 z-10 shrink-0">
        <h2 className="text-2xl font-black text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400">Internships Feed</h2>
      </header>

      <div className="flex-1 overflow-y-auto p-8 bg-[#0A0710]">
        <div className="max-w-6xl mx-auto">
          {loading ? (
            <div className="flex justify-center items-center py-20">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500"></div>
            </div>
          ) : jobs.length === 0 ? (
            <div className="flex flex-col justify-center items-center py-20 bg-[#15121E] border border-[#ffffff10] rounded-2xl">
              <svg className="w-16 h-16 text-gray-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M12 14l9-5-9-5-9 5 9 5zm0 0l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z" /></svg>
              <h3 className="text-xl font-bold text-gray-200 mb-2">No internships found</h3>
              <p className="text-gray-500">Check back later for new junior roles.</p>
            </div>
          ) : (
            <div className="grid gap-4">
              {jobs.map((job) => {
                const isSaved = savedJobIds.has(job.id);
                return (
                <div key={job.id} className="bg-[#15121E] border border-[#ffffff10] hover:border-indigo-500/50 p-6 rounded-2xl transition-all hover:shadow-[0_8px_30px_rgb(0,0,0,0.5)] hover:-translate-y-1 relative overflow-hidden group">
                  <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/10 rounded-full blur-3xl group-hover:bg-indigo-500/20 transition-all opacity-0 group-hover:opacity-100 pointer-events-none"></div>
                  
                  <div className="flex justify-between items-start mb-4 relative z-10">
                    <div>
                      <a href={job.job_url} target="_blank" rel="noreferrer" className="block group-hover:text-indigo-400 transition-colors">
                        <h3 className="text-xl font-bold text-gray-100 mb-1">{job.title}</h3>
                      </a>
                      <div className="text-indigo-300 font-medium">{job.company}</div>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <button 
                        onClick={() => handleToggleSave(job.id, isSaved)}
                        className={`p-2 rounded-lg transition-colors border ${isSaved ? 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30' : 'bg-[#ffffff05] text-gray-500 border-[#ffffff10] hover:bg-[#ffffff10] hover:text-gray-300'}`}
                        title={isSaved ? "Saved" : "Save Job"}
                      >
                        <svg className="w-5 h-5" fill={isSaved ? "currentColor" : "none"} stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={isSaved ? 1 : 2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" /></svg>
                      </button>
                    </div>
                  </div>
                  
                  <div className="flex flex-wrap gap-2 text-sm text-gray-400 relative z-10 mb-4">
                    <span className="bg-[#ffffff05] px-2 py-1 rounded-md border border-[#ffffff0a]">{job.location || 'Location Not Specified'}</span>
                    <span className="bg-[#ffffff05] px-2 py-1 rounded-md border border-[#ffffff0a] capitalize">{job.source_site}</span>
                    {job.posted_date && (
                      <span className="bg-[#ffffff05] px-2 py-1 rounded-md border border-[#ffffff0a]">
                        {new Date(job.posted_date).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                  
                  <p className="text-gray-400 text-sm line-clamp-2 relative z-10">
                    {job.description?.replace(/<[^>]*>?/gm, '') || 'No description provided.'}
                  </p>
                </div>
                )
              })}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
