'use client';

import { useEffect, useState } from 'react';
import { createClient } from '@/utils/supabase/client';
import JobCard from '@/components/JobCard';

export default function InterestedPage() {
  const [jobs, setJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const supabase = createClient();

  useEffect(() => {
    fetchInterestedJobs();
  }, []);

  async function fetchInterestedJobs() {
    setLoading(true);
    const { data: { user } } = await supabase.auth.getUser();
    
    if (user) {
      // Query the junction table and join with jobs
      const { data, error } = await supabase
        .from('user_saved_jobs')
        .select(`
          job_id,
          jobs (*)
        `)
        .eq('user_id', user.id)
        .order('created_at', { ascending: false });
        
      if (error) {
        console.error('Error fetching interested jobs:', error);
      } else if (data) {
        // Extract the joined jobs
        const savedJobs = data.map((d: any) => d.jobs).filter(Boolean);
        setJobs(savedJobs);
      }
    }
    setLoading(false);
  }

  async function removeJob(jobId: string) {
    const { data: { user } } = await supabase.auth.getUser();
    if (user) {
      await supabase
        .from('user_saved_jobs')
        .delete()
        .match({ user_id: user.id, job_id: jobId });
      
      // Update UI
      setJobs(jobs.filter(j => j.id !== jobId));
    }
  }

  return (
    <>
      <header className="h-20 border-b border-[#ffffff10] bg-[#120F1A]/80 backdrop-blur-md px-8 flex items-center sticky top-0 z-10 shrink-0">
        <h2 className="text-2xl font-black text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400">Interested Jobs</h2>
      </header>

      <div className="flex-1 overflow-y-auto p-8 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-indigo-900/10 via-[#0A0710] to-[#0A0710]">
        <div className="max-w-6xl mx-auto">
          {loading ? (
            <div className="flex justify-center items-center py-20">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500"></div>
            </div>
          ) : jobs.length === 0 ? (
            <div className="flex flex-col justify-center items-center py-20 bg-[#15121E] border border-[#ffffff10] rounded-2xl">
              <svg className="w-16 h-16 text-gray-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" /></svg>
              <h3 className="text-xl font-bold text-gray-200 mb-2">No saved jobs yet</h3>
              <p className="text-gray-500">Jobs you star in the Home Feed will appear here.</p>
            </div>
          ) : (
            <div className="grid gap-4">
              {jobs.map((job) => (
                <JobCard 
                  key={job.id} 
                  job={job} 
                  isSaved={true} 
                  onToggleSave={removeJob} 
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
