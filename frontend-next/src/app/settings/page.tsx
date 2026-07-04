'use client';

import { useEffect, useState } from 'react';
import { createClient } from '@/utils/supabase/client';

export default function SettingsPage() {
  const [jobTitle, setJobTitle] = useState('Software Engineer');
  const [location, setLocation] = useState('Remote');
  const [emailNotifications, setEmailNotifications] = useState(true);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState('');

  const supabase = createClient();

  useEffect(() => {
    fetchSettings();
  }, []);

  async function fetchSettings() {
    setIsLoading(true);
    const { data: { user } } = await supabase.auth.getUser();
    if (user) {
      const { data } = await supabase.from('user_settings').select('*').eq('user_id', user.id).single();
      if (data) {
        setJobTitle(data.target_job_title || '');
        setLocation(data.target_location || '');
        setEmailNotifications(data.email_notifications);
      }
    }
    setIsLoading(false);
  }

  async function saveSettings(e: React.FormEvent) {
    e.preventDefault();
    setIsSaving(true);
    setSaveStatus('');
    
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) {
      setSaveStatus('You must be logged in to save settings.');
      setIsSaving(false);
      return;
    }

    try {
      const { error } = await supabase.from('user_settings').upsert({
        user_id: user.id,
        email: user.email,
        target_job_title: jobTitle,
        target_location: location,
        email_notifications: emailNotifications,
        updated_at: new Date().toISOString()
      });

      if (error) throw error;
      setSaveStatus('Settings saved successfully!');
    } catch (e: any) {
      console.error(e);
      if (e.message?.includes("does not exist")) {
        setSaveStatus("Database setup required (Run SQL Migration 05).");
      } else {
        setSaveStatus('Failed to save settings.');
      }
    } finally {
      setIsSaving(false);
      setTimeout(() => setSaveStatus(''), 3000);
    }
  }

  return (
    <>
      <header className="h-20 border-b border-[#ffffff10] bg-[#120F1A]/80 backdrop-blur-md px-8 flex items-center sticky top-0 z-10 shrink-0">
        <h2 className="text-2xl font-black text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400">Settings & Preferences</h2>
      </header>

      <div className="flex-1 overflow-y-auto p-8 bg-[#0A0710]">
        <div className="max-w-3xl mx-auto space-y-8">
          
          <section className="bg-[#15121E] border border-[#ffffff10] p-8 rounded-3xl shadow-2xl relative overflow-hidden">
            <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/5 rounded-full blur-3xl pointer-events-none"></div>
            
            <div className="mb-6 border-b border-[#ffffff10] pb-4">
              <h3 className="text-xl font-bold text-gray-100 flex items-center gap-2">
                <span>🎯</span> Job Targeting
              </h3>
              <p className="text-gray-400 text-sm mt-1">Configure what roles the scraper looks for and emails to you.</p>
            </div>

            {isLoading ? (
              <div className="flex justify-center py-10">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500"></div>
              </div>
            ) : (
              <form onSubmit={saveSettings} className="space-y-6 relative z-10">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-semibold text-gray-300 mb-2">Target Job Title</label>
                    <input 
                      type="text" 
                      value={jobTitle}
                      onChange={(e) => setJobTitle(e.target.value)}
                      placeholder="e.g. Software Engineer"
                      className="w-full bg-[#0A0710] border border-[#ffffff15] rounded-xl px-4 py-3 text-gray-200 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none transition-colors"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-gray-300 mb-2">Target Location</label>
                    <input 
                      type="text" 
                      value={location}
                      onChange={(e) => setLocation(e.target.value)}
                      placeholder="e.g. Remote, New York, NY"
                      className="w-full bg-[#0A0710] border border-[#ffffff15] rounded-xl px-4 py-3 text-gray-200 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none transition-colors"
                      required
                    />
                  </div>
                </div>

                <div className="flex items-center gap-4 p-4 bg-[#0A0710] border border-[#ffffff0a] rounded-xl">
                  <div className="flex-1">
                    <h4 className="text-gray-200 font-semibold">Daily Email Notifications</h4>
                    <p className="text-gray-500 text-sm">Receive a daily digest of new jobs matching your criteria.</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input 
                      type="checkbox" 
                      checked={emailNotifications}
                      onChange={(e) => setEmailNotifications(e.target.checked)}
                      className="sr-only peer" 
                    />
                    <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-500"></div>
                  </label>
                </div>

                <div className="flex items-center justify-between pt-4">
                  <div className={`text-sm font-medium ${saveStatus.includes('success') ? 'text-green-400' : 'text-red-400'}`}>
                    {saveStatus}
                  </div>
                  <button 
                    type="submit" 
                    disabled={isSaving}
                    className="px-6 py-3 bg-indigo-600 hover:bg-indigo-500 disabled:bg-[#ffffff10] disabled:text-gray-500 text-white font-bold rounded-xl transition-colors shadow-lg flex items-center gap-2"
                  >
                    {isSaving ? 'Saving...' : 'Save Preferences'}
                  </button>
                </div>
              </form>
            )}
          </section>

        </div>
      </div>
    </>
  );
}
