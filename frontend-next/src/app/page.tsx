'use client';

import { useEffect, useState } from 'react';
import { createClient } from '@/utils/supabase/client';
import { toggleSavedJob } from './actions';
import JobCard from '@/components/JobCard';

export default function Home() {
  const [jobs, setJobs] = useState<any[]>([]);
  const [savedJobIds, setSavedJobIds] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [locationTerm, setLocationTerm] = useState('');
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

  async function fetchJobs(search = '', loc = '') {
    setLoading(true);
    let query = supabase.from('jobs').select('*').order('posted_date', { ascending: false }).limit(50);
    
    if (search) {
      query = query.ilike('title', `%${search}%`);
    }
    if (loc) {
      query = query.ilike('location', `%${loc}%`);
    }

    const { data, error } = await query;
    if (error) {
      console.error('Error fetching jobs:', error);
    } else {
      setJobs(data || []);
    }
    setLoading(false);
  }

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchJobs(searchTerm, locationTerm);
  };

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
      <header className="h-20 border-b border-[#ffffff10] bg-[#120F1A]/80 backdrop-blur-md px-8 flex items-center justify-between sticky top-0 z-10 shrink-0">
        <form onSubmit={handleSearch} className="flex flex-1 max-w-3xl items-center gap-4 bg-[#1A1625] border border-[#ffffff15] p-2 rounded-2xl shadow-inner">
          <div className="flex-1 flex items-center px-4 gap-2 border-r border-[#ffffff15]">
            <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
            <input 
              type="text" 
              placeholder="Job title, keywords, or company" 
              className="bg-transparent border-none outline-none w-full text-sm text-gray-200 placeholder-gray-500"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <div className="flex-1 flex items-center px-4 gap-2">
            <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
            <input 
              type="text" 
              placeholder="City, state, or Remote" 
              className="bg-transparent border-none outline-none w-full text-sm text-gray-200 placeholder-gray-500"
              value={locationTerm}
              onChange={(e) => setLocationTerm(e.target.value)}
            />
          </div>
          <button type="submit" className="px-6 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-medium rounded-xl transition-colors shadow-[0_0_15px_rgba(79,70,229,0.4)]">
            Search
          </button>
        </form>
      </header>

      <div className="flex-1 overflow-y-auto p-8 bg-[#0A0710]">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-2xl font-bold mb-6 text-indigo-400">
            Showing {jobs.length} {searchTerm || locationTerm ? 'matching jobs' : 'recent jobs'}
          </h2>
          
          {loading ? (
            <div className="flex justify-center items-center py-20">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500"></div>
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
