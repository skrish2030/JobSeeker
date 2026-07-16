import { createClient } from '@/utils/supabase/server'
import AnalyticsDashboard from './AnalyticsDashboard'

export const revalidate = 60 // Revalidate every minute

export default async function AnalyticsPage() {
  const supabase = await createClient()

  // Fetch the latest analytics insight
  const { data: insights } = await supabase
    .from('analytics_insights')
    .select('*')
    .eq('is_latest', true)
    .single()

  // Fetch Market Intelligence Feed
  const { data: marketFeed } = await supabase
    .from('intelligence_feed')
    .select('*')
    .order('created_at', { ascending: false })
    .limit(10)

  // Fetch daily scrape trends (past 90 days)
  const ninetyDaysAgo = new Date()
  ninetyDaysAgo.setDate(ninetyDaysAgo.getDate() - 90)
  
  const { data: scrapeTrendRaw } = await supabase
    .from('jobs')
    .select('scraped_at')
    .gte('scraped_at', ninetyDaysAgo.toISOString())

  const counts: { [date: string]: number } = {}
  for (let i = 89; i >= 0; i--) {
    const d = new Date()
    d.setDate(d.getDate() - i)
    const dateStr = d.toISOString().split('T')[0]
    counts[dateStr] = 0
  }

  if (scrapeTrendRaw) {
    scrapeTrendRaw.forEach((job: any) => {
      if (job.scraped_at) {
        const dateStr = job.scraped_at.split('T')[0]
        if (counts[dateStr] !== undefined) {
          counts[dateStr]++
        }
      }
    })
  }

  const scrapeTrend = Object.keys(counts).map(date => ({
    date: date, // Keep full YYYY-MM-DD to filter/sort correctly on client
    count: counts[date]
  }))

  const formatNumber = (num: number) => new Intl.NumberFormat('en-US').format(num)

  if (!insights) {
    return (
      <div className="min-h-screen bg-[#0F0C16] flex flex-col items-center justify-center p-6">
        <h1 className="text-3xl font-bold text-gray-100 mb-4">Market Analytics 📊</h1>
        <p className="text-gray-400">No analytics data available yet. Please run the JobSeeker Scraper action.</p>
      </div>
    )
  }

  return <AnalyticsDashboard insights={insights} marketFeed={marketFeed || []} scrapeTrend={scrapeTrend} />
}
