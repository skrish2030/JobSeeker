import { createClient } from '@/utils/supabase/server'
import { saveSettings } from './actions'

export default async function SettingsPage() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()
  
  // Fetch current settings if they exist
  const { data: settings } = await supabase
    .from('user_settings')
    .select('*')
    .eq('user_id', user?.id)
    .single()

  return (
    <div className="flex-1 overflow-y-auto p-8 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-indigo-900/10 via-[#0A0710] to-[#0A0710]">
      <div className="max-w-4xl mx-auto">
        <h2 className="text-3xl font-black mb-2 text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400">Settings</h2>
        <p className="text-gray-400 mb-8">Configure your AI API keys and application preferences.</p>

        <div className="bg-[#120F1A]/80 backdrop-blur-xl border border-[#ffffff15] p-8 rounded-3xl shadow-[0_8px_32px_rgba(0,0,0,0.5)]">
          <h3 className="text-xl font-bold text-gray-100 mb-6 flex items-center gap-2">
            <svg className="w-6 h-6 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
            AI Features Configuration
          </h3>
          
          <div className="bg-indigo-500/10 border border-indigo-500/20 text-indigo-200 p-4 rounded-xl mb-6 text-sm">
            <strong>BYO-Key Architecture:</strong> To keep this application 100% free to host, all AI features (Interview Assistant and Resume Builder) run directly using your personal API key. Your key is stored securely and never shared.
          </div>

          <form action={saveSettings} className="space-y-6">
            <div className="flex flex-col gap-2">
              <label className="text-sm font-medium text-gray-300 ml-1">AI Provider</label>
              <select 
                name="ai_provider" 
                defaultValue={settings?.ai_provider || 'gemini'}
                className="w-full px-4 py-3 bg-[#1A1625] border border-[#ffffff10] rounded-xl outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/50 text-gray-100 transition-all appearance-none"
              >
                <option value="gemini">Google Gemini (Recommended)</option>
                <option value="openai">OpenAI (ChatGPT)</option>
                <option value="anthropic">Anthropic (Claude)</option>
              </select>
            </div>

            <div className="flex flex-col gap-2">
              <label className="text-sm font-medium text-gray-300 ml-1">API Key</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" /></svg>
                </div>
                <input
                  type="password"
                  name="ai_api_key"
                  defaultValue={settings?.ai_api_key || ''}
                  placeholder="Paste your API key here..."
                  className="w-full pl-10 pr-4 py-3 bg-[#1A1625] border border-[#ffffff10] rounded-xl outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/50 text-gray-100 placeholder-gray-600 transition-all shadow-inner"
                />
              </div>
              <p className="text-xs text-gray-500 ml-1 mt-1">Make sure you paste the correct API key for the provider you selected above.</p>
            </div>

            <div className="pt-4 border-t border-[#ffffff10]">
              <button
                type="submit"
                className="w-full sm:w-auto px-8 py-3 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-xl transition-all shadow-[0_0_15px_rgba(79,70,229,0.4)] hover:shadow-[0_0_25px_rgba(79,70,229,0.6)]"
              >
                Save Configuration
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
