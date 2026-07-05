"use client"

import React, { useMemo } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, CartesianGrid } from 'recharts'
import { TrendingUp, Briefcase, Code, Building, MessageSquare, AlertCircle } from 'lucide-react'

const COLORS = ['#6366f1', '#a855f7', '#ec4899', '#f43f5e', '#f59e0b']

export default function AnalyticsDashboard({ insights, marketFeed }: { insights: any, marketFeed: any[] }) {
  const { total_jobs_analyzed, ai_market_summary, trending_skills, trending_titles, top_companies, generated_at } = insights

  // Parse Algorithmic JSON
  let algoData: any = { market_mood: "Analyzing market mood...", trending_topics: [], source_metrics: null }
  try {
    if (ai_market_summary && ai_market_summary.includes('{')) {
      algoData = JSON.parse(ai_market_summary)
    } else if (ai_market_summary) {
       algoData.market_mood = ai_market_summary
    }
  } catch (e) {
    console.error("Failed to parse Algorithmic JSON", e)
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
                    <YAxis dataKey="skill" type="category" stroke="#e5e7eb" width={80} tick={{fill: '#e5e7eb'}} />
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
                    <YAxis dataKey="title" type="category" stroke="#e5e7eb" width={100} tick={{fill: '#e5e7eb', fontSize: 12}} />
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
                    <YAxis dataKey="company" type="category" stroke="#e5e7eb" width={100} tick={{fill: '#e5e7eb', fontSize: 12}} />
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
                    <YAxis dataKey="certificate" type="category" stroke="#e5e7eb" width={100} tick={{fill: '#e5e7eb', fontSize: 12}} />
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
                    <YAxis dataKey="skill" type="category" stroke="#e5e7eb" width={80} tick={{fill: '#e5e7eb'}} />
                    <Tooltip cursor={{fill: '#ffffff05'}} contentStyle={{backgroundColor: '#1A1625', borderColor: '#ffffff20', borderRadius: '8px'}} />
                    <Bar dataKey="count" name="Learning Mentions" fill="#f97316" radius={[0, 4, 4, 0]} barSize={24} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          {/* 3-Year Future Outlook */}
          <div className="bg-gradient-to-br from-purple-900/40 to-[#1A1625] p-6 rounded-3xl border border-purple-500/30 shadow-[0_0_30px_rgba(168,85,247,0.15)] flex flex-col h-[400px]">
            <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
              <TrendingUp className="w-6 h-6 text-purple-400" /> 3-Year Future Outlook
            </h2>
            <div className="flex-1 w-full min-h-[300px]">
              {(!algoData.future_trends || algoData.future_trends.length === 0) ? (
                 <div className="h-full flex items-center justify-center text-gray-500">No future trend data available yet.</div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={algoData.future_trends} layout="vertical" margin={{ top: 0, right: 30, left: 40, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" horizontal={true} vertical={false} />
                    <XAxis type="number" stroke="#6b7280" />
                    <YAxis dataKey="trend" type="category" stroke="#e5e7eb" width={100} tick={{fill: '#e5e7eb', fontSize: 12}} />
                    <Tooltip cursor={{fill: '#ffffff05'}} contentStyle={{backgroundColor: '#1A1625', borderColor: '#ffffff20', borderRadius: '8px'}} />
                    <Bar dataKey="momentum" name="Prediction Score" fill="#a855f7" radius={[0, 4, 4, 0]} barSize={24} />
                  </BarChart>
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
