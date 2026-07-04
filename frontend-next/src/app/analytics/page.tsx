import { createClient } from '@/utils/supabase/server'
import Image from 'next/image'

export const revalidate = 60 // Revalidate every minute

export default async function AnalyticsPage() {
  const supabase = await createClient()

  // Fetch the latest analytics insight
  const { data: insights } = await supabase
    .table('analytics_insights')
    .select('*')
    .eq('is_latest', true)
    .single()

  if (!insights) {
    return (
      <div className="min-h-screen bg-[#0F0C16] flex flex-col items-center justify-center p-6">
        <h1 className="text-3xl font-bold text-gray-100 mb-4">Market Analytics 📊</h1>
        <p className="text-gray-400">No analytics data available yet. Please run the JobSeeker Scraper action.</p>
      </div>
    )
  }

  const { total_jobs_analyzed, ai_market_summary, trending_skills, trending_titles, generated_at } = insights

  // Helper to find max count for relative bar widths
  const maxSkillCount = trending_skills?.length ? Math.max(...trending_skills.map((s: any) => s.count)) : 1
  const maxTitleCount = trending_titles?.length ? Math.max(...trending_titles.map((t: any) => t.count)) : 1

  return (
    <div className="min-h-screen bg-[#0F0C16] p-6 lg:p-12 font-sans">
      <div className="max-w-6xl mx-auto space-y-8">
        
        {/* Header */}
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 bg-[#1A1625] p-6 rounded-2xl border border-[#ffffff15] shadow-lg">
          <div>
            <h1 className="text-3xl font-bold text-white flex items-center gap-3">
              <span className="text-4xl">📈</span> Market Analytics
            </h1>
            <p className="text-gray-400 mt-2">
              Based on an analysis of <strong className="text-indigo-400">{total_jobs_analyzed}</strong> recently scraped jobs.
            </p>
          </div>
          <div className="text-sm text-gray-500 bg-[#2A2438] px-4 py-2 rounded-lg border border-[#ffffff10]">
            Last Updated: {new Date(generated_at).toLocaleString()}
          </div>
        </div>

        {/* AI Summary Section */}
        <div className="bg-gradient-to-br from-indigo-900/40 to-purple-900/20 p-8 rounded-3xl border border-indigo-500/30 shadow-[0_0_30px_rgba(79,70,229,0.15)] relative overflow-hidden">
          <div className="absolute top-0 right-0 p-8 opacity-20">
            <span className="text-8xl">✨</span>
          </div>
          <h2 className="text-xl font-bold text-indigo-300 mb-4 flex items-center gap-2">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
            Smart Market Decisioning
          </h2>
          <p className="text-gray-200 text-lg leading-relaxed max-w-4xl relative z-10">
            {ai_market_summary}
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Trending Skills Chart */}
          <div className="bg-[#1A1625] p-8 rounded-3xl border border-[#ffffff15] shadow-lg">
            <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
              <span className="text-2xl">💻</span> Top Requested Skills
            </h2>
            <div className="space-y-5">
              {trending_skills?.map((skill: any, idx: number) => {
                const widthPercent = (skill.count / maxSkillCount) * 100
                return (
                  <div key={idx} className="relative">
                    <div className="flex justify-between text-sm mb-1.5">
                      <span className="font-semibold text-gray-200">{skill.skill}</span>
                      <span className="text-gray-400 font-mono">{skill.count} mentions</span>
                    </div>
                    <div className="w-full bg-[#2A2438] rounded-full h-3.5 overflow-hidden border border-[#ffffff10]">
                      <div 
                        className="bg-gradient-to-r from-blue-500 to-indigo-500 h-full rounded-full transition-all duration-1000 ease-out"
                        style={{ width: `${widthPercent}%` }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Trending Roles Chart */}
          <div className="bg-[#1A1625] p-8 rounded-3xl border border-[#ffffff15] shadow-lg">
            <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
              <span className="text-2xl">🔥</span> Trending Tech Roles
            </h2>
            <div className="space-y-5">
              {trending_titles?.map((title: any, idx: number) => {
                const widthPercent = (title.count / maxTitleCount) * 100
                return (
                  <div key={idx} className="relative">
                    <div className="flex justify-between text-sm mb-1.5">
                      <span className="font-semibold text-gray-200">{title.title}</span>
                      <span className="text-gray-400 font-mono">{title.count} postings</span>
                    </div>
                    <div className="w-full bg-[#2A2438] rounded-full h-3.5 overflow-hidden border border-[#ffffff10]">
                      <div 
                        className="bg-gradient-to-r from-purple-500 to-pink-500 h-full rounded-full transition-all duration-1000 ease-out"
                        style={{ width: `${widthPercent}%` }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>

      </div>
    </div>
  )
}
