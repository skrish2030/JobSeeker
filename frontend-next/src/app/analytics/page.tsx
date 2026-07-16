import { createClient } from '@/utils/supabase/server'
import AnalyticsDashboard from './AnalyticsDashboard'

export const dynamic = 'force-dynamic'
export const revalidate = 0

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

  // Fetch daily scrape trends (past 90 days) in parallel to bypass 1000-row REST API limit
  const counts: { [date: string]: number } = {}
  const promises = []
  
  for (let i = 89; i >= 0; i--) {
    const d = new Date()
    d.setDate(d.getDate() - i)
    const dateStr = d.toISOString().split('T')[0]
    counts[dateStr] = 0
    
    // Query start and end bounds for the day
    const dayStart = `${dateStr}T00:00:00.000Z`
    const dayEnd = `${dateStr}T23:59:59.999Z`
    
    // We execute exact counts using head: true which fetches 0 rows, keepingPgBouncer requests fast
    const p = supabase
      .from('jobs')
      .select('*', { count: 'exact', head: true })
      .gte('scraped_at', dayStart)
      .lte('scraped_at', dayEnd)
      .then(({ count }) => {
        if (count !== null) {
          counts[dateStr] = count
        }
      })
    promises.push(p)
  }

  // Wait for all counts to resolve
  await Promise.all(promises)

  const scrapeTrend = Object.keys(counts).map(date => ({
    date: date,
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
