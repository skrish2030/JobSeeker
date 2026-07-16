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

  const [activeTab, setActiveTab] = useState('targeting');
  const [apiKey, setApiKey] = useState('');
  const [aiProvider, setAiProvider] = useState('gemini');
  const [aiModel, setAiModel] = useState('gemini-2.5-flash');

  const supabase = createClient();

  useEffect(() => {
    fetchSettings();
    setApiKey(localStorage.getItem('ai_api_key') || localStorage.getItem('gemini_api_key') || '');
    setAiProvider(localStorage.getItem('ai_provider') || 'gemini');
    setAiModel(localStorage.getItem('ai_model') || 'gemini-2.5-flash');
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
    
    if (activeTab === 'api') {
      localStorage.setItem('ai_api_key', apiKey);
      localStorage.setItem('ai_provider', aiProvider);
      localStorage.setItem('ai_model', aiModel);
      setSaveStatus('API settings saved locally!');
      setIsSaving(false);
      setTimeout(() => setSaveStatus(''), 3000);
      return;
    }
    
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) {
      setSaveStatus('You must be logged in to save settings.');
      setIsSaving(false);
      return;
    }

    try {
      const { error } = await supabase.from('user_settings').upsert({
        user_id: user.id,
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
        setSaveStatus("Database setup required.");
      } else {
        setSaveStatus('Failed to save settings.');
      }
    } finally {
      setIsSaving(false);
      setTimeout(() => setSaveStatus(''), 3000);
    }
  }

  const getModelOptions = () => {
    switch (aiProvider) {
      case 'openai':
        return [
          { id: 'gpt-4o', name: 'GPT-4o (Most Capable)' },
          { id: 'gpt-4o-mini', name: 'GPT-4o Mini (Fastest)' }
        ];
      case 'anthropic':
        return [
          { id: 'claude-3-5-sonnet-20240620', name: 'Claude 3.5 Sonnet' },
          { id: 'claude-3-haiku-20240307', name: 'Claude 3 Haiku' }
        ];
      case 'gemini':
      default:
        return [
          { id: 'gemini-2.5-flash', name: 'Gemini 2.5 Flash' },
          { id: 'gemini-1.5-pro', name: 'Gemini 1.5 Pro' }
        ];
    }
  };

  const handleProviderChange = (newProvider: string) => {
    setAiProvider(newProvider);
    // Reset model to default of new provider
    if (newProvider === 'openai') setAiModel('gpt-4o');
    else if (newProvider === 'anthropic') setAiModel('claude-3-5-sonnet-20240620');
    else setAiModel('gemini-2.5-flash');
  };

  return (
    <>
      <header className="h-20 border-b border-[#ffffff10] bg-[#120F1A]/80 backdrop-blur-md px-8 flex items-center sticky top-0 z-10 shrink-0">
        <h2 className="text-2xl font-black text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400">Settings & Preferences</h2>
      </header>

      <div className="flex-1 overflow-y-auto p-8 bg-[#0A0710]">
        <div className="max-w-3xl mx-auto space-y-8">
          
          {/* Tabs */}
          <div className="flex gap-2 p-1 bg-[#15121E] border border-[#ffffff10] rounded-xl w-fit">
            <button
              onClick={() => setActiveTab('targeting')}
              className={`px-5 py-2.5 rounded-lg font-semibold text-sm transition-all ${activeTab === 'targeting' ? 'bg-indigo-600 text-white shadow-lg' : 'text-gray-400 hover:text-gray-200 hover:bg-[#ffffff05]'}`}
            >
              🎯 Job Targeting
            </button>
            <button
              onClick={() => setActiveTab('api')}
              className={`px-5 py-2.5 rounded-lg font-semibold text-sm transition-all ${activeTab === 'api' ? 'bg-indigo-600 text-white shadow-lg' : 'text-gray-400 hover:text-gray-200 hover:bg-[#ffffff05]'}`}
            >
              🔑 API Keys
            </button>
          </div>

          <section className="bg-[#15121E] border border-[#ffffff10] p-8 rounded-3xl shadow-2xl relative overflow-hidden">
            <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/5 rounded-full blur-3xl pointer-events-none"></div>
            
            <div className="mb-6 border-b border-[#ffffff10] pb-4">
              <h3 className="text-xl font-bold text-gray-100 flex items-center gap-2">
                {activeTab === 'targeting' ? (
                  <><span>🎯</span> Job Targeting</>
                ) : (
                  <><span>🔑</span> AI Settings</>
                )}
              </h3>
              <p className="text-gray-400 text-sm mt-1">
                {activeTab === 'targeting' 
                  ? 'Configure what roles the scraper looks for and emails to you.'
                  : 'Select your preferred AI provider, model, and manage your API keys.'}
              </p>
            </div>

            {isLoading && activeTab === 'targeting' ? (
              <div className="flex justify-center py-10">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500"></div>
              </div>
            ) : (
              <form onSubmit={saveSettings} className="space-y-6 relative z-10">
                {activeTab === 'targeting' ? (
                  <>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <label className="block text-sm font-semibold text-gray-300 mb-2">Target Job Title</label>
                        <input 
                          type="text" 
                          value={jobTitle}
                          onChange={(e) => setJobTitle(e.target.value)}
                          placeholder="e.g. Software Engineer"
                          className="w-full bg-[#0A0710] border border-[#ffffff15] rounded-xl px-4 py-3 text-gray-200 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none transition-colors"
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
                  </>
                ) : (
                  <>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-4">
                      <div>
                        <label className="block text-sm font-semibold text-gray-300 mb-2">AI Provider</label>
                        <select 
                          value={aiProvider}
                          onChange={(e) => handleProviderChange(e.target.value)}
                          className="w-full bg-[#0A0710] border border-[#ffffff15] rounded-xl px-4 py-3 text-gray-200 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none transition-colors appearance-none"
                        >
                          <option value="gemini">Google Gemini</option>
                          <option value="openai">OpenAI ChatGPT</option>
                          <option value="anthropic">Anthropic Claude</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm font-semibold text-gray-300 mb-2">AI Model</label>
                        <input 
                          type="text"
                          list="model-options"
                          value={aiModel}
                          onChange={(e) => setAiModel(e.target.value)}
                          placeholder="Type or select model (e.g. gpt-4o)"
                          className="w-full bg-[#0A0710] border border-[#ffffff15] rounded-xl px-4 py-3 text-gray-200 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none transition-colors"
                        />
                        <datalist id="model-options">
                          {getModelOptions().map((opt) => (
                            <option key={opt.id} value={opt.id}>{opt.name}</option>
                          ))}
                        </datalist>
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm font-semibold text-gray-300 mb-2 capitalize">{aiProvider} API Key</label>
                      <input 
                        type="password" 
                        value={apiKey}
                        onChange={(e) => setApiKey(e.target.value)}
                        placeholder={aiProvider === 'openai' ? 'sk-...' : aiProvider === 'anthropic' ? 'sk-ant-...' : 'AIzaSy...'}
                        className="w-full bg-[#0A0710] border border-[#ffffff15] rounded-xl px-4 py-3 text-gray-200 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none transition-colors"
                      />
                      <p className="text-xs text-gray-500 mt-2 mb-3">Stored securely in your local browser storage for client-side AI features.</p>
                      
                      {aiProvider === 'gemini' && (
                        <div className="text-sm text-indigo-300 bg-indigo-500/10 p-3 rounded-lg border border-indigo-500/20">
                          <strong>Get your API key at <a href="https://aistudio.google.com/" target="_blank" rel="noreferrer" className="underline hover:text-indigo-200">Google AI Studio</a>.</strong> Gemini offers a generous free tier (15 requests/min) which is perfect for this app!
                        </div>
                      )}
                      {aiProvider === 'openai' && (
                        <div className="text-sm text-yellow-300 bg-yellow-500/10 p-3 rounded-lg border border-yellow-500/20">
                          <strong>Get your API key at <a href="https://platform.openai.com/api-keys" target="_blank" rel="noreferrer" className="underline hover:text-yellow-200">OpenAI Platform</a>.</strong> Note: You MUST have pre-funded API credits in your billing account (ChatGPT Plus subscription does not count).
                        </div>
                      )}
                      {aiProvider === 'anthropic' && (
                        <div className="text-sm text-orange-300 bg-orange-500/10 p-3 rounded-lg border border-orange-500/20">
                          <strong>Get your API key at <a href="https://console.anthropic.com/" target="_blank" rel="noreferrer" className="underline hover:text-orange-200">Anthropic Console</a>.</strong> Note: API credits are required. New accounts may receive free trial credits.
                        </div>
                      )}
                    </div>
                  </>
                )}

                <div className="flex items-center justify-between pt-4">
                  <div className={`text-sm font-medium ${saveStatus.includes('success') || saveStatus.includes('locally') ? 'text-green-400' : 'text-red-400'}`}>
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
