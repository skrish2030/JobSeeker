import { login, signup } from './actions'
import { redirect } from 'next/navigation'
import { createClient } from '@/utils/supabase/server'

export default async function LoginPage({
  searchParams,
}: {
  searchParams: { error?: string }
}) {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  if (user) {
    redirect('/')
  }

  return (
    <main className="min-h-screen bg-[#0A0710] flex items-center justify-center font-sans p-4 relative overflow-hidden">
      {/* Background decorations */}
      <div className="absolute top-[-10%] left-[-10%] w-96 h-96 bg-indigo-600/20 rounded-full blur-[120px] pointer-events-none"></div>
      <div className="absolute bottom-[-10%] right-[-10%] w-96 h-96 bg-purple-600/20 rounded-full blur-[120px] pointer-events-none"></div>

      <div className="w-full max-w-md relative z-10">
        <div className="bg-[#120F1A]/80 backdrop-blur-xl border border-[#ffffff15] p-8 rounded-3xl shadow-[0_8px_32px_rgba(0,0,0,0.5)]">
          
          <div className="flex items-center justify-center gap-3 mb-8">
            <div className="w-12 h-12 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center font-bold text-xl text-white shadow-[0_0_15px_rgba(99,102,241,0.5)]">JS</div>
            <h1 className="text-2xl font-black tracking-wider bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-purple-400">JOBSEEKER</h1>
          </div>

          <h2 className="text-xl font-bold text-gray-100 text-center mb-2">Welcome Back</h2>
          <p className="text-gray-400 text-center text-sm mb-8">Sign in to your account or create a new one to continue.</p>

          <form className="flex flex-col gap-5">
            <div className="flex flex-col gap-2">
              <label className="text-sm font-medium text-gray-300 ml-1" htmlFor="email">Email</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path></svg>
                </div>
                <input
                  id="email"
                  name="email"
                  type="email"
                  required
                  placeholder="you@example.com"
                  className="w-full pl-10 pr-4 py-3 bg-[#1A1625] border border-[#ffffff10] rounded-xl outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/50 text-gray-100 placeholder-gray-600 transition-all shadow-inner"
                />
              </div>
            </div>

            <div className="flex flex-col gap-2">
              <label className="text-sm font-medium text-gray-300 ml-1" htmlFor="password">Password</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path></svg>
                </div>
                <input
                  id="password"
                  name="password"
                  type="password"
                  required
                  placeholder="••••••••"
                  className="w-full pl-10 pr-4 py-3 bg-[#1A1625] border border-[#ffffff10] rounded-xl outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/50 text-gray-100 placeholder-gray-600 transition-all shadow-inner"
                />
              </div>
            </div>

            {searchParams?.error && (
              <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-3 rounded-lg text-sm text-center">
                {searchParams.error}
              </div>
            )}

            <div className="flex gap-3 mt-4">
              <button
                formAction={login}
                className="flex-1 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-3 rounded-xl transition-all shadow-[0_0_15px_rgba(79,70,229,0.4)] hover:shadow-[0_0_25px_rgba(79,70,229,0.6)]"
              >
                Sign In
              </button>
              <button
                formAction={signup}
                className="flex-1 bg-[#ffffff0a] border border-[#ffffff15] hover:bg-[#ffffff10] hover:border-indigo-500/30 text-gray-200 font-semibold py-3 rounded-xl transition-all"
              >
                Create Account
              </button>
            </div>
          </form>
          
          <div className="mt-8 text-center text-xs text-gray-500">
            Secure authentication powered by Supabase
          </div>
        </div>
      </div>
    </main>
  )
}
