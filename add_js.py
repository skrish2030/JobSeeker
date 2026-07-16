import os

filepath = r"C:\Users\skris\OneDrive\Desktop\JobSeeker\frontend\app.js"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

js_code = """
// --- Market Analyst Insights Logic ---
let marketInsightsLoaded = false;

async function fetchMarketInsights() {
    const loadingDiv = document.getElementById('market-loading');
    const dashboardDiv = document.getElementById('market-dashboard');
    
    loadingDiv.style.display = 'flex';
    dashboardDiv.style.display = 'none';
    
    try {
        const response = await fetch('/api/market-insights', {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('jobseeker_session')}` }
        });
        
        if (!response.ok) throw new Error('Failed to fetch market insights');
        
        const data = await response.json();
        
        // Populate Summary
        document.getElementById('market-summary-text').textContent = data.analysis.market_summary || 'Analysis complete.';
        
        // Populate Stats (Local Demand)
        const statsList = document.getElementById('market-stats-list');
        statsList.innerHTML = '';
        if (data.stats && data.stats.length > 0) {
            data.stats.forEach(job => {
                const li = document.createElement('li');
                li.style.display = 'flex';
                li.style.justifyContent = 'space-between';
                li.style.padding = '8px 0';
                li.style.borderBottom = '1px solid var(--border-color)';
                li.innerHTML = `<span style="font-weight: 500; color: var(--text-color);">${job._id}</span> <span style="background: var(--bg-hover); padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: 600; color: var(--primary);">${job.count} listings</span>`;
                statsList.appendChild(li);
            });
        } else {
            statsList.innerHTML = '<li style="color: var(--text-muted);">No local job data available yet.</li>';
        }
        
        // Populate Booming Roles
        const rolesList = document.getElementById('market-roles-list');
        rolesList.innerHTML = '';
        (data.analysis.booming_roles || []).forEach(role => {
            const span = document.createElement('span');
            span.style.background = 'rgba(51, 154, 240, 0.1)';
            span.style.color = '#339af0';
            span.style.border = '1px solid rgba(51, 154, 240, 0.2)';
            span.style.padding = '4px 10px';
            span.style.borderRadius = '16px';
            span.style.fontSize = '13px';
            span.style.fontWeight = '500';
            span.textContent = role;
            rolesList.appendChild(span);
        });
        
        // Populate Best Certificates
        const certsList = document.getElementById('market-certs-list');
        certsList.innerHTML = '';
        (data.analysis.best_certificates || []).forEach(cert => {
            const div = document.createElement('div');
            div.style.display = 'flex';
            div.style.alignItems = 'center';
            div.style.gap = '8px';
            div.style.padding = '8px';
            div.style.background = 'var(--bg-hover)';
            div.style.borderRadius = '6px';
            div.innerHTML = `<i class="fa-solid fa-award" style="color: #fcc419;"></i> <span style="font-size: 14px; font-weight: 500; color: var(--text-color);">${cert}</span>`;
            certsList.appendChild(div);
        });
        
        // Populate YouTube Cards
        const ytGrid = document.getElementById('market-youtube-grid');
        ytGrid.innerHTML = '';
        (data.videos || []).forEach(video => {
            const card = document.createElement('a');
            card.href = video.link;
            card.target = '_blank';
            card.style.display = 'block';
            card.style.textDecoration = 'none';
            card.style.borderRadius = '12px';
            card.style.overflow = 'hidden';
            card.style.border = '1px solid var(--border-color)';
            card.style.background = 'var(--bg-surface)';
            card.style.transition = 'transform 0.2s, box-shadow 0.2s';
            
            // Hover effect managed inline for simplicity or class
            card.onmouseenter = () => { card.style.transform = 'translateY(-4px)'; card.style.boxShadow = '0 10px 15px -3px rgba(0,0,0,0.1)'; };
            card.onmouseleave = () => { card.style.transform = 'translateY(0)'; card.style.boxShadow = 'none'; };
            
            card.innerHTML = `
                <div style="position: relative; width: 100%; padding-top: 56.25%;">
                    <img src="${video.thumbnail}" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: cover;" alt="Video Thumbnail">
                    <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.3); display: flex; align-items: center; justify-content: center;">
                        <i class="fa-solid fa-play" style="color: white; font-size: 3rem; opacity: 0.8; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.5));"></i>
                    </div>
                </div>
                <div style="padding: 16px;">
                    <h4 style="margin: 0 0 8px 0; color: var(--text-color); font-size: 15px; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">${video.title}</h4>
                    <span style="color: var(--text-muted); font-size: 13px; display: flex; align-items: center; gap: 4px;"><i class="fa-solid fa-circle-check" style="font-size: 10px;"></i> ${video.channel || 'YouTube Influencer'}</span>
                </div>
            `;
            ytGrid.appendChild(card);
        });
        
        loadingDiv.style.display = 'none';
        dashboardDiv.style.display = 'grid';
        marketInsightsLoaded = true;
        
    } catch (err) {
        console.error(err);
        loadingDiv.innerHTML = `<i class="fa-solid fa-triangle-exclamation" style="font-size: 3rem; color: #ff6b6b;"></i><h3 style="color: var(--text-color);">Error fetching insights</h3><p style="color: var(--text-secondary);">${err.message}</p><button onclick="fetchMarketInsights()" class="btn btn-primary" style="margin-top: 16px;">Try Again</button>`;
    }
}

// Attach listener to refresh button
const btnRefreshMarket = document.getElementById('btn-refresh-market');
if(btnRefreshMarket) {
    btnRefreshMarket.addEventListener('click', fetchMarketInsights);
}

// Hook into existing navigation
const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
        if (mutation.target.classList.contains('active') && mutation.target.id === 'panel-market-analyst') {
            if (!marketInsightsLoaded) fetchMarketInsights();
        }
    });
});
const marketPanel = document.getElementById('panel-market-analyst');
if(marketPanel) {
    observer.observe(marketPanel, { attributes: true, attributeFilter: ['class'] });
}
"""

with open(filepath, "a", encoding="utf-8") as f:
    f.write("\n" + js_code)
print("Injected JS logic into app.js")
