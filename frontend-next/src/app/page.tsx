"use client";

import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabase';

export default function Home() {
  const [jobs, setJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [locationTerm, setLocationTerm] = useState('');

  useEffect(() => {
    fetchJobs();
  }, []);

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

  return (
    <main className="min-h-screen bg-[#0A0710] text-gray-100 flex font-sans">
      {/* Sidebar */}
      <aside className="w-64 border-r border-[#ffffff10] bg-[#120F1A] flex flex-col hidden md:flex">
        <div className="p-6 border-b border-[#ffffff10] flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center font-bold text-lg shadow-[0_0_15px_rgba(99,102,241,0.5)]">JS</div>
          <h1 className="text-xl font-black tracking-wider bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-purple-400">JOBSEEKER</h1>
        </div>
        <nav className="flex-1 p-4 space-y-2">
          <a href="#" className="flex items-center gap-3 px-4 py-3 bg-indigo-500/10 text-indigo-400 rounded-xl font-semibold border border-indigo-500/20 transition-all shadow-[inset_0_1px_1px_rgba(255,255,255,0.05)]">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" /></svg>
            Job Feed
          </a>
          {/* Add more nav items here */}
        </nav>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        {/* Header */}
        <header className="h-20 border-b border-[#ffffff10] bg-[#120F1A]/80 backdrop-blur-md px-8 flex items-center justify-between sticky top-0 z-10">
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
          
          {/* Auth Button */}
          <div className="ml-8">
            <button className="px-4 py-2 border border-indigo-500/30 hover:bg-indigo-500/10 text-indigo-400 rounded-xl font-medium transition-colors">Sign In</button>
          </div>
        </header>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto p-8 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-indigo-900/10 via-[#0A0710] to-[#0A0710]">
          <div className="max-w-6xl mx-auto">
            <h2 className="text-2xl font-bold mb-6 text-gray-100">{jobs.length} jobs matching your criteria</h2>
            
            {loading ? (
              <div className="flex justify-center items-center py-20">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500"></div>
              </div>
            ) : (
              <div className="grid gap-4">
                {jobs.map((job) => (
                  <a href={job.job_url} target="_blank" rel="noreferrer" key={job.id} className="block group">
                    <div className="bg-[#15121E] border border-[#ffffff10] group-hover:border-indigo-500/50 p-6 rounded-2xl transition-all hover:shadow-[0_8px_30px_rgb(0,0,0,0.5)] hover:-translate-y-1 relative overflow-hidden">
                      {/* Gradient glow effect on hover */}
                      <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/10 rounded-full blur-3xl group-hover:bg-indigo-500/20 transition-all opacity-0 group-hover:opacity-100"></div>
                      
                      <div className="flex justify-between items-start mb-4 relative z-10">
                        <div>
                          <h3 className="text-xl font-bold text-gray-100 group-hover:text-indigo-400 transition-colors mb-1">{job.title}</h3>
                          <div className="text-indigo-300 font-medium">{job.company}</div>
                        </div>
                        {job.score >= 80 && (
                          <div className="px-3 py-1 bg-green-500/20 text-green-400 text-xs font-bold rounded-lg border border-green-500/30 flex items-center gap-1 shadow-[0_0_10px_rgba(34,197,94,0.2)]">
                            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/></svg>
                            {job.score}% Match
                          </div>
                        )}
                      </div>
                      
                      <div className="flex flex-wrap gap-2 text-sm text-gray-400 relative z-10 mb-4">
                        <span className="flex items-center gap-1 bg-[#ffffff05] px-2 py-1 rounded-md border border-[#ffffff0a]">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
                          {job.location || 'Location Not Specified'}
                        </span>
                        <span className="flex items-center gap-1 bg-[#ffffff05] px-2 py-1 rounded-md border border-[#ffffff0a] capitalize">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>
                          {job.source_site}
                        </span>
                        {job.posted_date && (
                          <span className="flex items-center gap-1 bg-[#ffffff05] px-2 py-1 rounded-md border border-[#ffffff0a]">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                            {new Date(job.posted_date).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                      
                      <p className="text-gray-400 text-sm line-clamp-2 relative z-10">
                        {job.description?.replace(/<[^>]*>?/gm, '') || 'No description provided.'}
                      </p>
                    </div>
                  </a>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}
