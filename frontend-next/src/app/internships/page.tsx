'use client';

import { useEffect, useState } from 'react';
import { createClient } from '@/utils/supabase/client';
import { toggleSavedJob } from '../actions';
import JobCard from '@/components/JobCard';

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
              {jobs.map((job) => (
                <JobCard 
                  key={job.id} 
                  job={job} 
                  isSaved={savedJobIds.has(job.id)} 
                  onToggleSave={handleToggleSave} 
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
