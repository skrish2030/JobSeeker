'use client';

import { useEffect, useState } from 'react';
import { createClient } from '@/utils/supabase/client';
import { toggleSavedJob } from './actions';
import JobRow from '@/components/JobRow';
import JobDetail from '@/components/JobDetail';

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
    let activeSearch = search;
    let activeLoc = loc;

    // If no explicit search terms are provided, default to user's targeted settings!
    if (!search && !loc) {
      const { data: { user } } = await supabase.auth.getUser();
      if (user) {
        const { data: settings } = await supabase.from('user_settings').select('target_job_title, target_location').eq('user_id', user.id).single();
        if (settings) {
          if (settings.target_job_title) {
            activeSearch = settings.target_job_title;
            setSearchTerm(activeSearch); // Populate UI search bar so user sees the filter
          }
          if (settings.target_location) {
            activeLoc = settings.target_location;
            setLocationTerm(activeLoc); // Populate UI location bar
          }
        }
      }
    }

    let query = supabase.from('jobs').select('*').not('title', 'ilike', '%intern%').order('posted_date', { ascending: false }).limit(50);
    
    if (activeSearch) {
      query = query.ilike('title', `%${activeSearch}%`);
    }
    if (activeLoc) {
      query = query.ilike('location', `%${activeLoc}%`);
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

  const [selectedJob, setSelectedJob] = useState<any | null>(null);

  if (selectedJob) {
    return (
      <JobDetail 
        job={selectedJob} 
        isSaved={savedJobIds.has(selectedJob.id)} 
        onToggleSave={handleToggleSave} 
        onBack={() => setSelectedJob(null)} 
      />
    );
  }

  return (
    <div className="flex flex-col h-full bg-[#0A0710]">
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

      <div className="flex-1 overflow-y-auto p-8">
        <div className="max-w-5xl mx-auto">
          <div className="flex justify-between items-end mb-6 border-b border-[#ffffff10] pb-4">
            <h2 className="text-2xl font-bold text-indigo-400">
              {searchTerm || locationTerm ? 'Matching Jobs' : 'Recent Jobs'}
            </h2>
            <span className="text-sm font-medium text-gray-500 bg-[#ffffff05] px-3 py-1 rounded-lg border border-[#ffffff10]">
              Showing {jobs.length} results
            </span>
          </div>
          
          {loading ? (
            <div className="flex justify-center items-center py-20">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500"></div>
            </div>
          ) : (
            <div className="flex flex-col gap-3">
              {jobs.map((job) => (
                <JobRow 
                  key={job.id} 
                  job={job} 
                  isSaved={savedJobIds.has(job.id)} 
                  onToggleSave={handleToggleSave} 
                  onClick={() => setSelectedJob(job)}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
