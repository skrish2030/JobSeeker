import os

filepath = r"C:\Users\skris\OneDrive\Desktop\JobSeeker\frontend\index.html"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

new_panel = """
            <!-- PANEL: Market Analyst Insights -->
            <div class="tab-panel" id="panel-market-analyst">
                <div class="panel-header" style="display: flex; justify-content: space-between; align-items: center; padding: 20px 24px; border-bottom: 1px solid var(--border-color);">
                    <div>
                        <h2 style="font-size: 24px; color: var(--text-color); margin-bottom: 4px;">Market Analyst Insights <i class="fa-solid fa-chart-line" style="color: var(--primary);"></i></h2>
                        <p style="color: var(--text-secondary); font-size: 14px;">Real-time database trends and AI-driven career predictions.</p>
                    </div>
                    <button id="btn-refresh-market" class="btn btn-primary">
                        <i class="fa-solid fa-rotate-right"></i> Refresh Data
                    </button>
                </div>
                <div class="market-analyst-content" id="market-analyst-content" style="padding: 24px; display: grid; gap: 24px; max-width: 1200px; margin: 0 auto; min-height: 500px;">
                    
                    <div id="market-loading" style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 300px; gap: 16px;">
                        <i class="fa-solid fa-circle-notch fa-spin" style="font-size: 3rem; color: var(--primary);"></i>
                        <h3 style="color: var(--text-color);">Our 30-Year Veteran AI is analyzing the market...</h3>
                        <p style="color: var(--text-secondary);">Crunching local demand stats and fetching top influencer videos.</p>
                    </div>

                    <div id="market-dashboard" style="display: none; grid-template-columns: 1fr; gap: 24px;">
                        
                        <!-- Top Summary Banner -->
                        <div style="background: linear-gradient(135deg, rgba(108,99,255,0.1), rgba(108,99,255,0.05)); border: 1px solid rgba(108,99,255,0.2); padding: 24px; border-radius: 12px; display: flex; gap: 16px; align-items: flex-start;">
                            <i class="fa-solid fa-robot" style="font-size: 2rem; color: var(--primary); margin-top: 4px;"></i>
                            <div>
                                <h3 style="margin: 0 0 8px 0; color: var(--text-color);">Analyst Verdict</h3>
                                <p id="market-summary-text" style="color: var(--text-secondary); line-height: 1.6; margin: 0;"></p>
                            </div>
                        </div>

                        <!-- 3 Column Data Grid -->
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 24px;">
                            
                            <!-- Stat Card: Current Demand -->
                            <div class="glass-card" style="padding: 20px; border-radius: 12px; background: var(--bg-surface); border: 1px solid var(--border-color); box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
                                <h4 style="color: var(--text-color); margin: 0 0 16px 0; display: flex; align-items: center; gap: 8px;"><i class="fa-solid fa-fire" style="color: #ff6b6b;"></i> Top Local Demand (Last 30 Days)</h4>
                                <ul id="market-stats-list" style="list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 12px;"></ul>
                            </div>
                            
                            <!-- Stat Card: Booming Roles -->
                            <div class="glass-card" style="padding: 20px; border-radius: 12px; background: var(--bg-surface); border: 1px solid var(--border-color); box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
                                <h4 style="color: var(--text-color); margin: 0 0 16px 0; display: flex; align-items: center; gap: 8px;"><i class="fa-solid fa-rocket" style="color: #339af0;"></i> 5-Year Booming Roles</h4>
                                <div id="market-roles-list" style="display: flex; flex-wrap: wrap; gap: 8px;"></div>
                            </div>
                            
                            <!-- Stat Card: Best Certificates -->
                            <div class="glass-card" style="padding: 20px; border-radius: 12px; background: var(--bg-surface); border: 1px solid var(--border-color); box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
                                <h4 style="color: var(--text-color); margin: 0 0 16px 0; display: flex; align-items: center; gap: 8px;"><i class="fa-solid fa-certificate" style="color: #fcc419;"></i> High-ROI Certifications</h4>
                                <div id="market-certs-list" style="display: flex; flex-direction: column; gap: 8px;"></div>
                            </div>
                            
                        </div>

                        <!-- YouTube Section -->
                        <div style="margin-top: 12px;">
                            <h3 style="margin: 0 0 16px 0; color: var(--text-color); display: flex; align-items: center; gap: 8px;">
                                <i class="fa-brands fa-youtube" style="color: #ff0000;"></i> Recommended Influencer Insights
                            </h3>
                            <div id="market-youtube-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 20px;">
                                <!-- Videos injected here -->
                            </div>
                        </div>

                    </div>
                </div>
            </div>
"""

# Insert right before </main>
insert_pos = content.rfind("        </main>")
if insert_pos != -1:
    content = content[:insert_pos] + new_panel + content[insert_pos:]
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print("Injected UI panel into index.html")
else:
    print("Could not find </main>")
