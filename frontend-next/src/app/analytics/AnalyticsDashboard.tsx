"use client"

import React, { useMemo, useState } from 'react'
import { BarChart, Bar, LineChart, Line, AreaChart, Area, Legend, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, CartesianGrid } from 'recharts'
import { TrendingUp, Briefcase, Code, Building, MessageSquare, AlertCircle, Calendar, Shield, Cpu, Cloud, Database, FileCode, CheckCircle2, DollarSign, Award, GraduationCap, ArrowRight, Activity } from 'lucide-react'

const COLORS = ['#6366f1', '#a855f7', '#ec4899', '#f43f5e', '#f59e0b']

export default function AnalyticsDashboard({ insights, marketFeed, scrapeTrend }: { insights: any, marketFeed: any[], scrapeTrend: any[] }) {
  const [timeRange, setTimeRange] = useState<number>(30) // Default 30 days
  const [selectedCareerSlug, setSelectedCareerSlug] = useState<string | null>(null)
  const { total_jobs_analyzed, ai_market_summary, trending_skills, trending_titles, top_companies, generated_at } = insights

  const filteredTrend = useMemo(() => {
    if (!scrapeTrend) return []
    const sliced = scrapeTrend.slice(-timeRange)
    return sliced.map(s => ({
      ...s,
      date: s.date.substring(5) // MM-DD for clean chart labels
    }))
  }, [scrapeTrend, timeRange])

  const futureKeys = useMemo(() => {
    let aiData: any = {}
    try {
      if (ai_market_summary && ai_market_summary.includes('{')) {
        aiData = JSON.parse(ai_market_summary)
      }
    } catch(e) {}
    if (!aiData.future_trends || aiData.future_trends.length === 0) return []
    return Object.keys(aiData.future_trends[0]).filter(k => k !== 'year')
  }, [ai_market_summary])

  // Parse Algorithmic JSON
  let algoData: any = { market_mood: "Analyzing market mood...", trending_topics: [], source_metrics: null, career_insights: [] }
  try {
    if (ai_market_summary && ai_market_summary.includes('{')) {
      algoData = JSON.parse(ai_market_summary)
    } else if (ai_market_summary) {
       algoData.market_mood = ai_market_summary
    }
  } catch (e) {
    console.error("Failed to parse Algorithmic JSON", e)
  }

  const activeCareer = useMemo(() => {
    if (!algoData.career_insights || algoData.career_insights.length === 0) return null
    if (selectedCareerSlug) {
      return algoData.career_insights.find((c: any) => c.slug === selectedCareerSlug) || algoData.career_insights[0]
    }
    return algoData.career_insights[0]
  }, [algoData.career_insights, selectedCareerSlug])

  const getCareerIcon = (slug: string) => {
    switch (slug) {
      case 'ai-engineer': return <Cpu className="w-5 h-5 text-emerald-400" />
      case 'cybersecurity': return <Shield className="w-5 h-5 text-red-400" />
      case 'cloud-engineer': return <Cloud className="w-5 h-5 text-sky-400" />
      case 'data-scientist': return <Activity className="w-5 h-5 text-purple-400" />
      case 'software-engineer': return <FileCode className="w-5 h-5 text-blue-400" />
      case 'data-engineer': return <Database className="w-5 h-5 text-pink-400" />
      default: return <Briefcase className="w-5 h-5 text-indigo-400" />
    }
  }

  // Smart dynamic YAxis width calculator based on the longest string in the data
  const getDynamicWidth = (data: any[], key: string) => {
    if (!data || data.length === 0) return 100;
    const maxLen = Math.max(...data.map(d => String(d[key]).length));
    // Roughly 7.5px per character, bounded between 80px and 220px
    return Math.min(Math.max(maxLen * 7.5, 80), 220);
  }

  return (
    <div className="min-h-screen bg-[#0F0C16] p-6 lg:p-12 font-sans text-gray-200">
      <div className="max-w-7xl mx-auto space-y-8">
        
        {/* Header */}
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 bg-[#1A1625] p-6 rounded-2xl border border-[#ffffff15] shadow-lg">
          <div>
            <h1 className="text-3xl font-bold text-white flex items-center gap-3">
              <TrendingUp className="w-8 h-8 text-indigo-500" /> Market Analytics
            </h1>
            <div className="flex flex-wrap items-center gap-4 mt-3">
              <p className="text-gray-400">
                Based on <strong className="text-indigo-400">{total_jobs_analyzed}</strong> recently scraped jobs.
              </p>
              {algoData.source_metrics && (
                <div className="flex gap-3">
                  <span className="bg-red-500/20 text-red-300 text-xs px-2 py-1 rounded-md border border-red-500/30">
                    {algoData.source_metrics.youtube} YouTube Videos
                  </span>
                  <span className="bg-orange-500/20 text-orange-300 text-xs px-2 py-1 rounded-md border border-orange-500/30">
                    {algoData.source_metrics.reddit} Reddit Threads
                  </span>
                </div>
              )}
            </div>
          </div>
          <div className="text-sm text-gray-500 bg-[#2A2438] px-4 py-2 rounded-lg border border-[#ffffff10]">
            Last Updated: {new Date(generated_at).toLocaleString()}
          </div>
        </div>

        {/* Algorithmic Prediction Summary */}
        <div className="bg-gradient-to-br from-emerald-900/30 to-teal-900/20 p-8 rounded-3xl border border-emerald-500/30 shadow-[0_0_30px_rgba(16,185,129,0.1)] relative overflow-hidden flex gap-4 items-start">
          <AlertCircle className="w-10 h-10 text-emerald-400 flex-shrink-0" />
          <div>
            <h2 className="text-xl font-bold text-emerald-300 mb-2">Algorithmic Market Predictions</h2>
            <p className="text-gray-200 text-lg leading-relaxed">{algoData.market_mood}</p>
          </div>
        </div>

        {/* Career Intelligence comparison board */}
        {algoData.career_insights && algoData.career_insights.length > 0 && (
          <div className="bg-[#1A1625] p-6 lg:p-8 rounded-3xl border border-[#ffffff15] shadow-lg flex flex-col gap-6">
            <div>
              <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                <GraduationCap className="w-7 h-7 text-indigo-500" /> Career Intelligence Hub (2030 predictions)
              </h2>
              <p className="text-gray-400 mt-2 text-sm">Select a tech career to view its required skills roadmap, target certificates, free courses, and salary curves.</p>
            </div>
            
            <div className="overflow-x-auto rounded-2xl border border-[#ffffff10] bg-[#120F1A]">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-[#ffffff10] text-gray-400 text-xs font-semibold uppercase tracking-wider bg-[#1c1829]">
                    <th className="py-4 px-6">Career Profile</th>
                    <th className="py-4 px-6">5-Yr Growth</th>
                    <th className="py-4 px-6">AI Risk</th>
                    <th className="py-4 px-6">Starting Pay</th>
                    <th className="py-4 px-6">Overall Future Rating</th>
                    <th className="py-4 px-6">Global Demand</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#ffffff08] text-sm">
                  {algoData.career_insights.map((career: any) => {
                    const isSelected = activeCareer && activeCareer.slug === career.slug
                    return (
                      <tr 
                        key={career.slug} 
                        onClick={() => setSelectedCareerSlug(career.slug)}
                        className={`cursor-pointer transition-all hover:bg-[#ffffff05] ${isSelected ? 'bg-indigo-600/10 border-l-4 border-indigo-500' : ''}`}
                      >
                        <td className="py-4 px-6 font-semibold text-white flex items-center gap-3">
                          {getCareerIcon(career.slug)}
                          {career.name}
                        </td>
                        <td className="py-4 px-6 text-yellow-500 text-base font-bold">
                          {"★".repeat(career.growth)}
                        </td>
                        <td className="py-4 px-6">
                          <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${career.ai_risk === 'Low' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'}`}>
                            {career.ai_risk}
                          </span>
                        </td>
                        <td className="py-4 px-6 text-emerald-400 font-mono font-bold">{career.salary}</td>
                        <td className="py-4 px-6 text-indigo-400 font-bold">{career.future_score.overall}/100</td>
                        <td className="py-4 px-6 text-gray-300 font-semibold">{career.demand}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>

            {/* Career details deep-dive drawer */}
            {activeCareer && (
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 border-t border-[#ffffff10] pt-8 mt-4">
                
                {/* Left side: Future score stats and learning roadmap */}
                <div className="lg:col-span-7 space-y-6">
                  <div className="flex items-center gap-3">
                    {getCareerIcon(activeCareer.slug)}
                    <h3 className="text-xl font-bold text-white">{activeCareer.name} Intelligence Breakdown</h3>
                  </div>

                  {/* Future score radial representation */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                    <div className="bg-[#120F1A] p-4 rounded-2xl border border-[#ffffff08] flex flex-col items-center">
                      <span className="text-xs text-gray-400 mb-1">Demand</span>
                      <strong className="text-xl font-bold text-sky-400">{activeCareer.future_score.demand}</strong>
                    </div>
                    <div className="bg-[#120F1A] p-4 rounded-2xl border border-[#ffffff08] flex flex-col items-center">
                      <span className="text-xs text-gray-400 mb-1">Salary Grade</span>
                      <strong className="text-xl font-bold text-emerald-400">{activeCareer.future_score.salary}</strong>
                    </div>
                    <div className="bg-[#120F1A] p-4 rounded-2xl border border-[#ffffff08] flex flex-col items-center">
                      <span className="text-xs text-gray-400 mb-1">AI Safety</span>
                      <strong className="text-xl font-bold text-amber-400">{activeCareer.future_score.ai_safety}</strong>
                    </div>
                    <div className="bg-[#120F1A] p-4 rounded-2xl border border-[#ffffff08] flex flex-col items-center">
                      <span className="text-xs text-gray-400 mb-1">Overall Future</span>
                      <strong className="text-xl font-bold text-indigo-400">{activeCareer.future_score.overall}</strong>
                    </div>
                  </div>

                  {/* Skills roadmap SVG Flowchart layout */}
                  <div className="bg-[#120F1A] p-6 rounded-3xl border border-[#ffffff08]">
                    <h4 className="text-sm font-bold text-white mb-4 uppercase tracking-wider flex items-center gap-2">
                      <Code className="w-4 h-4 text-indigo-400" /> Step-by-Step Learning Roadmap
                    </h4>
                    <div className="flex flex-wrap items-center gap-3">
                      {activeCareer.roadmap.map((step: string, idx: number) => {
                        const isLast = idx === activeCareer.roadmap.length - 1
                        return (
                          <React.Fragment key={step}>
                            <div className="bg-[#1c1829] px-4 py-2.5 rounded-xl border border-[#ffffff10] text-sm text-gray-200 font-medium">
                              {step}
                            </div>
                            {!isLast && <ArrowRight className="w-4 h-4 text-indigo-500/50 flex-shrink-0" />}
                          </React.Fragment>
                        )
                      })}
                    </div>
                  </div>

                  {/* Best Free Learning resources */}
                  <div className="bg-[#120F1A] p-6 rounded-3xl border border-[#ffffff08]">
                    <h4 className="text-sm font-bold text-white mb-4 uppercase tracking-wider flex items-center gap-2">
                      <GraduationCap className="w-4 h-4 text-emerald-400" /> Top Free Learning Resources
                    </h4>
                    <div className="space-y-4">
                      {activeCareer.free_learning.map((resource: any) => (
                        <div key={resource.skill} className="flex justify-between items-start gap-4 pb-3 border-b border-[#ffffff05] last:border-0 last:pb-0">
                          <div>
                            <span className="text-sm font-semibold text-white">{resource.skill}</span>
                            <div className="flex flex-wrap gap-2 mt-1">
                              {resource.resources.map((res: string) => (
                                <span key={res} className="bg-emerald-500/10 text-emerald-300 text-xs px-2 py-0.5 rounded border border-emerald-500/20 font-medium">
                                  {res}
                                </span>
                              ))}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Right side: Salary Progression Chart and Certs/Bootcamp Rankings */}
                <div className="lg:col-span-5 space-y-6">
                  {/* Salary progression bar chart */}
                  <div className="bg-[#120F1A] p-6 rounded-3xl border border-[#ffffff08] h-[250px] flex flex-col">
                    <h4 className="text-sm font-bold text-white mb-4 uppercase tracking-wider flex items-center gap-2">
                      <DollarSign className="w-4 h-4 text-emerald-400" /> Salary Growth Progression (Annual)
                    </h4>
                    <div className="flex-1 w-full min-h-[150px]">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={[
                          { stage: 'Junior', salary: parseInt(activeCareer.salary_trend.junior.replace('$', '').replace('k', '')) * 1000 },
                          { stage: 'Mid', salary: parseInt(activeCareer.salary_trend.mid.replace('$', '').replace('k', '')) * 1000 },
                          { stage: 'Senior', salary: parseInt(activeCareer.salary_trend.senior.replace('$', '').replace('k', '')) * 1000 },
                          { stage: 'Principal', salary: parseInt(activeCareer.salary_trend.principal.replace('$', '').replace('k', '')) * 1000 }
                        ]}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#ffffff05" vertical={false} />
                          <XAxis dataKey="stage" stroke="#6b7280" tick={{fill: '#e5e7eb', fontSize: 11}} />
                          <YAxis stroke="#6b7280" tickFormatter={(v) => `$${v/1000}k`} tick={{fill: '#e5e7eb', fontSize: 11}} />
                          <Tooltip formatter={(value: any) => [`$${value?.toLocaleString()}`, 'Annual Salary']} contentStyle={{backgroundColor: '#1c1829', borderColor: '#ffffff10', borderRadius: '8px'}} />
                          <Bar dataKey="salary" fill="#10b981" radius={[4, 4, 0, 0]} barSize={36} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  {/* Certificates rankings table */}
                  <div className="bg-[#120F1A] p-6 rounded-3xl border border-[#ffffff08]">
                    <h4 className="text-sm font-bold text-white mb-4 uppercase tracking-wider flex items-center gap-2">
                      <Award className="w-4 h-4 text-yellow-400" /> Curated Certificate Recommendations
                    </h4>
                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs border-collapse">
                        <thead>
                          <tr className="border-b border-[#ffffff10] text-gray-400 font-semibold uppercase tracking-wider bg-[#1c1829]">
                            <th className="py-2 px-3">Certificate</th>
                            <th className="py-2 px-3">Value</th>
                            <th className="py-2 px-3">Cost</th>
                            <th className="py-2 px-3">Recognition</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-[#ffffff05] text-gray-300">
                          {activeCareer.certificates.map((cert: any) => (
                            <tr key={cert.certificate} className="hover:bg-[#ffffff02]">
                              <td className="py-2.5 px-3 font-medium text-white">{cert.certificate}</td>
                              <td className="py-2.5 px-3 text-yellow-500 font-bold">{cert.value}</td>
                              <td className="py-2.5 px-3 text-gray-400">{cert.cost}</td>
                              <td className="py-2.5 px-3 text-emerald-400 font-semibold">{cert.recognition}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* Bootcamps metrics */}
                  <div className="bg-[#120F1A] p-6 rounded-3xl border border-[#ffffff08]">
                    <h4 className="text-sm font-bold text-white mb-4 uppercase tracking-wider flex items-center gap-2">
                      <GraduationCap className="w-4 h-4 text-sky-400" /> Ranked Professional Bootcamps
                    </h4>
                    <div className="space-y-4">
                      {activeCareer.bootcamps.map((camp: any) => (
                        <div key={camp.name} className="flex justify-between items-center gap-4 pb-3 border-b border-[#ffffff05] last:border-0 last:pb-0">
                          <div>
                            <span className="text-sm font-semibold text-white">{camp.name}</span>
                            <div className="text-xs text-gray-400 mt-0.5">Duration: {camp.time} | Cost: {camp.cost}</div>
                          </div>
                          <span className="bg-sky-500/10 text-sky-300 text-xs px-2 py-1 rounded border border-sky-500/20 font-bold">
                            ROI: {camp.roi}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Daily Scrape Volume Trend (Full Width) */}
        <div className="bg-[#1A1625] p-6 lg:p-8 rounded-3xl border border-[#ffffff15] shadow-lg flex flex-col h-[400px]">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <Calendar className="w-6 h-6 text-indigo-500" /> Daily Jobs Scraped Volume
            </h2>
            {/* Time range buttons */}
            <div className="flex gap-1.5 p-1 bg-[#120F1A] border border-[#ffffff10] rounded-xl w-fit">
              <button
                onClick={() => setTimeRange(7)}
                className={`px-3 py-1.5 rounded-lg font-semibold text-xs transition-all ${timeRange === 7 ? 'bg-indigo-600 text-white shadow-lg' : 'text-gray-400 hover:text-gray-200'}`}
              >
                7 Days
              </button>
              <button
                onClick={() => setTimeRange(30)}
                className={`px-3 py-1.5 rounded-lg font-semibold text-xs transition-all ${timeRange === 30 ? 'bg-indigo-600 text-white shadow-lg' : 'text-gray-400 hover:text-gray-200'}`}
              >
                30 Days
              </button>
              <button
                onClick={() => setTimeRange(90)}
                className={`px-3 py-1.5 rounded-lg font-semibold text-xs transition-all ${timeRange === 90 ? 'bg-indigo-600 text-white shadow-lg' : 'text-gray-400 hover:text-gray-200'}`}
              >
                90 Days
              </button>
            </div>
          </div>
          
          <div className="flex-1 w-full min-h-[250px]">
            {filteredTrend.length === 0 ? (
              <div className="h-full flex items-center justify-center text-gray-500">No scrape trend data available.</div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={filteredTrend} margin={{ top: 10, right: 30, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorScrape" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4}/>
                      <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
                  <XAxis dataKey="date" stroke="#6b7280" tick={{fill: '#e5e7eb', fontSize: 11}} />
                  <YAxis stroke="#6b7280" tick={{fill: '#e5e7eb', fontSize: 11}} />
                  <Tooltip contentStyle={{backgroundColor: '#1A1625', borderColor: '#ffffff20', borderRadius: '8px'}} />
                  <Area type="monotone" dataKey="count" name="Jobs Scraped" stroke="#6366f1" strokeWidth={3} fillOpacity={1} fill="url(#colorScrape)" />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Main Grid for Visualizations */}
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-8">
          
          {/* Top Skills Chart */}
          <div className="bg-[#1A1625] p-6 rounded-3xl border border-[#ffffff15] shadow-lg flex flex-col h-[400px]">
            <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
              <Code className="w-6 h-6 text-pink-500" /> Most Requested Skills
            </h2>
            <div className="flex-1 w-full min-h-[300px]">
              {(!trending_skills || trending_skills.length === 0) ? (
                 <div className="h-full flex items-center justify-center text-gray-500">No skill data available yet.</div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={trending_skills} layout="vertical" margin={{ top: 0, right: 30, left: 40, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" horizontal={true} vertical={false} />
                    <XAxis type="number" stroke="#6b7280" />
                    <YAxis dataKey="skill" type="category" stroke="#e5e7eb" width={getDynamicWidth(trending_skills, 'skill')} tick={{fill: '#e5e7eb', fontSize: 12}} />
                    <Tooltip cursor={{fill: '#ffffff05'}} contentStyle={{backgroundColor: '#1A1625', borderColor: '#ffffff20', borderRadius: '8px'}} />
                    <Bar dataKey="count" name="Mentions in Jobs" fill="#ec4899" radius={[0, 4, 4, 0]} barSize={24} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          {/* Top Roles Chart */}
          <div className="bg-[#1A1625] p-6 rounded-3xl border border-[#ffffff15] shadow-lg flex flex-col h-[400px]">
            <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
              <Briefcase className="w-6 h-6 text-purple-500" /> Trending Tech Roles
            </h2>
            <div className="flex-1 w-full min-h-[300px]">
              {(!trending_titles || trending_titles.length === 0) ? (
                 <div className="h-full flex items-center justify-center text-gray-500">No role data available yet.</div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={trending_titles} layout="vertical" margin={{ top: 0, right: 30, left: 40, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" horizontal={true} vertical={false} />
                    <XAxis type="number" stroke="#6b7280" />
                    <YAxis dataKey="title" type="category" stroke="#e5e7eb" width={getDynamicWidth(trending_titles, 'title')} tick={{fill: '#e5e7eb', fontSize: 12}} />
                    <Tooltip cursor={{fill: '#ffffff05'}} contentStyle={{backgroundColor: '#1A1625', borderColor: '#ffffff20', borderRadius: '8px'}} />
                    <Bar dataKey="count" name="Active Job Postings" fill="#a855f7" radius={[0, 4, 4, 0]} barSize={24} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          {/* Top Companies Hiring */}
          <div className="bg-[#1A1625] p-6 rounded-3xl border border-[#ffffff15] shadow-lg flex flex-col h-[400px]">
            <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
              <Building className="w-6 h-6 text-blue-500" /> Top Companies Hiring
            </h2>
            <div className="flex-1 w-full min-h-[300px]">
              {(!algoData.top_companies || algoData.top_companies.length === 0) ? (
                 <div className="h-full flex items-center justify-center text-gray-500">No company data available yet.</div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={algoData.top_companies} layout="vertical" margin={{ top: 0, right: 30, left: 40, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" horizontal={true} vertical={false} />
                    <XAxis type="number" stroke="#6b7280" />
                    <YAxis dataKey="company" type="category" stroke="#e5e7eb" width={getDynamicWidth(algoData.top_companies, 'company')} tick={{fill: '#e5e7eb', fontSize: 12}} />
                    <Tooltip cursor={{fill: '#ffffff05'}} contentStyle={{backgroundColor: '#1A1625', borderColor: '#ffffff20', borderRadius: '8px'}} />
                    <Bar dataKey="count" name="Open Roles" fill="#3b82f6" radius={[0, 4, 4, 0]} barSize={24} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          {/* Top Certificates Chart */}
          <div className="bg-[#1A1625] p-6 rounded-3xl border border-[#ffffff15] shadow-lg flex flex-col h-[400px]">
            <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
              <Code className="w-6 h-6 text-green-500" /> Top Certificates
            </h2>
            <div className="flex-1 w-full min-h-[300px]">
              {(!algoData.top_certificates || algoData.top_certificates.length === 0) ? (
                 <div className="h-full flex items-center justify-center text-gray-500">No certificate data available yet.</div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={algoData.top_certificates} layout="vertical" margin={{ top: 0, right: 30, left: 40, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" horizontal={true} vertical={false} />
                    <XAxis type="number" stroke="#6b7280" />
                    <YAxis dataKey="certificate" type="category" stroke="#e5e7eb" width={getDynamicWidth(algoData.top_certificates, 'certificate')} tick={{fill: '#e5e7eb', fontSize: 12}} />
                    <Tooltip cursor={{fill: '#ffffff05'}} contentStyle={{backgroundColor: '#1A1625', borderColor: '#ffffff20', borderRadius: '8px'}} />
                    <Bar dataKey="count" name="Requested in Jobs" fill="#22c55e" radius={[0, 4, 4, 0]} barSize={24} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          {/* Top Skills to Learn */}
          <div className="bg-[#1A1625] p-6 rounded-3xl border border-[#ffffff15] shadow-lg flex flex-col h-[400px]">
            <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
              <TrendingUp className="w-6 h-6 text-orange-500" /> Community Learning Focus
            </h2>
            <div className="flex-1 w-full min-h-[300px]">
              {(!algoData.top_learning_skills || algoData.top_learning_skills.length === 0) ? (
                 <div className="h-full flex items-center justify-center text-gray-500">No learning data available yet.</div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={algoData.top_learning_skills} layout="vertical" margin={{ top: 0, right: 30, left: 40, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" horizontal={true} vertical={false} />
                    <XAxis type="number" stroke="#6b7280" />
                    <YAxis dataKey="skill" type="category" stroke="#e5e7eb" width={getDynamicWidth(algoData.top_learning_skills, 'skill')} tick={{fill: '#e5e7eb', fontSize: 12}} />
                    <Tooltip cursor={{fill: '#ffffff05'}} contentStyle={{backgroundColor: '#1A1625', borderColor: '#ffffff20', borderRadius: '8px'}} />
                    <Bar dataKey="count" name="Learning Mentions" fill="#f97316" radius={[0, 4, 4, 0]} barSize={24} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          {/* 10-Year Technology Forecast */}
          <div className="bg-gradient-to-br from-purple-900/40 to-[#1A1625] p-6 rounded-3xl border border-purple-500/30 shadow-[0_0_30px_rgba(168,85,247,0.15)] flex flex-col h-[400px]">
            <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
              <TrendingUp className="w-6 h-6 text-purple-400" /> 10-Year Technology Forecast
            </h2>
            <div className="flex-1 w-full min-h-[300px]">
              {(!algoData.future_trends || algoData.future_trends.length === 0) ? (
                 <div className="h-full flex items-center justify-center text-gray-500">No future trend data available yet.</div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={algoData.future_trends} margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
                    <XAxis dataKey="year" stroke="#6b7280" tick={{fill: '#9ca3af', fontSize: 12}} />
                    <YAxis stroke="#6b7280" tick={{fill: '#9ca3af', fontSize: 12}} />
                    <Tooltip contentStyle={{backgroundColor: '#1A1625', borderColor: '#ffffff20', borderRadius: '8px'}} itemStyle={{color: '#fff'}} />
                    <Legend wrapperStyle={{paddingTop: '20px'}} />
                    {futureKeys.map((key, index) => (
                      <Line 
                        key={key}
                        type="monotone" 
                        dataKey={key} 
                        stroke={COLORS[index % COLORS.length]} 
                        strokeWidth={3}
                        dot={{ fill: COLORS[index % COLORS.length], r: 4, strokeWidth: 0 }}
                        activeDot={{ r: 6 }}
                      />
                    ))}
                  </LineChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          {/* Community Discussion Topics (Donut Chart) */}
          <div className="bg-[#1A1625] p-6 rounded-3xl border border-[#ffffff15] shadow-lg flex flex-col h-[400px]">
            <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
              <MessageSquare className="w-6 h-6 text-amber-500" /> Hot Community Topics
            </h2>
            <div className="flex-1 w-full min-h-[300px]">
              {(!algoData.trending_topics || algoData.trending_topics.length === 0) ? (
                 <div className="h-full flex items-center justify-center text-gray-500">No community topic data available yet.</div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={algoData.trending_topics}
                      dataKey="heat_score"
                      nameKey="topic"
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      paddingAngle={5}
                      label={({ name, percent }) => percent ? `${name} ${(percent * 100).toFixed(0)}%` : name}
                    >
                      {algoData.trending_topics.map((entry: any, index: number) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{backgroundColor: '#1A1625', borderColor: '#ffffff20', borderRadius: '8px'}} />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

        </div>
      </div>
    </div>
  )
}
