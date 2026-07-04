// --- Remote Logger to backend ---
(function() {
    function sendLog(level, args) {
        try {
            const message = Array.from(args).map(arg => {
                if (typeof arg === 'object') {
                    try { return JSON.stringify(arg); } catch(e) { return String(arg); }
                }
                return String(arg);
            }).join(' ');
            
            const baseUrl = window.API_BASE_URL ? window.API_BASE_URL.replace(/\/$/, '') : '';
            fetch(baseUrl + '/api/log', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ level, message })
            }).catch(err => {});
        } catch(e) {}
    }

    const orgLog = console.log;
    const orgError = console.error;
    const orgWarn = console.warn;

    console.log = function() {
        orgLog.apply(console, arguments);
        sendLog('info', arguments);
    };
    console.error = function() {
        orgError.apply(console, arguments);
        sendLog('error', arguments);
    };
    console.warn = function() {
        orgWarn.apply(console, arguments);
        sendLog('warn', arguments);
    };

    window.onerror = function(message, source, lineno, colno, error) {
        sendLog('error', [`Uncaught Error: ${message} at ${source}:${lineno}:${colno}`]);
        return false;
    };
})();

// --- App State ---
let state = {
    jobs: [],
    selectedJobId: null,
    settings: {},
    companies: [],
    hasSearched: false,
    activeProfileId: localStorage.getItem('activeProfileId') || 'default',
    profiles: [],
    isManagingProfiles: false,
    activePanel: 'panel-home',
    interestedJobs: [],
    internshipJobs: [],
    filters: {
        search: '',
        location: '',
        statuses: ['identified', 'applied', 'interviewing'],
        remoteTypes: ['remote', 'hybrid', 'onsite'],
        visaTypes: ['h1b', 'none', 'unknown'],
        contractTypes: ['full-time', 'contract', 'w2', 'c2c', 'internship'],
        minScore: 50
    }
};

// --- API Client Helpers ---
async function apiRequest(url, method = 'GET', body = null) {
    try {
        window.lastApiErrorMessage = null;
        const token = localStorage.getItem('sessionToken');
        const headers = { 
            'Content-Type': 'application/json',
            'X-Profile-Id': state.activeProfileId || 'default'
        };
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        // Inject browser-stored AI provider configuration headers
        const aiProvider = localStorage.getItem('ai_model_provider');
        const aiModel = localStorage.getItem('ai_model_name');
        const aiApiKey = localStorage.getItem('ai_api_key');
        if (aiProvider) headers['X-AI-Provider'] = aiProvider;
        if (aiModel) headers['X-AI-Model'] = aiModel;
        if (aiApiKey) headers['X-AI-API-Key'] = aiApiKey;
        
        const options = {
            method,
            headers
        };
        if (body) {
            options.body = JSON.stringify(body);
        }
        let baseUrl = window.API_BASE_URL || "";
        if (baseUrl.endsWith('/')) {
            baseUrl = baseUrl.slice(0, -1);
        }
        const response = await fetch(baseUrl + url, options);
        if (response.status === 401 && !url.includes('/api/auth/')) {
            performLogout();
            throw new Error("Session expired or unauthorized. Please log in.");
        }
        if (!response.ok) {
            let errDetail = 'API request failed';
            try {
                const err = await response.json();
                errDetail = err.detail || errDetail;
            } catch(e) {}
            
            if (typeof errDetail === 'object') {
                window.lastApiErrorData = errDetail;
                throw new Error(errDetail.message || 'API request failed');
            } else {
                window.lastApiErrorData = null;
                throw new Error(errDetail);
            }
        }
        return await response.json();
    } catch (e) {
        window.lastApiErrorMessage = e.message;
        showToast(e.message);
        console.error("API Error:", e);
        return null;
    }
}

// --- Toast Notifications ---
function showToast(message) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.style.display = 'block';
    setTimeout(() => {
        toast.style.display = 'none';
    }, 4000);
}

// --- DOM References ---
const jobListContainer = document.getElementById('job-list-container');
const detailsPanelContainer = document.getElementById('details-panel-container');
const headerSearchInput = document.getElementById('header-search-input');
const headerLocationInput = document.getElementById('header-location-input');
const btnFindJobs = document.getElementById('btn-find-jobs');
const scoreSlider = document.getElementById('score-slider');
const scoreVal = document.getElementById('score-val');
const resultsCount = document.getElementById('feed-results-count');

// Modals & Forms
const settingsModal = document.getElementById('settings-modal');
const btnSettings = document.getElementById('btn-settings');
const settingsClose = document.getElementById('settings-close');
const settingsCancel = document.getElementById('settings-cancel');
const settingsSave = document.getElementById('settings-save');
const tabButtons = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');

// Actions
const btnEmailNow = document.getElementById('btn-email-now');
const btnTestSmtp = document.getElementById('btn-test-smtp');
const btnAddCompany = document.getElementById('btn-add-company');
const companyAddInput = document.getElementById('company-add-input');
const companiesTagsContainer = document.getElementById('companies-tags-container');
const companyUrlInput = document.getElementById('company-url-input');

// --- Initialization ---
document.addEventListener('DOMContentLoaded', async () => {
    console.log("[DEBUG] DOMContentLoaded triggered");
    try {
        setupEventListeners();
        console.log("[DEBUG] setupEventListeners completed");
        await initializeProfiles();
        console.log("[DEBUG] initializeProfiles completed");
        setupInactivityTimer();
        console.log("[DEBUG] setupInactivityTimer completed");
        
        // Load scheduler status viz immediately on startup if logged in
        if (localStorage.getItem('sessionToken')) {
            await loadSchedulerViz();
        }
        
        // Start polling the scraper status logs to show active runs
        setInterval(async () => {
            if (!localStorage.getItem('sessionToken')) return;
            
            // Only poll if the analytics panel is expanded OR settings tab status is active
            const analyticsPanel = document.getElementById('analytics-panel-container');
            const analyticsOpen = analyticsPanel && !analyticsPanel.classList.contains('collapsed');
            const statusTab = document.getElementById('tab-status');
            const statusTabActive = statusTab && statusTab.classList.contains('active') && state.activePanel === 'panel-settings';
            
            if (analyticsOpen || statusTabActive) {
                await loadSchedulerViz();
                if (statusTabActive) {
                    await loadSystemLogs(true);
                }
            }
        }, 15000); // Poll every 15 seconds to prevent spamming
    } catch (e) {
        console.error("[DEBUG] Error during DOMContentLoaded initialization:", e);
    }
});

function performLogout(showPrompt = false) {
    if (showPrompt && !confirm("Are you sure you want to end your secure session?")) {
        return;
    }
    localStorage.removeItem('sessionToken');
    localStorage.removeItem('activeProfileId');
    localStorage.removeItem('username');
    const sidebarUsername = document.getElementById('sidebar-username');
    const settingsUsername = document.getElementById('settings-username');
    if (sidebarUsername) sidebarUsername.textContent = 'Guest Session';
    if (settingsUsername) settingsUsername.textContent = 'Guest Session';
    state.activeProfileId = 'default';
    showAuthOverlay();
    showToast(showPrompt ? "Logged out successfully." : "Session expired due to inactivity. Please log in again.");
}

function setupInactivityTimer() {
    const INACTIVITY_TIMEOUT = 30 * 60 * 1000; // 30 minutes
    let timeoutId;
    
    const resetTimer = () => {
        clearTimeout(timeoutId);
        if (localStorage.getItem('sessionToken')) {
            timeoutId = setTimeout(() => performLogout(false), INACTIVITY_TIMEOUT);
        }
    };
    
    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'];
    events.forEach(name => {
        document.addEventListener(name, resetTimer, true);
    });
    
    resetTimer();
}

async function initializeProfiles() {
    console.log("[DEBUG] initializeProfiles called");
    const token = localStorage.getItem('sessionToken');
    console.log("[DEBUG] sessionToken in localStorage:", token);
    if (!token) {
        console.log("[DEBUG] No sessionToken in localStorage, showing auth overlay");
        showAuthOverlay();
        return;
    }
    
    console.log("[DEBUG] sessionToken exists in localStorage, hiding auth overlay");
    hideAuthOverlay();
    
    // Update sidebar username from localStorage
    const sidebarUsername = document.getElementById('sidebar-username');
    const settingsUsername = document.getElementById('settings-username');
    const storedUsername = localStorage.getItem('username');
    console.log("[DEBUG] storedUsername in localStorage:", storedUsername);
    if (storedUsername) {
        if (sidebarUsername) sidebarUsername.textContent = storedUsername;
        if (settingsUsername) settingsUsername.textContent = storedUsername;
    }
    
    // Auto-select 'default' profile and load the workspace
    state.activeProfileId = 'default';
    localStorage.setItem('activeProfileId', 'default');
    
    // Load config settings and jobs list
    console.log("[DEBUG] Calling loadInitialData()");
    await loadInitialData();
    console.log("[DEBUG] Calling fetchJobs()");
    await fetchJobs();
    console.log("[DEBUG] Calling fetchInterestedJobs()");
    await fetchInterestedJobs();
    console.log("[DEBUG] initializeProfiles completed successfully");
}

function showAuthOverlay() {
    const authOverlay = document.getElementById('auth-overlay');
    if (authOverlay) authOverlay.style.display = 'flex';
    hideProfileOverlay();
}

function hideAuthOverlay() {
    const authOverlay = document.getElementById('auth-overlay');
    if (authOverlay) authOverlay.style.display = 'none';
}

async function loadInitialData() {
    await fetchSettings();
    await fetchCompanies();
    // Keep feed clean on refresh by not loading jobs until searched
    filterAndRenderJobs();
}

// --- Profile Helper Methods ---
let selectedColor = '#7c4dff';

async function fetchProfiles() {
    const res = await apiRequest('/api/profiles');
    if (res) {
        state.profiles = res;
    }
}

function showProfileOverlay() {
    state.isManagingProfiles = false;
    const overlay = document.getElementById('profile-selection-overlay');
    const manageBtn = document.getElementById('btn-manage-profiles');
    if (overlay) {
        overlay.classList.remove('managing');
        overlay.style.display = 'flex';
    }
    if (manageBtn) {
        manageBtn.textContent = 'Manage Profiles';
        manageBtn.classList.remove('btn-primary');
        manageBtn.classList.add('btn-secondary');
    }
    renderProfilesOverlay();
}

function hideProfileOverlay() {
    const overlay = document.getElementById('profile-selection-overlay');
    if (overlay) overlay.style.display = 'none';
}

async function selectProfile(profileId, hideOverlay = true) {
    state.activeProfileId = profileId;
    localStorage.setItem('activeProfileId', profileId);
    
    if (hideOverlay) hideProfileOverlay();
    
    // Update header avatar circle and profile name text
    const activeProfile = state.profiles.find(p => p.id === profileId);
    if (activeProfile) {
        const circle = document.getElementById('active-profile-avatar-circle');
        const nameText = document.getElementById('active-profile-name-text');
        if (circle) {
            circle.style.backgroundColor = activeProfile.avatar_color || '#7c4dff';
            circle.textContent = activeProfile.name.charAt(0).toUpperCase();
        }
        if (nameText) {
            nameText.textContent = activeProfile.name;
        }
    }
    
    showToast(`Switched to profile: ${activeProfile ? activeProfile.name : profileId}`);
    
    // Reset search inputs
    const headerSearchInput = document.getElementById('header-search-input');
    const headerLocationInput = document.getElementById('header-location-input');
    if (headerSearchInput) headerSearchInput.value = '';
    if (headerLocationInput) headerLocationInput.value = '';
    const internSearch = document.getElementById('internship-search-input');
    const internLoc = document.getElementById('internship-location-input');
    if (internSearch) internSearch.value = 'Internship';
    if (internLoc) internLoc.value = '';
    state.hasSearched = false;
    
    // Load this profile's configuration
    await loadInitialData();
    // Also fetch jobs for the selected profile
    await fetchJobs();
    await fetchInterestedJobs();
    
    // Render dropdown menu with other profiles
    renderHeaderProfileDropdown();
}

function renderProfilesOverlay() {
    const container = document.getElementById('profile-grid-container');
    if (!container) return;
    
    container.innerHTML = '';
    
    state.profiles.forEach(p => {
        const initial = p.name.charAt(0).toUpperCase();
        const card = document.createElement('div');
        card.className = 'profile-card';
        card.innerHTML = `
            <div class="profile-avatar-square" style="background-color: ${p.avatar_color || '#7c4dff'}">
                ${initial}
                ${p.id !== 'default' ? `<i class="fa-solid fa-trash profile-delete-btn" data-id="${p.id}"></i>` : ''}
            </div>
            <div class="profile-name">${p.name}</div>
        `;
        
        card.querySelector('.profile-avatar-square').addEventListener('click', (e) => {
            if (state.isManagingProfiles) {
                if (e.target.classList.contains('profile-delete-btn')) {
                    const id = e.target.getAttribute('data-id');
                    handleDeleteProfileClick(id, p.name);
                    return;
                }
                return;
            }
            selectProfile(p.id);
        });
        
        const deleteBtn = card.querySelector('.profile-delete-btn');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                handleDeleteProfileClick(p.id, p.name);
            });
        }
        
        container.appendChild(card);
    });
    
    // Add "Add Profile" card
    const addCard = document.createElement('div');
    addCard.className = 'profile-card add-card';
    addCard.innerHTML = `
        <div class="profile-avatar-square">
            <i class="fa-solid fa-plus"></i>
        </div>
        <div class="profile-name">Add Profile</div>
    `;
    addCard.addEventListener('click', () => {
        if (state.isManagingProfiles) return;
        openCreateProfileModal();
    });
    container.appendChild(addCard);
}

function renderHeaderProfileDropdown() {
    const dropdownMenu = document.getElementById('profile-dropdown-menu');
    if (!dropdownMenu) return;
    
    dropdownMenu.innerHTML = '';
    
    state.profiles.forEach(p => {
        if (p.id === state.activeProfileId) return;
        
        const initial = p.name.charAt(0).toUpperCase();
        const item = document.createElement('div');
        item.className = 'profile-item';
        item.innerHTML = `
            <span class="profile-avatar-circle" style="background-color: ${p.avatar_color || '#7c4dff'}">${initial}</span>
            <span>${p.name}</span>
        `;
        item.addEventListener('click', () => {
            selectProfile(p.id, false);
        });
        dropdownMenu.appendChild(item);
    });
    
    const divider = document.createElement('div');
    divider.className = 'dropdown-divider';
    dropdownMenu.appendChild(divider);
    
    const switchLink = document.createElement('a');
    switchLink.href = '#';
    switchLink.id = 'menu-switch-profile';
    switchLink.innerHTML = `<i class="fa-solid fa-users"></i> Switch Profile`;
    switchLink.addEventListener('click', (e) => {
        e.preventDefault();
        showProfileOverlay();
    });
    dropdownMenu.appendChild(switchLink);
}

function openCreateProfileModal() {
    const modal = document.getElementById('create-profile-modal');
    if (modal) {
        modal.style.display = 'flex';
        const input = document.getElementById('profile-name-input');
        if (input) {
            input.value = '';
            input.focus();
        }
    }
}

async function handleDeleteProfileClick(id, name) {
    if (confirm(`Are you sure you want to delete profile "${name}"? All settings and jobs for this profile will be permanently deleted.`)) {
        const res = await apiRequest(`/api/profiles/${id}`, 'DELETE');
        if (res) {
            showToast(`Profile "${name}" deleted.`);
            if (state.activeProfileId === id) {
                state.activeProfileId = 'default';
                localStorage.setItem('activeProfileId', 'default');
            }
            await fetchProfiles();
            renderProfilesOverlay();
            renderHeaderProfileDropdown();
        }
    }
}

// --- Events Setup ---
function setupEventListeners() {
    setTimeout(() => {
        const mc = document.querySelector('.main-content');
        const tp = document.querySelector('.tab-panel.active');
        const ws = tp ? tp.querySelector('.workspace') : null;
        console.log(`[LAYOUT DEBUG] main-content display: ${mc ? window.getComputedStyle(mc).display : 'null'}, height: ${mc ? mc.offsetHeight : 0}, justify: ${mc ? window.getComputedStyle(mc).justifyContent : 'null'}`);
        console.log(`[LAYOUT DEBUG] tab-panel display: ${tp ? window.getComputedStyle(tp).display : 'null'}, height: ${tp ? tp.offsetHeight : 0}, justify: ${tp ? window.getComputedStyle(tp).justifyContent : 'null'}`);
        console.log(`[LAYOUT DEBUG] workspace display: ${ws ? window.getComputedStyle(ws).display : 'null'}, height: ${ws ? ws.offsetHeight : 0}`);
    }, 2000);
    // Panel Tab Toggling (Left Sidebar)
    const navItems = document.querySelectorAll('.nav-sidebar .nav-item');
    const tabPanels = document.querySelectorAll('.main-content .tab-panel');
    
    navItems.forEach(item => {
        item.addEventListener('click', async () => {
            navItems.forEach(i => i.classList.remove('active'));
            tabPanels.forEach(p => p.classList.remove('active'));
            
            item.classList.add('active');
            const panelId = item.getAttribute('data-panel');
            state.activePanel = panelId;
            document.getElementById(panelId).classList.add('active');
            
            // Clean active job selections when swapping tabs
            state.selectedJobId = null;
            
            if (panelId === 'panel-interested') {
                await fetchInterestedJobs();
            } else if (panelId === 'panel-settings') {
                fillSettingsForm();
            } else if (panelId === 'panel-market-analyst') {
                if (typeof fetchMarketInsights === 'function' && typeof marketInsightsLoaded !== 'undefined' && !marketInsightsLoaded) {
                    fetchMarketInsights();
                }
            } else if (panelId === 'panel-interview') {
                populateInterviewJobSelector();
            } else if (panelId === 'panel-resume') {
                populateResumeJobSelector();
            }
        });
    });

    // Toggle Header Dropdown Filters (Home)
    const btnToggleFiltersDropdown = document.getElementById('btn-toggle-filters-dropdown');
    const filtersDropdownHome = document.getElementById('filters-dropdown-home');
    
    // Toggle Header Dropdown Filters (Internship)
    const btnToggleInternFiltersDropdown = document.getElementById('btn-toggle-internship-filters-dropdown');
    const filtersDropdownInternship = document.getElementById('filters-dropdown-internship');

    // Create/get a filters backdrop overlay
    let filtersBackdrop = document.querySelector('.filters-backdrop');
    if (!filtersBackdrop) {
        filtersBackdrop = document.createElement('div');
        filtersBackdrop.className = 'filters-backdrop';
        document.body.appendChild(filtersBackdrop);
    }

    const toggleBackdrop = () => {
        const anyActive = (filtersDropdownHome && filtersDropdownHome.classList.contains('active')) ||
                          (filtersDropdownInternship && filtersDropdownInternship.classList.contains('active'));
        if (anyActive) {
            filtersBackdrop.classList.add('active');
        } else {
            filtersBackdrop.classList.remove('active');
        }
    };

    if (btnToggleFiltersDropdown && filtersDropdownHome) {
        btnToggleFiltersDropdown.addEventListener('click', (e) => {
            e.stopPropagation();
            filtersDropdownHome.classList.toggle('active');
            if (filtersDropdownInternship) filtersDropdownInternship.classList.remove('active');
            toggleBackdrop();
        });
    }

    if (btnToggleInternFiltersDropdown && filtersDropdownInternship) {
        btnToggleInternFiltersDropdown.addEventListener('click', (e) => {
            e.stopPropagation();
            filtersDropdownInternship.classList.toggle('active');
            if (filtersDropdownHome) filtersDropdownHome.classList.remove('active');
            toggleBackdrop();
        });
    }

    // Toggle Analytics Panel
    const btnToggleAnalytics = document.getElementById('btn-toggle-analytics');
    const analyticsPanelContainer = document.getElementById('analytics-panel-container');
    if (btnToggleAnalytics && analyticsPanelContainer) {
        btnToggleAnalytics.addEventListener('click', () => {
            const isCurrentlyCollapsed = analyticsPanelContainer.classList.contains('collapsed');
            analyticsPanelContainer.classList.toggle('collapsed');
            btnToggleAnalytics.classList.toggle('active');
            
            // If we are opening analytics, load the viz immediately and hide details on mobile
            if (isCurrentlyCollapsed) {
                loadSchedulerViz();
                document.querySelectorAll('.workspace').forEach(ws => {
                    ws.classList.remove('show-details');
                });
                document.querySelectorAll('.job-card.selected').forEach(c => c.classList.remove('selected'));
                state.selectedJobId = null;
            }
        });
    }

    // Dismiss active dropdowns on click outside or escape key, and handle mobile back button
    document.addEventListener('click', (e) => {
        let changed = false;
        if (filtersDropdownHome && filtersDropdownHome.classList.contains('active')) {
            if (!filtersDropdownHome.contains(e.target) && e.target !== btnToggleFiltersDropdown && !btnToggleFiltersDropdown.contains(e.target)) {
                filtersDropdownHome.classList.remove('active');
                changed = true;
            }
        }
        if (filtersDropdownInternship && filtersDropdownInternship.classList.contains('active')) {
            if (!filtersDropdownInternship.contains(e.target) && e.target !== btnToggleInternFiltersDropdown && !btnToggleInternFiltersDropdown.contains(e.target)) {
                filtersDropdownInternship.classList.remove('active');
                changed = true;
            }
        }
        if (changed) {
            toggleBackdrop();
        }
        
        // Handle back button for details pane on mobile
        const backBtn = e.target.closest('.btn-back-to-feed');
        if (backBtn) {
            const workspace = backBtn.closest('.workspace');
            if (workspace) {
                workspace.classList.remove('show-details');
            }
            document.querySelectorAll('.job-card.selected').forEach(c => c.classList.remove('selected'));
            state.selectedJobId = null;
        }

        // Handle close button for analytics pane on mobile
        const closeAnalyticsBtn = e.target.closest('.btn-close-analytics');
        if (closeAnalyticsBtn) {
            if (analyticsPanelContainer) {
                analyticsPanelContainer.classList.add('collapsed');
            }
            if (btnToggleAnalytics) {
                btnToggleAnalytics.classList.remove('active');
            }
        }

        // Handle Apply & Close filters button click
        const closeFiltersBtn = e.target.closest('.btn-close-filters');
        if (closeFiltersBtn) {
            if (filtersDropdownHome) filtersDropdownHome.classList.remove('active');
            if (filtersDropdownInternship) filtersDropdownInternship.classList.remove('active');
            toggleBackdrop();
        }
    });

    if (filtersBackdrop) {
        filtersBackdrop.addEventListener('click', () => {
            if (filtersDropdownHome) filtersDropdownHome.classList.remove('active');
            if (filtersDropdownInternship) filtersDropdownInternship.classList.remove('active');
            filtersBackdrop.classList.remove('active');
        });
    }

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            let changed = false;
            if (filtersDropdownHome && filtersDropdownHome.classList.contains('active')) {
                filtersDropdownHome.classList.remove('active');
                changed = true;
            }
            if (filtersDropdownInternship && filtersDropdownInternship.classList.contains('active')) {
                filtersDropdownInternship.classList.remove('active');
                changed = true;
            }
            if (changed) {
                toggleBackdrop();
            }
        }
    });

    // Home Scraper Search
    const triggerHomeSearch = async () => {
        const keyword = headerSearchInput.value.trim();
        const location = headerLocationInput.value.trim();
        
        if (!keyword && !location) {
            showToast("Please enter a job title or location to search.");
            return;
        }
        
        btnFindJobs.disabled = true;
        btnFindJobs.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Searching...';
        
        const displayLocation = location || (state.settings.locations ? state.settings.locations : 'default');
        showToast(`Searching for '${keyword}' in '${displayLocation}'...`);
        
        const res = await apiRequest('/api/scrape/find', 'POST', {
            search_term: keyword,
            location: location
        });
        
        if (res && Array.isArray(res)) {
            // Update internshipJobs from the search results
            state.internshipJobs = res.filter(j => {
                const title = (j.title || '').toLowerCase();
                const contract = (j.contract_type || '').toLowerCase();
                return title.includes('intern') || title.includes('co-op') || title.includes('coop') || title.includes('fellow') || contract === 'internship';
            });
            
            // Exclude internships from general jobs feed (Home)
            state.jobs = res.filter(j => {
                const title = (j.title || '').toLowerCase();
                const contract = (j.contract_type || '').toLowerCase();
                const isIntern = title.includes('intern') || title.includes('co-op') || title.includes('coop') || title.includes('fellow') || contract === 'internship';
                return !isIntern;
            });
            state.hasSearched = true;
            
            if (res.length > 0) {
                state.filters.statuses = ['identified', 'applied', 'interviewing'];
                state.filters.remoteTypes = ['remote', 'hybrid', 'onsite'];
                state.filters.visaTypes = ['h1b', 'none', 'unknown'];
                state.filters.contractTypes = ['full-time', 'contract', 'w2', 'c2c', 'internship'];
                state.filters.minScore = 0;
                state.filters.search = '';
                state.filters.location = '';
                if (scoreSlider) { scoreSlider.value = 0; scoreVal.textContent = '0'; }
                document.querySelectorAll('#panel-home input[name="status-filter"]').forEach(c => c.checked = true);
                document.querySelectorAll('#panel-home input[name="remote-filter"]').forEach(c => c.checked = true);
                document.querySelectorAll('#panel-home input[name="visa-filter"]').forEach(c => c.checked = true);
                document.querySelectorAll('#panel-home input[name="contract-filter"]').forEach(c => c.checked = true);
            }
            
            filterAndRenderJobs();
            showToast(res.length > 0 ? `Found ${res.length} matches!` : "Zero matches found. Try a broader term.");
        } else {
            state.jobs = [];
            state.hasSearched = true;
            filterAndRenderJobs();
            showToast("Search failed or returned invalid format.");
        }
        
        btnFindJobs.disabled = false;
        btnFindJobs.innerHTML = 'Search';
    };

    btnFindJobs.addEventListener('click', triggerHomeSearch);
    headerSearchInput.addEventListener('keyup', (e) => { if (e.key === 'Enter') triggerHomeSearch(); });
    headerLocationInput.addEventListener('keyup', (e) => { if (e.key === 'Enter') triggerHomeSearch(); });

    // Internship Scraper Search
    const btnInternshipFindJobs = document.getElementById('btn-internship-find-jobs');
    const internshipSearchInput = document.getElementById('internship-search-input');
    const internshipLocationInput = document.getElementById('internship-location-input');

    const triggerInternshipSearch = async () => {
        const keyword = internshipSearchInput.value.trim();
        const location = internshipLocationInput.value.trim();
        
        if (!keyword) {
            showToast("Please enter keywords to search.");
            return;
        }
        
        btnInternshipFindJobs.disabled = true;
        btnInternshipFindJobs.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Searching...';
        
        showToast(`Searching internships for '${keyword}'...`);
        const res = await apiRequest('/api/scrape/find', 'POST', {
            search_term: keyword,
            location: location
        });
        
        if (res && Array.isArray(res)) {
            state.internshipJobs = res.filter(j => {
                const title = (j.title || '').toLowerCase();
                const contract = (j.contract_type || '').toLowerCase();
                return title.includes('intern') || title.includes('co-op') || title.includes('coop') || title.includes('fellow') || contract === 'internship';
            });
            state.hasSearched = true;
            renderInternshipJobs();
            showToast(`Found ${state.internshipJobs.length} internships`);
        } else {
            state.internshipJobs = [];
            state.hasSearched = true;
            renderInternshipJobs();
            showToast("No internships found.");
        }
        
        btnInternshipFindJobs.disabled = false;
        btnInternshipFindJobs.innerHTML = 'Search';
    };

    if (btnInternshipFindJobs) {
        btnInternshipFindJobs.addEventListener('click', triggerInternshipSearch);
    }
    if (internshipSearchInput) {
        internshipSearchInput.addEventListener('keyup', (e) => { if (e.key === 'Enter') triggerInternshipSearch(); });
        internshipSearchInput.addEventListener('input', () => {
            renderInternshipJobs();
        });
    }
    if (internshipLocationInput) {
        internshipLocationInput.addEventListener('keyup', (e) => { if (e.key === 'Enter') triggerInternshipSearch(); });
    }

    // Home Filters Binding
    if (scoreSlider) {
        scoreSlider.addEventListener('input', (e) => {
            const val = e.target.value;
            scoreVal.textContent = val;
            state.filters.minScore = parseInt(val);
            filterAndRenderJobs();
        });
    }

    document.querySelectorAll('#panel-home input[name="status-filter"]').forEach(chk => {
        chk.addEventListener('change', () => {
            state.filters.statuses = Array.from(document.querySelectorAll('#panel-home input[name="status-filter"]:checked')).map(c => c.value);
            filterAndRenderJobs();
        });
    });

    document.querySelectorAll('#panel-home input[name="remote-filter"]').forEach(chk => {
        chk.addEventListener('change', () => {
            state.filters.remoteTypes = Array.from(document.querySelectorAll('#panel-home input[name="remote-filter"]:checked')).map(c => c.value);
            filterAndRenderJobs();
        });
    });

    document.querySelectorAll('#panel-home input[name="visa-filter"]').forEach(chk => {
        chk.addEventListener('change', () => {
            state.filters.visaTypes = Array.from(document.querySelectorAll('#panel-home input[name="visa-filter"]:checked')).map(c => c.value);
            filterAndRenderJobs();
        });
    });

    document.querySelectorAll('#panel-home input[name="contract-filter"]').forEach(chk => {
        chk.addEventListener('change', () => {
            state.filters.contractTypes = Array.from(document.querySelectorAll('#panel-home input[name="contract-filter"]:checked')).map(c => c.value);
            filterAndRenderJobs();
        });
    });

    // Internship Filters Binding
    const internScoreSlider = document.getElementById('intern-score-slider');
    const internScoreVal = document.getElementById('intern-score-val');
    if (internScoreSlider && internScoreVal) {
        internScoreSlider.addEventListener('input', (e) => {
            const val = e.target.value;
            internScoreVal.textContent = val;
            renderInternshipJobs();
        });
    }

    document.querySelectorAll('#panel-internship input[name="intern-remote-filter"]').forEach(chk => {
        chk.addEventListener('change', () => {
            renderInternshipJobs();
        });
    });

    // Action buttons
    if (btnEmailNow) {
        btnEmailNow.addEventListener('click', async () => {
            btnEmailNow.disabled = true;
            btnEmailNow.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> <span>Emailing...</span>';
            showToast("Checking pipeline and sending match digests...");
            const res = await apiRequest('/api/email/now', 'POST');
            if (res) {
                showToast(res.message);
                await fetchJobs(); 
            }
            btnEmailNow.disabled = false;
            btnEmailNow.innerHTML = '<i class="fa-solid fa-paper-plane"></i> <span>Send Digest</span>';
        });
    }

    // Settings Embedded Tab switching
    const settingsNavBtns = document.querySelectorAll('.settings-nav-btn');
    settingsNavBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            settingsNavBtns.forEach(b => b.classList.remove('active'));
            document.querySelectorAll('#panel-settings .tab-content').forEach(c => c.classList.remove('active'));
            
            btn.classList.add('active');
            const target = btn.getAttribute('data-tab');
            document.getElementById(target).classList.add('active');
            
            if (target === 'tab-status') {
                loadSystemLogs();
            }
        });
    });

    // Save Settings
    const handleSaveSettings = async () => {
        await saveSettings();
    };
    const handleResetSettings = () => {
        fillSettingsForm();
        showToast("Configurations reset to last saved.");
    };

    const settingsSaveBtn = document.getElementById('settings-save');
    if (settingsSaveBtn) {
        settingsSaveBtn.addEventListener('click', handleSaveSettings);
    }
    const settingsSaveMobileBtn = document.getElementById('settings-save-mobile');
    if (settingsSaveMobileBtn) {
        settingsSaveMobileBtn.addEventListener('click', handleSaveSettings);
    }

    const settingsCancelBtn = document.getElementById('settings-cancel');
    if (settingsCancelBtn) {
        settingsCancelBtn.addEventListener('click', handleResetSettings);
    }
    const settingsCancelMobileBtn = document.getElementById('settings-cancel-mobile');
    if (settingsCancelMobileBtn) {
        settingsCancelMobileBtn.addEventListener('click', handleResetSettings);
    }

    const btnAddAiConfig = document.getElementById('btn-add-ai-config');
    if (btnAddAiConfig) {
        btnAddAiConfig.addEventListener('click', () => {
            addAiConfigRow('gemini', '', '');
        });
    }

    // Add company
    if (btnAddCompany) {
        btnAddCompany.addEventListener('click', async () => {
            const name = companyAddInput.value.trim();
            const url = companyUrlInput.value.trim();
            if (name) {
                const res = await apiRequest('/api/target-companies', 'POST', { name, portal_url: url || null });
                if (res) {
                    state.companies = res.companies;
                    renderCompanyTags();
                    companyAddInput.value = '';
                    companyUrlInput.value = '';
                    showToast(`Company '${name}' added to focus targets.`);
                    await fetchJobs(); 
                }
            }
        });
    }

    // Test SMTP
    if (btnTestSmtp) {
        btnTestSmtp.addEventListener('click', async () => {
            const email = document.getElementById('test-email-target').value.trim();
            if (!email) {
                showToast("Enter recipient address for test");
                return;
            }
            btnTestSmtp.disabled = true;
            btnTestSmtp.textContent = "Sending...";
            const res = await apiRequest('/api/email/test', 'POST', { email });
            if (res) {
                showToast(res.message);
            }
            btnTestSmtp.disabled = false;
            btnTestSmtp.textContent = "Send Test Email";
        });
    }

    // Auth tabs toggling
    const tabLoginBtn = document.getElementById('tab-login-btn');
    const tabRegisterBtn = document.getElementById('tab-register-btn');
    const loginFormPanel = document.getElementById('login-form-panel');
    const registerFormPanel = document.getElementById('register-form-panel');
    const mfaFormPanel = document.getElementById('mfa-form-panel');

    // Helper for resetting captcha states
    const resetCaptchas = () => {
        const loginCaptchaTrack = document.getElementById('login-captcha-track');
        const registerCaptchaTrack = document.getElementById('register-captcha-track');
        if (loginCaptchaTrack && loginCaptchaTrack.reset) loginCaptchaTrack.reset();
        if (registerCaptchaTrack && registerCaptchaTrack.reset) registerCaptchaTrack.reset();
        
        const btnLoginProceed = document.getElementById('btn-login-proceed');
        const btnRegisterProceed = document.getElementById('btn-register-proceed');
        const loginCaptchaContainer = document.getElementById('login-captcha-container');
        const registerCaptchaContainer = document.getElementById('register-captcha-container');
        
        if (btnLoginProceed) btnLoginProceed.style.display = 'block';
        if (btnRegisterProceed) btnRegisterProceed.style.display = 'block';
        if (loginCaptchaContainer) loginCaptchaContainer.style.display = 'none';
        if (registerCaptchaContainer) registerCaptchaContainer.style.display = 'none';
    };

    if (tabLoginBtn && tabRegisterBtn && loginFormPanel && registerFormPanel) {
        tabLoginBtn.addEventListener('click', () => {
            tabLoginBtn.classList.add('active');
            tabRegisterBtn.classList.remove('active');
            loginFormPanel.classList.add('active');
            registerFormPanel.classList.remove('active');
            mfaFormPanel.classList.remove('active');
            
            // Clear inputs
            const regUser = document.getElementById('auth-reg-username');
            const regEmail = document.getElementById('auth-reg-email');
            const regPass = document.getElementById('auth-reg-password');
            if (regUser) regUser.value = '';
            if (regEmail) regEmail.value = '';
            if (regPass) regPass.value = '';
            
            resetCaptchas();
        });
        tabRegisterBtn.addEventListener('click', () => {
            tabRegisterBtn.classList.add('active');
            tabLoginBtn.classList.remove('active');
            registerFormPanel.classList.add('active');
            loginFormPanel.classList.remove('active');
            mfaFormPanel.classList.remove('active');
            
            // Clear inputs
            const logUser = document.getElementById('auth-login-username');
            const logPass = document.getElementById('auth-login-password');
            if (logUser) logUser.value = '';
            if (logPass) logPass.value = '';
            
            resetCaptchas();
        });
    }

    // Initialize custom slider captchas
    initSliderCaptcha(
        'login-captcha-track', 
        'login-captcha-handle', 
        'login-captcha-label', 
        'btn-submit-login',
        () => {
            const btnLoginProceed = document.getElementById('btn-login-proceed');
            const btnSubmitLogin = document.getElementById('btn-submit-login');
            if (btnLoginProceed) btnLoginProceed.style.display = 'none';
            if (btnSubmitLogin) {
                btnSubmitLogin.style.display = 'block';
                btnSubmitLogin.disabled = false;
            }
        }
    );

    initSliderCaptcha(
        'register-captcha-track', 
        'register-captcha-handle', 
        'register-captcha-label', 
        'btn-submit-register',
        () => {
            const btnRegisterProceed = document.getElementById('btn-register-proceed');
            const btnSubmitRegister = document.getElementById('btn-submit-register');
            if (btnRegisterProceed) btnRegisterProceed.style.display = 'none';
            if (btnSubmitRegister) {
                btnSubmitRegister.style.display = 'block';
                btnSubmitRegister.disabled = false;
            }
        }
    );

    // Initial Proceed button triggers for showing captchas
    const btnLoginProceed = document.getElementById('btn-login-proceed');
    if (btnLoginProceed) {
        btnLoginProceed.addEventListener('click', () => {
            const username = document.getElementById('auth-login-username').value.trim();
            const password = document.getElementById('auth-login-password').value;
            if (!username || !password) {
                showToast("Please enter both username and password.");
                return;
            }
            // Show Captcha
            btnLoginProceed.style.display = 'none';
            const captchaContainer = document.getElementById('login-captcha-container');
            if (captchaContainer) captchaContainer.style.display = 'block';
        });
    }

    const btnRegisterProceed = document.getElementById('btn-register-proceed');
    if (btnRegisterProceed) {
        btnRegisterProceed.addEventListener('click', () => {
            const username = document.getElementById('auth-reg-username').value.trim();
            const email = document.getElementById('auth-reg-email').value.trim();
            const password = document.getElementById('auth-reg-password').value;
            if (!username || !email || !password) {
                showToast("Please fill out all registration fields.");
                return;
            }
            // Show Captcha
            btnRegisterProceed.style.display = 'none';
            const captchaContainer = document.getElementById('register-captcha-container');
            if (captchaContainer) captchaContainer.style.display = 'block';
        });
    }

    // Setup OTP grid auto-tabbing and paste listeners
    setupOtpInputTabbing();

    // Handle Authentication Form Submissions
    const btnSubmitLogin = document.getElementById('btn-submit-login');
    if (btnSubmitLogin) {
        btnSubmitLogin.addEventListener('click', async () => {
            const username = document.getElementById('auth-login-username').value.trim();
            const password = document.getElementById('auth-login-password').value;
            if (!username || !password) {
                showToast("Please enter both username and password.");
                return;
            }
            btnSubmitLogin.disabled = true;
            btnSubmitLogin.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Authenticating...';
            
            try {
                const res = await apiRequest('/api/auth/login', 'POST', { username, password });
                if (res && res.status === 'success') {
                    // Direct login success
                    localStorage.setItem('sessionToken', res.token);
                    localStorage.setItem('activeProfileId', 'default'); // default for now
                    localStorage.setItem('username', res.username || username);
                    window.location.reload();
                } else {
                    // Authentication failed (wrong password or username)
                    resetCaptchas();
                }
            } catch (err) {
                resetCaptchas();
            } finally {
                btnSubmitLogin.disabled = false;
                btnSubmitLogin.innerHTML = 'Confirm Sign In';
            }
        });
    }

    const btnSubmitRegister = document.getElementById('btn-submit-register');
    if (btnSubmitRegister) {
        btnSubmitRegister.addEventListener('click', async () => {
            const username = document.getElementById('auth-reg-username').value.trim();
            const email = document.getElementById('auth-reg-email').value.trim();
            const password = document.getElementById('auth-reg-password').value;
            
            if (!username || !email || !password) {
                showToast("Please fill out all registration fields.");
                return;
            }
            btnSubmitRegister.disabled = true;
            btnSubmitRegister.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Registering...';
            
            try {
                // Clear any previous suggestions
                const sugDiv = document.getElementById('username-suggestions');
                if (sugDiv) {
                    sugDiv.style.display = 'none';
                    sugDiv.innerHTML = '';
                }

                const res = await apiRequest('/api/auth/register', 'POST', { username, email, password });
                
                const showSuggestionsIfAny = () => {
                    if (window.lastApiErrorData && window.lastApiErrorData.suggestions) {
                        const sDiv = document.getElementById('username-suggestions');
                        if (sDiv) {
                            sDiv.style.display = 'block';
                            sDiv.innerHTML = '<span class="suggestions-label">Suggestions:</span>';
                            window.lastApiErrorData.suggestions.forEach(name => {
                                const badge = document.createElement('span');
                                badge.className = 'suggestion-badge';
                                badge.textContent = name;
                                badge.addEventListener('click', () => {
                                    document.getElementById('auth-reg-username').value = name;
                                    sDiv.style.display = 'none';
                                    sDiv.innerHTML = '';
                                });
                                sDiv.appendChild(badge);
                            });
                        }
                    }
                };

                if (res && res.status === 'success') {
                    // Direct registration success
                    localStorage.setItem('sessionToken', res.token);
                    localStorage.setItem('activeProfileId', 'default');
                    localStorage.setItem('username', res.username || username);
                    window.location.reload();
                } else {
                    // Registration failed
                    resetCaptchas();
                    showSuggestionsIfAny();
                }
            } catch (err) {
                resetCaptchas();
                if (window.lastApiErrorData && window.lastApiErrorData.suggestions) {
                    const sDiv = document.getElementById('username-suggestions');
                    if (sDiv) {
                        sDiv.style.display = 'block';
                        sDiv.innerHTML = '<span class="suggestions-label">Suggestions:</span>';
                        window.lastApiErrorData.suggestions.forEach(name => {
                            const badge = document.createElement('span');
                            badge.className = 'suggestion-badge';
                            badge.textContent = name;
                            badge.addEventListener('click', () => {
                                document.getElementById('auth-reg-username').value = name;
                                sDiv.style.display = 'none';
                                sDiv.innerHTML = '';
                            });
                            sDiv.appendChild(badge);
                        });
                    }
                }
            } finally {
                btnSubmitRegister.disabled = false;
                btnSubmitRegister.innerHTML = 'Confirm Registration';
            }
        });
    }

    const btnSubmitMfa = document.getElementById('btn-submit-mfa');
    if (btnSubmitMfa) {
        btnSubmitMfa.addEventListener('click', async () => {
            const code = Array.from(document.querySelectorAll('.otp-digit-input')).map(i => i.value.trim()).join('');
            if (!code || code.length !== 6) {
                showToast("Please enter the 6-digit verification code.");
                return;
            }
            btnSubmitMfa.disabled = true;
            btnSubmitMfa.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Verifying...';
            
            try {
                if (window.isRegistering) {
                    const res = await apiRequest('/api/auth/register/verify', 'POST', { registration_id: window.registrationId, code });
                    if (res && res.status === 'success') {
                        stopMfaCountdown();
                        
                        // Restore headers
                        const mainBrand = document.getElementById('auth-brand-main');
                        const tabsContainer = document.getElementById('auth-tabs-container');
                        if (mainBrand) mainBrand.style.display = 'flex';
                        if (tabsContainer) tabsContainer.style.display = 'flex';

                        // Pre-fill login username with registered one
                        const regUser = document.getElementById('auth-reg-username');
                        if (regUser) {
                            const logUser = document.getElementById('auth-login-username');
                            if (logUser) logUser.value = regUser.value;
                        }

                        // Clear registration fields
                        const regEmail = document.getElementById('auth-reg-email');
                        const regPass = document.getElementById('auth-reg-password');
                        if (regUser) regUser.value = '';
                        if (regEmail) regEmail.value = '';
                        if (regPass) regPass.value = '';

                        // Switch to Login Tab
                        tabLoginBtn.classList.add('active');
                        tabRegisterBtn.classList.remove('active');
                        loginFormPanel.classList.add('active');
                        registerFormPanel.classList.remove('active');
                        mfaFormPanel.classList.remove('active');
                        resetCaptchas();
                        
                        showToast("Registration verified successfully! Please sign in with your credentials.");
                    }
                } else {
                    const res = await apiRequest('/api/auth/mfa', 'POST', { username: window.authUsername, code });
                    if (res && res.status === 'success' && res.token) {
                        stopMfaCountdown();
                        
                        // Restore headers for future logins
                        const mainBrand = document.getElementById('auth-brand-main');
                        const tabsContainer = document.getElementById('auth-tabs-container');
                        if (mainBrand) mainBrand.style.display = 'flex';
                        if (tabsContainer) tabsContainer.style.display = 'flex';

                        localStorage.setItem('sessionToken', res.token);
                        localStorage.setItem('username', res.username || window.authUsername || '');
                        const sidebarUsername = document.getElementById('sidebar-username');
                        const settingsUsername = document.getElementById('settings-username');
                        const uName = res.username || window.authUsername || '';
                        if (sidebarUsername) sidebarUsername.textContent = uName;
                        if (settingsUsername) settingsUsername.textContent = uName;
                        hideAuthOverlay();
                        showToast("Verification successful! Loading workspace...");
                        await initializeProfiles();
                    }
                }
            } catch (e) {
                showToast(e.message || "Invalid or expired MFA code.");
            } finally {
                btnSubmitMfa.disabled = false;
                btnSubmitMfa.innerHTML = 'Verify Securely';
            }
        });
    }

    const btnBackToLogin = document.getElementById('btn-back-to-login');
    if (btnBackToLogin) {
        btnBackToLogin.addEventListener('click', () => {
            stopMfaCountdown();
            
            // Show main brand header and tabs
            const mainBrand = document.getElementById('auth-brand-main');
            const tabsContainer = document.getElementById('auth-tabs-container');
            if (mainBrand) mainBrand.style.display = 'flex';
            if (tabsContainer) tabsContainer.style.display = 'flex';

            mfaFormPanel.classList.remove('active');
            loginFormPanel.classList.add('active');
            resetCaptchas();
        });
    }

    // End secure session (logout)
    document.querySelectorAll('#btn-logout, #btn-logout-settings, .btn-logout').forEach(btn => {
        btn.addEventListener('click', () => {
            performLogout(true);
        });
    });

    // AI Feature Actions Setup
    const btnStartInterview = document.getElementById('btn-start-interview');
    if (btnStartInterview) {
        btnStartInterview.addEventListener('click', () => {
            startInterviewSession();
        });
    }

    const btnSubmitChatMessage = document.getElementById('btn-submit-chat-message');
    const chatMessageInput = document.getElementById('chat-message-input');
    if (btnSubmitChatMessage && chatMessageInput) {
        btnSubmitChatMessage.addEventListener('click', () => {
            sendChatMessage();
        });
        chatMessageInput.addEventListener('keyup', (e) => {
            if (e.key === 'Enter') sendChatMessage();
        });
    }

    const btnBuildResume = document.getElementById('btn-build-resume');
    if (btnBuildResume) {
        btnBuildResume.addEventListener('click', () => {
            generateTailoredResume();
        });
    }

    const btnCopyTailoredResume = document.getElementById('btn-copy-tailored-resume');
    if (btnCopyTailoredResume) {
        btnCopyTailoredResume.addEventListener('click', () => {
            const output = document.getElementById('resume-output-content');
            if (output && output.style.display !== 'none') {
                const content = output.textContent;
                navigator.clipboard.writeText(content);
                showToast("Resume copied to clipboard!");
            }
        });
    }

    const btnDownloadTailoredResume = document.getElementById('btn-download-tailored-resume');
    if (btnDownloadTailoredResume) {
        btnDownloadTailoredResume.addEventListener('click', () => {
            const output = document.getElementById('resume-output-content');
            if (output && output.style.display !== 'none') {
                const content = output.textContent;
                const blob = new Blob([content], { type: 'text/plain' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'Tailored_Resume.txt';
                a.click();
                URL.revokeObjectURL(url);
            }
        });
    }

    // Speech Recognition Event Listeners
    const btnMicInterview = document.getElementById('btn-mic-interview');
    if (btnMicInterview) {
        btnMicInterview.addEventListener('click', () => {
            if (!speechRecognition) {
                showToast("Speech Recognition is not supported in your browser.");
                return;
            }
            if (isListening) {
                speechRecognition.stop();
            } else {
                speechTranscript = '';
                speechRecognition.start();
            }
        });
    }
}
// --- Data Fetching ---
async function fetchJobs() {
    const res = await apiRequest('/api/jobs');
    if (res) {
        // Auto-initialize internshipJobs from the loaded jobs list
        state.internshipJobs = res.filter(j => {
            const title = (j.title || '').toLowerCase();
            const contract = (j.contract_type || '').toLowerCase();
            return title.includes('intern') || title.includes('co-op') || title.includes('coop') || title.includes('fellow') || contract === 'internship';
        });
        
        // Exclude internships from general jobs feed (Home)
        state.jobs = res.filter(j => {
            const title = (j.title || '').toLowerCase();
            const contract = (j.contract_type || '').toLowerCase();
            const isIntern = title.includes('intern') || title.includes('co-op') || title.includes('coop') || title.includes('fellow') || contract === 'internship';
            return !isIntern;
        });
        
        filterAndRenderJobs();
        if (state.activePanel === 'panel-internship') {
            renderInternshipJobs();
        }
    }
}

async function fetchSettings() {
    const res = await apiRequest('/api/settings');
    if (res) {
        state.settings = res;
        updateInterviewAssistantSubtitle();
        // Pre-fill min score slider based on saved config
        if (res.min_relevance_score) {
            const ms = parseInt(res.min_relevance_score);
            state.filters.minScore = ms;
            scoreSlider.value = ms;
            scoreVal.textContent = ms;
        }
    }
}

async function fetchCompanies() {
    const res = await apiRequest('/api/target-companies');
    if (res) {
        state.companies = res;
    }
}

// --- Filtering & Rendering ---
function filterAndRenderJobs() {
    if (state.activePanel === 'panel-interested') {
        renderJobList(state.interestedJobs);
        return;
    }
    if (state.activePanel === 'panel-internship') {
        renderInternshipJobs();
        return;
    }

    const f = state.filters;
    const filtered = state.jobs.filter(job => {
        if (f.search) {
            const searchWords = f.search.toLowerCase().split(/\s+/).filter(w => w.length > 0);
            const titleLower = (job.title || '').toLowerCase();
            const companyLower = (job.company || '').toLowerCase();
            const descLower = (job.description || '').toLowerCase();
            const contractLower = (job.contract_type || '').toLowerCase();
            
            let matchesAll = true;
            for (const w of searchWords) {
                let wordMatches = false;
                if (w === 'internship') {
                    wordMatches = titleLower.includes('intern') || 
                                  titleLower.includes('co-op') || 
                                  titleLower.includes('coop') || 
                                  titleLower.includes('fellow') ||
                                  companyLower.includes('intern') ||
                                  descLower.includes('intern') ||
                                  contractLower === 'internship';
                } else {
                    wordMatches = titleLower.includes(w) || 
                                  companyLower.includes(w) || 
                                  descLower.includes(w);
                }
                if (!wordMatches) {
                    matchesAll = false;
                    break;
                }
            }
            if (!matchesAll) return false;
        }
        if (f.location) {
            const l = f.location.toLowerCase();
            const locMatch = (job.location || '').toLowerCase().includes(l);
            if (!locMatch) return false;
        }
        const jobStatus = job.status || 'identified';
        if (!f.statuses.includes(jobStatus)) return false;
        
        const jobRemote = job.remote_type || 'remote';
        if (!f.remoteTypes.includes(jobRemote)) return false;
        
        const jobVisa = job.visa_type || 'unknown';
        if (!f.visaTypes.includes(jobVisa)) return false;
        
        const jobContract = job.contract_type || 'full-time';
        if (!f.contractTypes.includes(jobContract)) return false;
        
        if ((job.score || 0) < f.minScore) return false;
        return true;
    });

    resultsCount.textContent = `${filtered.length} jobs matching`;
    renderJobList(filtered);
    renderAnalytics(filtered);
}
function renderAnalytics(filteredJobs) {
    const container = document.getElementById('analytics-panel-container');
    if (!container) return;
    
    const total = filteredJobs.length;
    
    // Calculate Average Score
    const avgScore = total > 0 ? Math.round(filteredJobs.reduce((sum, j) => sum + (j.score || 0), 0) / total) : 0;
    
    // Calculate target companies ratio
    const targetCompaniesNames = state.companies.map(c => (c.name || '').toLowerCase().trim());
    const targetCount = filteredJobs.filter(j => targetCompaniesNames.includes((j.company || '').toLowerCase().trim())).length;
    const targetPct = total > 0 ? Math.round((targetCount / total) * 100) : 0;
    
    // Funnel Counts
    const statusCounts = { identified: 0, applied: 0, interviewing: 0, offer: 0, archived: 0 };
    filteredJobs.forEach(j => {
        if (statusCounts[j.status] !== undefined) {
            statusCounts[j.status]++;
        }
    });
    
    // Workplace type counts
    const remoteCounts = { remote: 0, hybrid: 0, onsite: 0 };
    filteredJobs.forEach(j => {
        const rt = (j.remote_type || 'onsite').toLowerCase();
        if (remoteCounts[rt] !== undefined) {
            remoteCounts[rt]++;
        }
    });
    
    // Contract type counts
    const contractCounts = { 'full-time': 0, 'contract': 0, 'w2': 0, 'c2c': 0 };
    filteredJobs.forEach(j => {
        const ct = (j.contract_type || 'full-time').toLowerCase();
        if (contractCounts[ct] !== undefined) {
            contractCounts[ct]++;
        }
    });
    
    // Get maximum status count for funnel scaling
    const maxStatusCount = Math.max(...Object.values(statusCounts), 1);
    
    container.innerHTML = `
        <div class="analytics-container" style="display: flex; flex-direction: column;">
            <button class="btn btn-secondary btn-action btn-close-analytics" style="display: none; margin-bottom: 16px; align-self: flex-start; width: auto;">
                <i class="fa-solid fa-arrow-left"></i> Back to Feed
            </button>
            <!-- Scraper Visualization Container -->
            <div id="scheduler-viz-container" style="margin-bottom: 16px;">
                ${state.lastSchedulerVizHtml || `
                <div class="analytics-section-title" style="margin-bottom: 8px;"><i class="fa-solid fa-microchip"></i> Scraper Engine Status</div>
                <div style="text-align: center; padding: 12px; color: #999; font-size: 13px; background: rgba(255,255,255,0.02); border-radius: 8px; border: 1px dashed rgba(255,255,255,0.05);">
                    <i class="fa-solid fa-spinner fa-spin"></i> Loading scraper engine status...
                </div>
                `}
            </div>
            <!-- Grid Stats -->
            <div class="analytics-grid-stats">
                <div class="analytics-stat-card">
                    <span class="analytics-stat-val">${total}</span>
                    <span class="analytics-stat-label">Matching Roles</span>
                </div>
                <div class="analytics-stat-card">
                    <span class="analytics-stat-val">${avgScore}%</span>
                    <span class="analytics-stat-label">Avg Suitability</span>
                </div>
                <div class="analytics-stat-card">
                    <span class="analytics-stat-val">${targetPct}%</span>
                    <span class="analytics-stat-label">Focus Targets</span>
                </div>
                <div class="analytics-stat-card">
                    <span class="analytics-stat-val">${statusCounts.applied + statusCounts.interviewing}</span>
                    <span class="analytics-stat-label">Active Apps</span>
                </div>
            </div>
            
            <!-- Funnel Chart -->
            <div class="analytics-section">
                <div class="analytics-section-title"><i class="fa-solid fa-filter"></i> Pipeline Funnel Conversion</div>
                
                <div class="funnel-stage">
                    <div class="funnel-stage-header">
                        <span>Identified Roles</span>
                        <span>${statusCounts.identified}</span>
                    </div>
                    <div class="funnel-bar-bg">
                        <div class="funnel-bar-fill" style="width: ${(statusCounts.identified / maxStatusCount) * 100}%"></div>
                    </div>
                </div>
                
                <div class="funnel-stage">
                    <div class="funnel-stage-header">
                        <span>Applied</span>
                        <span>${statusCounts.applied}</span>
                    </div>
                    <div class="funnel-bar-bg">
                        <div class="funnel-bar-fill applied" style="width: ${(statusCounts.applied / maxStatusCount) * 100}%"></div>
                    </div>
                </div>
                
                <div class="funnel-stage">
                    <div class="funnel-stage-header">
                        <span>Interviewing</span>
                        <span>${statusCounts.interviewing}</span>
                    </div>
                    <div class="funnel-bar-bg">
                        <div class="funnel-bar-fill interviewing" style="width: ${(statusCounts.interviewing / maxStatusCount) * 100}%"></div>
                    </div>
                </div>
                
                <div class="funnel-stage">
                    <div class="funnel-stage-header">
                        <span>Offers Received</span>
                        <span>${statusCounts.offer}</span>
                    </div>
                    <div class="funnel-bar-bg">
                        <div class="funnel-bar-fill offer" style="width: ${(statusCounts.offer / maxStatusCount) * 100}%"></div>
                    </div>
                </div>
                
                <div class="funnel-stage">
                    <div class="funnel-stage-header">
                        <span>Archived</span>
                        <span>${statusCounts.archived}</span>
                    </div>
                    <div class="funnel-bar-bg">
                        <div class="funnel-bar-fill archived" style="width: ${(statusCounts.archived / maxStatusCount) * 100}%"></div>
                    </div>
                </div>
            </div>
            
            <!-- Workplace Distribution -->
            <div class="analytics-section">
                <div class="analytics-section-title"><i class="fa-solid fa-house-laptop"></i> Workplace Environment</div>
                <div class="distribution-list">
                    <div class="distribution-item">
                        <div class="distribution-meta">
                            <span>Remote</span>
                            <span>${remoteCounts.remote} (${total > 0 ? Math.round((remoteCounts.remote / total) * 100) : 0}%)</span>
                        </div>
                        <div class="distribution-bar-bg">
                            <div class="distribution-bar-fill remote" style="width: ${total > 0 ? (remoteCounts.remote / total) * 100 : 0}%"></div>
                        </div>
                    </div>
                    <div class="distribution-item">
                        <div class="distribution-meta">
                            <span>Hybrid</span>
                            <span>${remoteCounts.hybrid} (${total > 0 ? Math.round((remoteCounts.hybrid / total) * 100) : 0}%)</span>
                        </div>
                        <div class="distribution-bar-bg">
                            <div class="distribution-bar-fill hybrid" style="width: ${total > 0 ? (remoteCounts.hybrid / total) * 100 : 0}%"></div>
                        </div>
                    </div>
                    <div class="distribution-item">
                        <div class="distribution-meta">
                            <span>Onsite</span>
                            <span>${remoteCounts.onsite} (${total > 0 ? Math.round((remoteCounts.onsite / total) * 100) : 0}%)</span>
                        </div>
                        <div class="distribution-bar-bg">
                            <div class="distribution-bar-fill onsite" style="width: ${total > 0 ? (remoteCounts.onsite / total) * 100 : 0}%"></div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Contract Type Distribution -->
            <div class="analytics-section">
                <div class="analytics-section-title"><i class="fa-solid fa-file-contract"></i> Employment Types</div>
                <div class="distribution-list">
                    <div class="distribution-item">
                        <div class="distribution-meta">
                            <span>Full-Time</span>
                            <span>${contractCounts['full-time']}</span>
                        </div>
                        <div class="distribution-bar-bg">
                            <div class="distribution-bar-fill" style="width: ${total > 0 ? (contractCounts['full-time'] / total) * 100 : 0}%"></div>
                        </div>
                    </div>
                    <div class="distribution-item">
                        <div class="distribution-meta">
                            <span>Contract</span>
                            <span>${contractCounts['contract']}</span>
                        </div>
                        <div class="distribution-bar-bg">
                            <div class="distribution-bar-fill" style="width: ${total > 0 ? (contractCounts['contract'] / total) * 100 : 0}%"></div>
                        </div>
                    </div>
                    <div class="distribution-item">
                        <div class="distribution-meta">
                            <span>W2 Contract</span>
                            <span>${contractCounts['w2']}</span>
                        </div>
                        <div class="distribution-bar-bg">
                            <div class="distribution-bar-fill" style="width: ${total > 0 ? (contractCounts['w2'] / total) * 100 : 0}%"></div>
                        </div>
                    </div>
                    <div class="distribution-item">
                        <div class="distribution-meta">
                            <span>C2C Contract</span>
                            <span>${contractCounts['c2c']}</span>
                        </div>
                        <div class="distribution-bar-bg">
                            <div class="distribution-bar-fill" style="width: ${total > 0 ? (contractCounts['c2c'] / total) * 100 : 0}%"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

async function loadSchedulerViz() {
    const res = await apiRequest('/api/status');
    if (!res) {
        const errorHtml = `
            <div class="analytics-section-title" style="margin-bottom: 8px;"><i class="fa-solid fa-microchip"></i> Scraper Engine Status</div>
            <div style="color: var(--danger); padding: 12px; font-size: 13px; text-align: center; background: rgba(244,67,54,0.05); border-radius: 8px; border: 1px solid rgba(244,67,54,0.1);">
                <i class="fa-solid fa-triangle-exclamation"></i> Failed to load status.
            </div>`;
        state.lastSchedulerVizHtml = errorHtml;
        const vizContainer = document.getElementById('scheduler-viz-container');
        if (vizContainer) vizContainer.innerHTML = errorHtml;
        return;
    }
    
    const sched = res.scheduler || { running: false, jobs: [] };
    const history = res.scrape_history || [];
    
    const scrapeJob = sched.jobs.find(j => j.id === 'scraper_job');
    const isRunning = sched.running;
    
    let nextRunText = "Not scheduled";
    if (scrapeJob && scrapeJob.next_run_time && scrapeJob.next_run_time !== "None") {
        try {
            const cleanTime = scrapeJob.next_run_time.split('.')[0];
            const nextDate = new Date(cleanTime.replace(' ', 'T'));
            if (!isNaN(nextDate.getTime())) {
                nextRunText = nextDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            } else {
                const parts = cleanTime.split(' ');
                if (parts.length > 1) {
                    nextRunText = parts[1].substring(0, 5);
                } else {
                    nextRunText = scrapeJob.next_run_time.substring(11, 16);
                }
            }
        } catch (e) {
            nextRunText = "Scheduled";
        }
    }
    
    // Scraper history stats
    const totalScrapes = history.length;
    const totalIdentified = history.reduce((sum, h) => sum + (h.jobs_found || 0), 0);
    const totalNew = history.reduce((sum, h) => sum + (h.new_jobs || 0), 0);
    
    const successCount = history.filter(h => h.status === 'success').length;
    const successRate = totalScrapes > 0 ? Math.round((successCount / totalScrapes) * 100) : 100;
    
    const isScraperRunning = history.length > 0 && history[0].status === 'running';
    
    const vizHtml = `
        <div class="analytics-section-title" style="margin-bottom: 8px;"><i class="fa-solid fa-microchip"></i> Scraper Engine Status</div>
        <div class="scheduler-viz-card" style="
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 12px;
            padding: 14px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            backdrop-filter: blur(10px);
        ">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div class="${isRunning ? 'scheduler-viz-dot-active' : 'scheduler-viz-dot-inactive'}" style="
                        width: 9px; 
                        height: 9px; 
                        border-radius: 50%; 
                        background-color: ${isRunning ? '#4caf50' : '#f44336'};
                    "></div>
                    <span style="font-weight: 700; font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px; color: ${isRunning ? '#4caf50' : '#f44336'}">
                        ${isRunning ? 'Active Engine' : 'Offline'}
                    </span>
                </div>
                <div style="font-size: 12px; color: #a5a5a5;">
                    Next Run: <strong style="color: #fff; font-weight: 600;">${nextRunText}</strong>
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
                <div style="background: rgba(255,255,255,0.01); padding: 8px 10px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.03);">
                    <div style="font-size: 11px; color: #a5a5a5;">Total Scraped</div>
                    <div style="font-size: 16px; font-weight: 700; color: var(--primary); margin-top: 2px;">${totalIdentified}</div>
                </div>
                <div style="background: rgba(255,255,255,0.01); padding: 8px 10px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.03);">
                    <div style="font-size: 11px; color: #a5a5a5;">New Matches (Deduplicated)</div>
                    <div style="font-size: 16px; font-weight: 700; color: #4caf50; margin-top: 2px;">${totalNew}</div>
                </div>
            </div>
            
            <div style="display: flex; flex-direction: column; gap: 4px;">
                <div style="display: flex; justify-content: space-between; font-size: 11px; color: #a5a5a5;">
                    <span>Engine Health (Success Rate)</span>
                    <span style="font-weight: 700; color: #fff;">${successRate}%</span>
                </div>
                <div style="width: 100%; height: 5px; background: rgba(255,255,255,0.05); border-radius: 3px; overflow: hidden;">
                    <div style="width: ${successRate}%; height: 100%; background: linear-gradient(90deg, #2196f3, #4caf50); border-radius: 3px;"></div>
                </div>
            </div>
 
            <div style="display: flex; align-items: center; justify-content: space-between; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.04); margin-top: 4px;">
                <span style="font-size: 11px; color: #a5a5a5;">Scraper Activity:</span>
                ${isScraperRunning ? `
                <span style="font-size: 12px; font-weight: 700; color: #ff9800; display: flex; align-items: center; gap: 6px;">
                    <i class="fa-solid fa-spinner fa-spin"></i> Scraping in progress...
                </span>` : `
                <span style="font-size: 12px; font-weight: 600; color: #a5a5a5;">
                    Idle
                </span>`}
            </div>
        </div>
    `;
    state.lastSchedulerVizHtml = vizHtml;
    const vizContainer = document.getElementById('scheduler-viz-container');
    if (vizContainer) {
        vizContainer.innerHTML = vizHtml;
    }
}

function renderJobList(jobsList) {
    let container = jobListContainer;
    let emptySubtitle = "Initialize scraper & AI matching parameters to load job listings.";
    if (state.activePanel === 'panel-internship') {
        container = document.getElementById('internship-job-list-container');
        emptySubtitle = "Initialize scraper to load internship listings.";
    } else if (state.activePanel === 'panel-interested') {
        container = document.getElementById('interested-job-list-container');
        emptySubtitle = "Bookmark jobs by starring them to save them here.";
    }
    
    if (!container) return;
    container.innerHTML = '';
    
    if (jobsList.length === 0) {
        if (!state.hasSearched && state.activePanel !== 'panel-interested') {
            container.innerHTML = `
            <div class="activation-console-card">
                <div class="activation-glow-pulse-container">
                    <div class="glow-pulse-ring"></div>
                    <div class="glow-pulse-ring-inner"></div>
                    <div class="activation-icon-circle">
                        <i class="fa-solid fa-terminal"></i>
                    </div>
                </div>
                <h2>Console Inactive</h2>
                <p class="console-subtitle">${emptySubtitle}</p>
            </div>`;
        } else {
            container.innerHTML = `
            <div class="activation-console-card empty-search-state">
                <div class="activation-glow-pulse-container danger-glow">
                    <div class="glow-pulse-ring"></div>
                    <div class="activation-icon-circle danger-icon">
                        <i class="fa-solid fa-folder-open"></i>
                    </div>
                </div>
                <h2>Zero Matches</h2>
                <p class="console-subtitle">${state.activePanel === 'panel-interested' ? 'No interested jobs bookmarked yet.' : 'No postings found matching criteria.'}</p>
            </div>`;
        }
        return;
    }

    jobsList.forEach(job => {
        const card = document.createElement('div');
        card.className = `job-card ${state.selectedJobId === job.id ? 'selected' : ''}`;
        card.setAttribute('data-id', job.id);
        
        let scoreClass = 'score-mid';
        if (job.score >= 80) scoreClass = 'score-high';
        else if (job.score < 50) scoreClass = 'score-low';
        
        const isTarget = state.companies.some(c => (c.name || '').toLowerCase() === (job.company || '').toLowerCase());
        const remoteType = job.remote_type || 'remote';
        const contractType = job.contract_type || 'full-time';
        const visaType = job.visa_type || 'unknown';
        const jobScore = job.score || 0;

        const titleLower = (job.title || '').toLowerCase();
        const isInternship = contractType === 'internship' || 
                             titleLower.includes('intern') || 
                             titleLower.includes('co-op') || 
                             titleLower.includes('coop') || 
                             titleLower.includes('fellow');

        card.innerHTML = `
            <div class="card-top">
                <div class="card-title">${escapeHTML(job.title)}</div>
                <div class="score-badge ${scoreClass}">${jobScore}%</div>
            </div>
            <div class="card-company">${escapeHTML(job.company || 'Unknown Company')}</div>
            <div class="card-tags">
                ${job.is_recommended ? '<span class="card-tag tag-recommended" style="background: linear-gradient(135deg, #10b981, #059669); color: white;"><i class="fa-solid fa-thumbs-up"></i> Recommended Match</span>' : ''}
                ${isInternship ? '<span class="card-tag tag-internship" style="background: linear-gradient(135deg, #a855f7, #7e22ce); color: white;"><i class="fa-solid fa-graduation-cap"></i> Internship</span>' : ''}
                <span class="card-tag tag-${remoteType}">${remoteType}</span>
                ${visaType === 'h1b' ? '<span class="card-tag tag-visa">H1B Sponsor</span>' : ''}
                <span class="card-tag tag-${contractType === 'full-time' ? 'onsite' : 'hybrid'}">${contractType}</span>
                ${isTarget ? '<span class="card-tag tag-target"><i class="fa-solid fa-star"></i> Target</span>' : ''}
            </div>
            <div class="card-footer">
                <span>Location: ${escapeHTML(job.location || 'N/A')}</span>
                <span class="card-source">${escapeHTML(job.source || 'web')} &bull; ${formatDate(job.posted_date)}</span>
            </div>
        `;
        
        // Star/Interested Button
        const starBtn = document.createElement('button');
        const isStarred = state.interestedJobs.some(j => j.id === job.id);
        starBtn.className = `btn-star-job ${isStarred ? 'starred' : ''}`;
        starBtn.innerHTML = `<i class="${isStarred ? 'fa-solid' : 'fa-regular'} fa-star"></i>`;
        starBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleInterestedJob(job, starBtn);
        });
        
        const starContainer = document.createElement('div');
        starContainer.className = 'card-star-container';
        starContainer.appendChild(starBtn);
        card.appendChild(starContainer);

        card.addEventListener('click', () => {
            selectJob(job.id);
        });
        
        container.appendChild(card);
    });
}
async function selectJob(jobId) {
    state.selectedJobId = jobId;
    document.querySelectorAll('.job-card').forEach(card => {
        if (card.getAttribute('data-id') === jobId) {
            card.classList.add('selected');
        } else {
            card.classList.remove('selected');
        }
    });
    
    let container = detailsPanelContainer;
    let activeWorkspace = document.querySelector('#panel-home .workspace');
    if (state.activePanel === 'panel-internship') {
        container = document.getElementById('internship-details-panel-container');
        activeWorkspace = document.querySelector('#panel-internship .workspace');
    } else if (state.activePanel === 'panel-interested') {
        container = document.getElementById('interested-details-panel-container');
        activeWorkspace = document.querySelector('#panel-interested .workspace');
    }
    
    if (activeWorkspace) {
        activeWorkspace.classList.add('show-details');
    }
    
    // Automatically close the analytics overlay if a job card is selected
    const analyticsPanel = document.getElementById('analytics-panel-container');
    const btnToggleAnalytics = document.getElementById('btn-toggle-analytics');
    if (analyticsPanel) {
        analyticsPanel.classList.add('collapsed');
    }
    if (btnToggleAnalytics) {
        btnToggleAnalytics.classList.remove('active');
    }
    
    let job = state.jobs.find(j => j.id === jobId) || 
              state.internshipJobs.find(j => j.id === jobId) || 
              state.interestedJobs.find(j => j.id === jobId);
    
    if (job) {
        renderJobDetails(job);
    } else {
        container.innerHTML = `
        <div style="display:flex; justify-content:center; align-items:center; height:100%;">
            <i class="fa-solid fa-spinner fa-spin" style="font-size:32px; color:var(--primary);"></i>
        </div>`;
        
        job = await apiRequest(`/api/jobs/${jobId}`);
        if (job) {
            renderJobDetails(job);
        } else {
            container.innerHTML = `<div style="padding: 2rem; color: #999;">Job details not available.</div>`;
        }
    }
}
function renderJobDetails(job) {
    let container = detailsPanelContainer;
    if (state.activePanel === 'panel-internship') {
        container = document.getElementById('internship-details-panel-container');
    } else if (state.activePanel === 'panel-interested') {
        container = document.getElementById('interested-details-panel-container');
    }
    if (!container) return;

    // Initialize AI cache for this job in the client state
    state.generatedContent = state.generatedContent || {};
    state.generatedContent[job.id] = state.generatedContent[job.id] || {};

    // Score ring styling
    let scoreColor = 'var(--warning)';
    if (job.score >= 80) scoreColor = 'var(--success)';
    else if (job.score < 50) scoreColor = 'var(--danger)';
    
    // Check if target company
    const targetCompanyObj = state.companies.find(c => (c.name || '').toLowerCase() === (job.company || '').toLowerCase());
    const isTarget = !!targetCompanyObj;
    const companyPortalUrl = job.company_portal_url || (targetCompanyObj ? targetCompanyObj.portal_url : null);
    
    // Red flags parsing
    let redFlagsHtml = '';
    if (job.red_flags) {
        try {
            const flags = JSON.parse(job.red_flags);
            if (flags && flags.length > 0) {
                redFlagsHtml = `
                <div class="details-section">
                    <h3 class="section-title">Recruiter Red Flags</h3>
                    ${flags.map(f => `
                        <div class="red-flag-item">
                            <i class="fa-solid fa-triangle-exclamation"></i>
                            <span>${escapeHTML(f)}</span>
                        </div>
                    `).join('')}
                </div>`;
            }
        } catch (e) {
            console.error("Error parsing red flags JSON:", e);
        }
    }
    
    container.innerHTML = `
        <header class="details-hero" style="display: flex; flex-direction: column;">
            <button class="btn btn-secondary btn-action btn-back-to-feed" style="display: none; margin-bottom: 12px; align-self: flex-start;">
                <i class="fa-solid fa-arrow-left"></i> Back to List
            </button>
            <div class="details-title-row" style="display:flex; justify-content:space-between; align-items:flex-start; width:100%;">
                <h1>${escapeHTML(job.title)}</h1>
                <button class="btn-star-job btn-star-details ${state.interestedJobs.some(j => j.id === job.id) ? 'starred' : ''}" style="font-size: 24px; padding: 4px 10px;">
                    <i class="${state.interestedJobs.some(j => j.id === job.id) ? 'fa-solid' : 'fa-regular'} fa-star"></i>
                </button>
            </div>
            
            <div class="details-subtitle">
                <span>${escapeHTML(job.company)}</span>
                ${companyPortalUrl ? `
                    <a href="${escapeHTML(companyPortalUrl)}" target="_blank" style="margin-left: 6px;" title="Visit Career Portal">
                        <i class="fa-solid fa-up-right-from-square" style="font-size: 11px;"></i> Career Portal
                    </a>` : ''
                } &bull; 
                <span>${escapeHTML(job.location)}</span>
            </div>
            
            <div class="details-meta-row">
                <div class="details-meta-pill">
                    <span class="meta-label">Est. Salary</span>
                    <span class="meta-value" style="color:var(--success);">${escapeHTML(job.salary || 'Not disclosed')}</span>
                </div>
                <div class="details-meta-pill">
                    <span class="meta-label">Job Source</span>
                    <span class="meta-value" style="text-transform:capitalize;">${escapeHTML(job.source)}</span>
                </div>
                <div class="details-meta-pill">
                    <span class="meta-label">Work Setting</span>
                    <span class="meta-value">${escapeHTML((job.remote_type || '').toUpperCase())}</span>
                </div>
                <div class="details-meta-pill">
                    <span class="meta-label">Date Scraped</span>
                    <span class="meta-value">${formatDate(job.created_at)}</span>
                </div>
                <div class="details-meta-pill">
                    <span class="meta-label">Date Posted</span>
                    <span class="meta-value">${formatDate(job.posted_date) || 'Not disclosed'}</span>
                </div>
            </div>
            
            <!-- Actions panel -->
            <div class="action-strip">
                <a href="${job.job_url}" target="_blank" class="btn btn-primary">
                    Apply on Source <i class="fa-solid fa-arrow-up-right-from-square"></i>
                </a>
                ${companyPortalUrl ? `
                <a href="${escapeHTML(companyPortalUrl)}" target="_blank" class="btn btn-secondary">
                    Company Portal <i class="fa-solid fa-link"></i>
                </a>
                ` : ''}
                
                <button id="btn-auto-apply" class="btn btn-primary" style="background-color: #8a2be2; border-color: #8a2be2; color: white;" onclick="window.handleAutoApplyClick('${job.id}')">
                    <i class="fa-solid fa-robot"></i> Auto-Apply
                </button>
                
                <div class="pipeline-group">
                    <div class="pipeline-label">Pipeline Status:</div>
                    <select id="details-pipeline-select" class="pipeline-select">
                        <option value="identified" ${job.status === 'identified' ? 'selected' : ''}>Identified</option>
                        <option value="applied" ${job.status === 'applied' ? 'selected' : ''}>Applied</option>
                        <option value="interviewing" ${job.status === 'interviewing' ? 'selected' : ''}>Interviewing</option>
                        <option value="offer" ${job.status === 'offer' ? 'selected' : ''}>Offer Received</option>
                        <option value="archived" ${job.status === 'archived' ? 'selected' : ''}>Archived</option>
                    </select>
                </div>
            </div>
            
            <div id="auto-apply-status-container" style="display: none; margin-top: 12px; padding: 12px; border-radius: 6px; border: 1px dashed var(--border-color); background: rgba(0,0,0,0.05); font-family: monospace; font-size: 11px;">
                <div style="font-weight: bold; margin-bottom: 6px; display: flex; justify-content: space-between; align-items: center;">
                    <span id="auto-apply-status-header"><i class="fa-solid fa-spinner fa-spin"></i> Auto-Apply Status:</span>
                    <span id="auto-apply-status-tag" style="padding: 2px 6px; border-radius: 4px; font-size: 9px; text-transform: uppercase; background: #e0e0e0; color: #333;">idle</span>
                </div>
                <div id="auto-apply-status-log" style="white-space: pre-wrap; color: var(--text-secondary); max-height: 120px; overflow-y: auto;"></div>
                <div id="auto-apply-status-actions" style="margin-top: 8px; display: flex; gap: 8px; justify-content: flex-end;"></div>
            </div>
        </header>
        
        <div class="details-body">
            <!-- Premium Details Navigation Tabs -->
            <div class="details-tabs-header">
                <button class="details-tab-btn active" data-pane="pane-assessment">
                    <i class="fa-solid fa-magnifying-glass"></i> Assessment
                </button>
                <button class="details-tab-btn" data-pane="pane-outreach">
                    <i class="fa-solid fa-paper-plane"></i> Outreach Hub
                </button>
                <button class="details-tab-btn" data-pane="pane-tailoring">
                    <i class="fa-solid fa-wand-magic-sparkles"></i> AI Tailor Suite
                </button>
                <button class="details-tab-btn" data-pane="pane-interview">
                    <i class="fa-solid fa-circle-question"></i> Prep Guide
                </button>
            </div>
            
            <!-- Pane 1: Assessment -->
            <div class="details-tab-pane active" id="pane-assessment">
                <div class="details-section">
                    <h3 class="section-title">Senior Recruiter Assessment</h3>
                    <div class="alignment-card">
                        <div class="alignment-score-row">
                            <div class="alignment-score-circle" style="border:3px solid ${scoreColor}; color:${scoreColor}">
                                ${job.score}%
                            </div>
                            <div class="alignment-insight">
                                <strong>Candidate Fit Suitability:</strong> ${job.score >= 80 ? 'Excellent Match. Matches key competencies.' : job.score >= 60 ? 'Moderate Match. Matches baseline but needs tweaks.' : 'Low Match. Missing alignment points.'}
                                ${isTarget ? '<br><span style="color:var(--gold); font-weight:bold;"><i class="fa-solid fa-star"></i> Focus target company.</span>' : ''}
                            </div>
                        </div>
                        <div class="alignment-text">
                            ${escapeHTML(job.reason || 'Keyword matches found. Resume AI validation not executed.')}
                        </div>
                    </div>
                </div>
                ${redFlagsHtml}
                ${renderStructuredJobDetails(job)}
            </div>
            
            <!-- Pane 2: Outreach Hub -->
            <div class="details-tab-pane" id="pane-outreach">
                <div class="details-section">
                    <h3 class="section-title">Recruiter Outreach Templates</h3>
                    <div id="outreach-content-area">
                        <div class="ai-gen-btn-container">
                            <i class="fa-solid fa-paper-plane ai-gen-icon"></i>
                            <p>Generate highly tailored templates (LinkedIn Connection Request, Recruitment Cold Email, and 1-Week Follow-up) customized for your resume and this role.</p>
                            <button class="btn btn-primary btn-ai-spark" id="btn-generate-outreach">
                                <i class="fa-solid fa-sparkles"></i> Generate Outreach Suite
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Pane 3: AI Tailoring Suite -->
            <div class="details-tab-pane" id="pane-tailoring">
                <div class="details-section">
                    <h3 class="section-title">AI Resume Tailoring & Cover Letter</h3>
                    <div id="tailoring-content-area">
                        <div class="ai-gen-btn-container">
                            <i class="fa-solid fa-wand-magic-sparkles ai-gen-icon"></i>
                            <p>Get actionable suggestions to adjust your resume bullets and generate a tailored, professional Cover Letter for this role.</p>
                            <button class="btn btn-primary btn-ai-spark" id="btn-generate-tailoring">
                                <i class="fa-solid fa-sparkles"></i> Generate Tailored Materials
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Pane 4: Interview Prep Guide -->
            <div class="details-tab-pane" id="pane-interview">
                <div class="details-section">
                    <h3 class="section-title">Mock Interview Preparation</h3>
                    <div id="interview-content-area">
                        <div class="ai-gen-btn-container">
                            <i class="fa-solid fa-circle-question ai-gen-icon"></i>
                            <p>Generate mock interview questions and answers specifically tailored to this job description and your resume context.</p>
                            <button class="btn btn-primary btn-ai-spark" id="btn-generate-interview">
                                <i class="fa-solid fa-sparkles"></i> Generate Interview Q&A
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Original Description Accordion -->
            <div class="details-section">
                <details class="details-original">
                    <summary>
                        <span>View Original Job Posting Text</span>
                        <i class="fa-solid fa-chevron-down" style="font-size:12px; margin-left:auto;"></i>
                    </summary>
                    <div class="details-original-content">
                        <div class="description-text">${escapeHTML(job.description || 'No description body available.')}</div>
                    </div>
                </details>
            </div>
        </div>
    `;
    
    // Add event listeners on details elements
    container.querySelector('#details-pipeline-select').addEventListener('change', async (e) => {
        const newStatus = e.target.value;
        const res = await apiRequest(`/api/jobs/${job.id}/status`, 'PUT', { status: newStatus });
        if (res) {
            showToast(`Pipeline status updated: ${newStatus.toUpperCase()}`);
            // Update local state and redraw feed
            const jobIndex = state.jobs.findIndex(j => j.id === job.id);
            if (jobIndex !== -1) {
                state.jobs[jobIndex].status = newStatus;
                filterAndRenderJobs();
            }
        }
    });

    // Handle Tab switching inside details body
    const detailTabs = container.querySelectorAll('.details-tab-btn');
    const detailPanes = container.querySelectorAll('.details-tab-pane');
    
    detailTabs.forEach(btn => {
        btn.addEventListener('click', () => {
            detailTabs.forEach(b => b.classList.remove('active'));
            detailPanes.forEach(p => p.classList.remove('active'));
            
            btn.classList.add('active');
            const targetPane = btn.getAttribute('data-pane');
            container.querySelector('#' + targetPane).classList.add('active');
            
            // Render cached contents if present
            if (targetPane === 'pane-outreach' && state.generatedContent[job.id].outreach) {
                renderOutreachSuite(job.id);
            } else if (targetPane === 'pane-tailoring' && state.generatedContent[job.id].tailoring) {
                renderTailoringSuite(job.id);
            } else if (targetPane === 'pane-interview' && state.generatedContent[job.id].interview) {
                renderInterviewPrep(job.id);
            }
        });
    });

    // Wire up AI generator triggers if not already cached
    const wireOutreachBtn = () => {
        const btn = container.querySelector('#btn-generate-outreach');
        if (btn) {
            btn.addEventListener('click', async () => {
                const area = container.querySelector('#outreach-content-area');
                area.innerHTML = `
                    <div style="display:flex; flex-direction:column; justify-content:center; align-items:center; height:150px; gap: 10px;">
                        <i class="fa-solid fa-spinner fa-spin" style="font-size:32px; color:var(--primary);"></i>
                        <span style="font-size:12px; color:var(--text-secondary);">Generating recruitment outreach templates...</span>
                    </div>`;
                
                const res = await apiRequest(`/api/jobs/ai/outreach-templates`, 'POST', {
                    title: job.title || '',
                    company: job.company || '',
                    description: job.description || ''
                });
                if (res) {
                    state.generatedContent[job.id].outreach = res;
                    renderOutreachSuite(job.id);
                } else {
                    const errMsg = window.lastApiErrorMessage || "Please ensure AI settings are configured correctly.";
                    area.innerHTML = `
                        <div class="ai-gen-btn-container">
                            <i class="fa-solid fa-triangle-exclamation" style="font-size:24px; color:var(--danger);"></i>
                            <p style="color:var(--danger); font-size:12px; margin-top:8px; max-width:90%; text-align:center;">Generation failed: ${errMsg}</p>
                            <button class="btn btn-primary" id="btn-generate-outreach" style="margin-top:10px;">Try Again</button>
                        </div>`;
                    wireOutreachBtn();
                }
            });
        }
    };
    wireOutreachBtn();

    const wireTailoringBtn = () => {
        const btn = container.querySelector('#btn-generate-tailoring');
        if (btn) {
            btn.addEventListener('click', async () => {
                const area = container.querySelector('#tailoring-content-area');
                area.innerHTML = `
                    <div style="display:flex; flex-direction:column; justify-content:center; align-items:center; height:150px; gap: 10px;">
                        <i class="fa-solid fa-spinner fa-spin" style="font-size:32px; color:var(--primary);"></i>
                        <span style="font-size:12px; color:var(--text-secondary);">Analyzing requirements and generating CV tailoring tips...</span>
                    </div>`;
                
                const tipsRes = await apiRequest(`/api/jobs/ai/tailor`, 'POST', {
                    title: job.title || '',
                    company: job.company || '',
                    description: job.description || ''
                });
                
                if (tipsRes) {
                    area.innerHTML = `
                        <div style="display:flex; flex-direction:column; justify-content:center; align-items:center; height:150px; gap: 10px;">
                            <i class="fa-solid fa-spinner fa-spin" style="font-size:32px; color:var(--primary);"></i>
                            <span style="font-size:12px; color:var(--text-secondary);">Generating tailored Cover Letter...</span>
                        </div>`;
                    
                    const clRes = await apiRequest(`/api/jobs/ai/cover-letter`, 'POST', {
                        title: job.title || '',
                        company: job.company || '',
                        description: job.description || ''
                    });
                    
                    if (clRes) {
                        state.generatedContent[job.id].tailoring = { tips: tipsRes.tips, cover_letter: clRes.cover_letter };
                        renderTailoringSuite(job.id);
                        return;
                    }
                }
                
                const errMsg = window.lastApiErrorMessage || "Please ensure AI settings are configured correctly.";
                area.innerHTML = `
                    <div class="ai-gen-btn-container">
                        <i class="fa-solid fa-triangle-exclamation" style="font-size:24px; color:var(--danger);"></i>
                        <p style="color:var(--danger); font-size:12px; margin-top:8px; max-width:90%; text-align:center;">Failed to tailor materials: ${errMsg}</p>
                        <button class="btn btn-primary" id="btn-generate-tailoring" style="margin-top:10px;">Try Again</button>
                    </div>`;
                wireTailoringBtn();
            });
        }
    };
    wireTailoringBtn();

    const wireInterviewBtn = () => {
        const btn = container.querySelector('#btn-generate-interview');
        if (btn) {
            btn.addEventListener('click', async () => {
                const area = container.querySelector('#interview-content-area');
                area.innerHTML = `
                    <div style="display:flex; flex-direction:column; justify-content:center; align-items:center; height:150px; gap: 10px;">
                        <i class="fa-solid fa-spinner fa-spin" style="font-size:32px; color:var(--primary);"></i>
                        <span style="font-size:12px; color:var(--text-secondary);">Simulating mock interview prep questions...</span>
                    </div>`;
                
                const res = await apiRequest(`/api/jobs/ai/mock-interview`, 'POST', {
                    title: job.title || '',
                    company: job.company || '',
                    description: job.description || ''
                });
                if (res) {
                    state.generatedContent[job.id].interview = res.qa;
                    renderInterviewPrep(job.id);
                } else {
                    const errMsg = window.lastApiErrorMessage || "Please ensure AI settings are configured correctly.";
                    area.innerHTML = `
                        <div class="ai-gen-btn-container">
                            <i class="fa-solid fa-triangle-exclamation" style="font-size:24px; color:var(--danger);"></i>
                            <p style="color:var(--danger); font-size:12px; margin-top:8px; max-width:90%; text-align:center;">Mock interview generation failed: ${errMsg}</p>
                            <button class="btn btn-primary" id="btn-generate-interview" style="margin-top:10px;">Try Again</button>
                        </div>`;
                    wireInterviewBtn();
                }
            });
        }
    };
    wireInterviewBtn();
    // Wire up star button click in details
    const starBtnDetails = container.querySelector('.btn-star-details');
    if (starBtnDetails) {
        starBtnDetails.addEventListener('click', () => {
            toggleInterestedJob(job, starBtnDetails);
        });
    }

}

function getActiveDetailsContainer() {
    if (state.activePanel === 'panel-internship') {
        return document.getElementById('internship-details-panel-container');
    } else if (state.activePanel === 'panel-interested') {
        return document.getElementById('interested-details-panel-container');
    } else {
        return document.getElementById('details-panel-container');
    }
}

function renderOutreachSuite(jobId) {
    const outreach = state.generatedContent[jobId].outreach;
    const container = getActiveDetailsContainer();
    const area = container ? container.querySelector('#outreach-content-area') : null;
    if (!outreach || !area) return;
    
    area.innerHTML = `
        <div class="outreach-sub-tabs">
            <button class="outreach-sub-tab-btn active" data-outreach-type="linkedin">LinkedIn Invite</button>
            <button class="outreach-sub-tab-btn" data-outreach-type="email">Cold Email</button>
            <button class="outreach-sub-tab-btn" data-outreach-type="followup">1-Week Follow-up</button>
        </div>
        <div class="pitch-container" style="margin-top: 10px;">
            <div class="pitch-text" id="outreach-text-content" style="white-space: pre-wrap;">${escapeHTML(outreach.linkedin_note)}</div>
            <div style="display:flex; justify-content:flex-end; margin-top:10px;">
                <button class="btn btn-secondary" id="btn-copy-outreach">
                    <i class="fa-regular fa-copy"></i> Copy Note
                </button>
            </div>
        </div>
    `;
    
    const tabs = area.querySelectorAll('.outreach-sub-tab-btn');
    const textContent = area.querySelector('#outreach-text-content');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            const type = tab.getAttribute('data-outreach-type');
            if (type === 'linkedin') {
                textContent.textContent = outreach.linkedin_note;
            } else if (type === 'email') {
                textContent.textContent = outreach.recruiter_email;
            } else {
                textContent.textContent = outreach.followup_message;
            }
        });
    });
    
    area.querySelector('#btn-copy-outreach').addEventListener('click', () => {
        navigator.clipboard.writeText(textContent.textContent).then(() => {
            showToast("Template note copied to clipboard!");
        });
    });
}

function renderTailoringSuite(jobId) {
    const tailoring = state.generatedContent[jobId].tailoring;
    const container = getActiveDetailsContainer();
    const area = container ? container.querySelector('#tailoring-content-area') : null;
    if (!tailoring || !area) return;
    
    const tipsHtml = tailoring.tips.map(tip => `
        <div class="tailoring-tip-item">
            <i class="fa-solid fa-circle-arrow-right"></i>
            <span>${escapeHTML(tip)}</span>
        </div>
    `).join('');
    
    area.innerHTML = `
        <h4 style="font-size:11px; font-weight:700; color:var(--text-secondary); margin-bottom:10px; text-transform:uppercase;">CV Adjustments for this role</h4>
        <div style="margin-bottom: 20px;">
            ${tipsHtml}
        </div>
        
        <h4 style="font-size:11px; font-weight:700; color:var(--text-secondary); margin-bottom:10px; text-transform:uppercase;">Tailored Cover Letter</h4>
        <div class="pitch-container">
            <div class="pitch-text" id="cover-letter-text-content" style="white-space: pre-wrap; font-size:12.5px; line-height:1.6;">${escapeHTML(tailoring.cover_letter)}</div>
            <div style="display:flex; justify-content:flex-end; margin-top:10px;">
                <button class="btn btn-secondary" id="btn-copy-cover-letter">
                    <i class="fa-regular fa-copy"></i> Copy Cover Letter
                </button>
            </div>
        </div>
    `;
    
    area.querySelector('#btn-copy-cover-letter').addEventListener('click', () => {
        navigator.clipboard.writeText(tailoring.cover_letter).then(() => {
            showToast("Tailored cover letter copied!");
        });
    });
}

function renderInterviewPrep(jobId) {
    const qa = state.generatedContent[jobId].interview;
    const container = getActiveDetailsContainer();
    const area = container ? container.querySelector('#interview-content-area') : null;
    if (!qa || !area) return;
    
    const qaHtml = qa.map((item, idx) => `
        <div class="interview-qa-item">
            <div class="interview-q">
                <i class="fa-solid fa-circle-question"></i>
                <span>Q${idx+1}: ${escapeHTML(item.question)}</span>
            </div>
            <div class="interview-a">
                <strong>Talking Points & Answer:</strong><br>
                ${escapeHTML(item.answer)}
            </div>
        </div>
    `).join('');
    
    area.innerHTML = `
        <div style="margin-top: 10px;">
            ${qaHtml}
        </div>
    `;
}

// --- Modal Helper Actions ---
function updateModelSuggestions(selectEl, inputEl, datalistEl) {
    const provider = selectEl.value;
    let models = [];
    if (provider === 'gemini') {
        models = ['gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-1.5-pro'];
    } else if (provider === 'openai') {
        models = ['gpt-4o-mini', 'gpt-4o', 'gpt-3.5-turbo'];
    } else if (provider === 'claude') {
        models = ['claude-sonnet-4-6', 'claude-haiku-4-5', 'claude-opus-4-8'];
    } else if (provider === 'groq') {
        models = ['llama-3.3-70b-versatile', 'llama3-8b-8192', 'llama3-70b-8192', 'mixtral-8x7b-32768'];
    } else if (provider === 'gorx') {
        models = ['grok-2-latest', 'grok-beta'];
    } else if (provider === 'deepseek') {
        models = ['deepseek-v4-flash', 'deepseek-v4-pro', 'deepseek-reasoner', 'deepseek-chat'];
    }
    
    datalistEl.innerHTML = models.map(m => `<option value="${m}">${m}</option>`).join('');
    
    // If the input is currently empty, we auto-fill it with the first recommended model
    if (!inputEl.value) {
        inputEl.value = models[0] || '';
    }
}

function addAiConfigRow(provider = 'gemini', model = '', key = '') {
    const container = document.getElementById('ai-configs-container');
    if (!container) return;
    const index = container.children.length + 1;
    
    const card = document.createElement('div');
    card.className = 'ai-config-card';
    card.style.border = '1px solid var(--border-color)';
    card.style.borderRadius = '8px';
    card.style.padding = '16px';
    card.style.backgroundColor = 'rgba(255, 255, 255, 0.02)';
    card.style.position = 'relative';
    card.style.marginBottom = '12px';
    
    const datalistId = `models-list-${Math.random().toString(36).substring(2, 9)}`;
    
    card.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <span style="font-weight: 600; font-size: 13px; color: var(--primary);">Configuration #${index}</span>
            <button class="btn-remove-ai-config" style="background: none; border: none; color: #ef4444; cursor: pointer; font-size: 12px; display: flex; align-items: center; gap: 4px;">
                <i class="fa-solid fa-trash-can"></i> Remove
            </button>
        </div>
        <div class="form-row" style="margin-bottom: 12px;">
            <label style="display: block; font-size: 12px; font-weight: 500; margin-bottom: 6px; color: var(--text-secondary);">AI Provider</label>
            <select class="form-select config-provider" style="width: 100%; border-radius: 6px; background: var(--bg-card); border: 1px solid var(--border-color); color: var(--text-primary); padding: 8px 12px;">
                <option value="gemini">Google Gemini</option>
                <option value="openai">OpenAI ChatGPT</option>
                <option value="claude">Anthropic Claude</option>
                <option value="groq">Groq</option>
                <option value="gorx">X.AI Grok</option>
                <option value="deepseek">DeepSeek</option>
            </select>
        </div>
        <div class="form-row" style="margin-bottom: 12px;">
            <label style="display: block; font-size: 12px; font-weight: 500; margin-bottom: 6px; color: var(--text-secondary);">Model Name</label>
            <input type="text" class="config-model" list="${datalistId}" placeholder="Select or type model name" value="${model}" style="width: 100%; border-radius: 6px; background: var(--bg-card); border: 1px solid var(--border-color); color: var(--text-primary); padding: 8px 12px;">
            <datalist id="${datalistId}"></datalist>
            <span style="display:block; font-size:10px; color:var(--text-muted); margin-top:4px;">Double-click input to view recommended list for selected provider.</span>
        </div>
        <div class="form-row" style="margin-bottom: 0;">
            <label style="display: block; font-size: 12px; font-weight: 500; margin-bottom: 6px; color: var(--text-secondary);">API Key</label>
            <input type="text" class="config-key" placeholder="Enter API Key" autocomplete="off" value="${key}" style="width: 100%; border-radius: 6px; background: var(--bg-card); border: 1px solid var(--border-color); color: var(--text-primary); padding: 8px 12px;">
        </div>
    `;
    
    // Select the proper option
    const select = card.querySelector('.config-provider');
    const input = card.querySelector('.config-model');
    const datalist = card.querySelector('datalist');
    
    if (select && input && datalist) {
        select.value = provider;
        updateModelSuggestions(select, input, datalist);
        
        if (model) {
            input.value = model;
        }
        
        select.addEventListener('change', () => {
            input.value = '';
            updateModelSuggestions(select, input, datalist);
        });
    }
    
    // Add remove event listener
    card.querySelector('.btn-remove-ai-config').addEventListener('click', () => {
        card.remove();
        reindexAiConfigs();
    });
    
    container.appendChild(card);
}

function reindexAiConfigs() {
    const cards = document.querySelectorAll('#ai-configs-container .ai-config-card');
    cards.forEach((card, idx) => {
        const titleSpan = card.querySelector('span');
        if (titleSpan) {
            titleSpan.textContent = `Configuration #${idx + 1}`;
        }
    });
}

function fillSettingsForm() {
    // Populate form fields
    document.getElementById('form-search-terms').value = state.settings.search_terms || '';
    document.getElementById('form-locations').value = state.settings.locations || '';
    document.getElementById('form-scrape-country').value = state.settings.scrape_country || 'USA';
    document.getElementById('form-resume-text').value = state.settings.resume_text || '';
    
    // Auto-apply details
    document.getElementById('form-candidate-first-name').value = state.settings.candidate_first_name || '';
    document.getElementById('form-candidate-last-name').value = state.settings.candidate_last_name || '';
    document.getElementById('form-candidate-email').value = state.settings.candidate_email || '';
    document.getElementById('form-candidate-phone').value = state.settings.candidate_phone || '';
    document.getElementById('form-candidate-linkedin').value = state.settings.candidate_linkedin || '';
    document.getElementById('form-candidate-github').value = state.settings.candidate_github || '';
    document.getElementById('form-candidate-portfolio').value = state.settings.candidate_portfolio || '';
    document.getElementById('form-resume-file-path').value = state.settings.resume_file_path || '';
    
    document.getElementById('form-email-recipient').value = state.settings.email_recipient || '';
    document.getElementById('form-min-score').value = state.settings.min_relevance_score || '50';
    
    document.getElementById('form-scrape-interval').value = state.settings.scrape_interval_mins || '10';
    document.getElementById('form-email-interval').value = state.settings.email_interval_hours || '1';

    // Email subscription settings
    const emailNotificationsEnabled = state.settings.email_notifications_enabled === 'true' || state.settings.email_notifications_enabled === true;
    document.getElementById('form-email-notifications-enabled').checked = emailNotificationsEnabled;
    document.getElementById('form-email-alert-job-title').value = state.settings.email_alert_job_title || '';
    document.getElementById('form-email-alert-location').value = state.settings.email_alert_location || '';

    // Populate dynamic AI Configurations
    const container = document.getElementById('ai-configs-container');
    if (container) {
        container.innerHTML = '';
        const providers = (state.settings.ai_provider || '').split(',').map(s => s.trim()).filter(s => s);
        const models = (state.settings.ai_model || '').split(',').map(s => s.trim()).filter(s => s);
        const keys = (state.settings.ai_api_key || '').split(',').map(s => s.trim()).filter(s => s);
        
        const count = Math.max(providers.length, models.length, keys.length);
        if (count === 0) {
            // Add a default blank one
            addAiConfigRow('gemini', '', '');
        } else {
            for (let i = 0; i < count; i++) {
                addAiConfigRow(
                    providers[i] || 'gemini',
                    models[i] || '',
                    keys[i] || ''
                );
            }
        }
        
        // Sync the full list to browser localStorage for request headers compatibility
        const fullProv = providers.join(',');
        const fullModel = models.join(',');
        const fullKey = keys.join(',');
        localStorage.setItem('ai_model_provider', fullProv);
        localStorage.setItem('ai_model_name', fullModel);
        if (fullKey && fullKey !== '********') {
            localStorage.setItem('ai_api_key', fullKey);
        }
    }

    // Jobspy boards checkboxes
    const activeBoards = (state.settings.job_boards || '').split(',').map(b => b.trim());
    document.querySelectorAll('input[name="form-boards"]').forEach(chk => {
        chk.checked = activeBoards.includes(chk.value);
    });

    renderCompanyTags();
    
    // Display modal
    if (settingsModal) settingsModal.style.display = 'flex';
}

async function saveSettings() {
    const selectedBoards = Array.from(document.querySelectorAll('input[name="form-boards"]:checked')).map(c => c.value).join(',');
    
    // Gather dynamic AI configs
    const configCards = document.querySelectorAll('#ai-configs-container .ai-config-card');
    const providers = [];
    const models = [];
    const keys = [];
    
    configCards.forEach(card => {
        const prov = card.querySelector('.config-provider').value.trim();
        const mod = card.querySelector('.config-model').value.trim();
        const key = card.querySelector('.config-key').value.trim();
        providers.push(prov);
        models.push(mod);
        keys.push(key);
    });
    
    const aiProvider = providers.join(',');
    const aiModel = models.join(',');
    const aiApiKey = keys.join(',');
    
    localStorage.setItem('ai_model_provider', aiProvider);
    localStorage.setItem('ai_model_name', aiModel);
    if (aiApiKey !== '********') {
        localStorage.setItem('ai_api_key', aiApiKey);
    }
    
    const settingsPayload = {
        search_terms: document.getElementById('form-search-terms').value.trim(),
        locations: document.getElementById('form-locations').value.trim(),
        scrape_country: document.getElementById('form-scrape-country').value.trim() || 'USA',
        job_boards: selectedBoards,
        resume_text: document.getElementById('form-resume-text').value.trim(),
        
        candidate_first_name: document.getElementById('form-candidate-first-name').value.trim(),
        candidate_last_name: document.getElementById('form-candidate-last-name').value.trim(),
        candidate_email: document.getElementById('form-candidate-email').value.trim(),
        candidate_phone: document.getElementById('form-candidate-phone').value.trim(),
        candidate_linkedin: document.getElementById('form-candidate-linkedin').value.trim(),
        candidate_github: document.getElementById('form-candidate-github').value.trim(),
        candidate_portfolio: document.getElementById('form-candidate-portfolio').value.trim(),
        resume_file_path: document.getElementById('form-resume-file-path').value.trim(),
        
        email_recipient: document.getElementById('form-email-recipient').value.trim(),
        min_relevance_score: document.getElementById('form-min-score').value.trim(),
        
        scrape_interval_mins: document.getElementById('form-scrape-interval').value.trim(),
        email_interval_hours: document.getElementById('form-email-interval').value.trim(),

        email_notifications_enabled: document.getElementById('form-email-notifications-enabled').checked ? 'true' : 'false',
        email_alert_job_title: document.getElementById('form-email-alert-job-title').value.trim(),
        email_alert_location: document.getElementById('form-email-alert-location').value.trim(),

        ai_provider: aiProvider,
        ai_model: aiModel,
        ai_api_key: aiApiKey
    };
    
    const res = await apiRequest('/api/settings', 'POST', settingsPayload);
    if (res) {
        state.settings = res.settings;
        updateInterviewAssistantSubtitle();
        showToast("System configuration updated successfully.");
        
        // Refresh feed with new score filters
        const ms = parseInt(res.settings.min_relevance_score || '50');
        state.filters.minScore = ms;
        scoreSlider.value = ms;
        scoreVal.textContent = ms;
        
        await fetchJobs(); // Recalculate match lists
    }
}

function renderCompanyTags() {
    companiesTagsContainer.innerHTML = '';
    state.companies.forEach(company => {
        const name = company.name;
        const url = company.portal_url;
        const tag = document.createElement('div');
        tag.className = 'company-tag';
        tag.innerHTML = `
            <span>
                ${escapeHTML(name)} 
                ${url ? `<a href="${escapeHTML(url)}" target="_blank" style="color:var(--primary); margin-left:4px;" title="Visit Career Site"><i class="fa-solid fa-link" style="font-size:10px;"></i></a>` : ''}
            </span>
            <button class="btn-tag-delete" data-name="${name}"><i class="fa-solid fa-xmark"></i></button>
        `;
        tag.querySelector('.btn-tag-delete').addEventListener('click', async (e) => {
            const name = e.currentTarget.getAttribute('data-name');
            const res = await apiRequest(`/api/target-companies/${name}`, 'DELETE');
            if (res) {
                state.companies = res.companies;
                renderCompanyTags();
                showToast(`Company '${name}' removed from priority target list.`);
                await fetchJobs(); // update score metrics
            }
        });
        companiesTagsContainer.appendChild(tag);
    });
}

// --- Status Dashboard and Logs ---
async function loadSystemLogs(silent = false) {
    if (!silent) {
        document.getElementById('status-scheduler').textContent = "Checking...";
        document.getElementById('logs-table-body').innerHTML = `
            <tr><td colspan="5" style="text-align:center;">Loading history logs...</td></tr>`;
    }
        
    const res = await apiRequest('/api/status');
    if (res) {
        // Scheduler panel
        const sched = res.scheduler;
        document.getElementById('status-scheduler').innerHTML = sched.running ? 
            '<span style="color:var(--success); font-weight:bold;"><i class="fa-solid fa-circle-check"></i> Active</span>' : 
            '<span style="color:var(--danger); font-weight:bold;"><i class="fa-solid fa-circle-xmark"></i> Inactive</span>';
            
        // Update scraper active card if present
        const scraperActiveEl = document.getElementById('status-scraper-active');
        if (scraperActiveEl) {
            const isScraperRunning = res.scrape_history.length > 0 && res.scrape_history[0].status === 'running';
            scraperActiveEl.innerHTML = isScraperRunning ? 
                '<span style="color:#ff9800; font-weight:bold;"><i class="fa-solid fa-spinner fa-spin"></i> Scraping...</span>' : 
                '<span style="color:var(--text-muted); font-weight:normal;">Idle</span>';
        }
            
        const scrapeJob = sched.jobs.find(j => j.id === 'scraper_job');
        const emailJob = sched.jobs.find(j => j.id === 'email_job');
        
        document.getElementById('status-next-scrape').textContent = scrapeJob ? formatLogTime(scrapeJob.next_run_time) : 'Disabled';
        document.getElementById('status-next-email').textContent = emailJob ? formatLogTime(emailJob.next_run_time) : 'Disabled';
        
        // History log table
        const tbody = document.getElementById('logs-table-body');
        tbody.innerHTML = '';
        if (res.scrape_history.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; color:var(--text-muted);">No log records yet. Run your first scrape cycle.</td></tr>';
            return;
        }
        
        res.scrape_history.forEach(log => {
            const tr = document.createElement('tr');
            let statusClass = 'logs-status-failed';
            let statusText = log.status.toUpperCase();
            if (log.status === 'success') {
                statusClass = 'logs-status-success';
            } else if (log.status === 'running') {
                statusClass = 'logs-status-running';
                statusText = '<i class="fa-solid fa-spinner fa-spin"></i> RUNNING';
            }
            
            tr.innerHTML = `
                <td>${formatLogTime(log.timestamp)}</td>
                <td class="${statusClass}">${statusText}</td>
                <td>${log.jobs_found}</td>
                <td>${log.new_jobs}</td>
                <td style="max-width:220px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;" title="${escapeHTML(log.error_message || '')}">
                    ${escapeHTML(log.error_message || (log.status === 'running' ? 'Active scraping in background...' : 'Completed cleanly'))}
                </td>
            `;
            tbody.appendChild(tr);
        });
    }
}

// --- Utilities ---
function escapeHTML(str) {
    if (!str) return '';
    return str.replace(/[&<>'"]/g, 
        tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
    );
}

function formatDate(dateStr) {
    if (!dateStr) return '';
    try {
        const d = new Date(dateStr);
        if (isNaN(d.getTime())) return dateStr;
        return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
    } catch(e) {
        return dateStr;
    }
}

function formatLogTime(timeStr) {
    if (!timeStr) return '-';
    try {
        const d = new Date(timeStr);
        if (isNaN(d.getTime())) return timeStr;
        return d.toLocaleString('en-US', { timeZone: 'America/New_York', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', timeZoneName: 'short' });
    } catch(e) {
        return timeStr;
    }
}

// --- Structured details view helper ---
function renderStructuredJobDetails(job) {
    if (!job.structured_data) return '';
    try {
        const sd = JSON.parse(job.structured_data);
        
        let techHtml = '';
        if (sd.tech_stack && sd.tech_stack.length > 0) {
            techHtml = `
            <div style="margin-top: 10px; margin-bottom: 20px;">
                ${sd.tech_stack.map(t => `<span class="tech-badge">${escapeHTML(t)}</span>`).join('')}
            </div>`;
        }
        
        return `
        <div class="details-section">
            <h3 class="section-title">Role Overview</h3>
            <div class="alignment-text" style="margin-bottom: 20px; font-size:13px; line-height:1.6;">
                ${escapeHTML(sd.role_overview || 'No overview summary available.')}
            </div>
            
            ${techHtml ? `
            <h3 class="section-title">Required Technologies</h3>
            ${techHtml}
            ` : ''}
            
            ${sd.responsibilities && sd.responsibilities.length > 0 ? `
            <h3 class="section-title">Core Responsibilities</h3>
            <ul class="structured-bullet-list" style="margin-bottom: 20px;">
                ${sd.responsibilities.map(r => `<li>${escapeHTML(r)}</li>`).join('')}
            </ul>
            ` : ''}
            
            ${sd.qualifications && sd.qualifications.length > 0 ? `
            <h3 class="section-title">Required Qualifications</h3>
            <ul class="structured-bullet-list" style="margin-bottom: 20px;">
                ${sd.qualifications.map(q => `<li>${escapeHTML(q)}</li>`).join('')}
            </ul>
            ` : ''}
            
            ${sd.benefits && sd.benefits.length > 0 ? `
            <h3 class="section-title">Benefits & Perks</h3>
            <ul class="structured-bullet-list" style="margin-bottom: 10px;">
                ${sd.benefits.map(b => `<li>${escapeHTML(b)}</li>`).join('')}
            </ul>
            ` : ''}
        </div>
        `;
    } catch(e) {
        console.error("Error rendering structured data:", e);
        return '';
    }
}


// --- Helper functions for Navigation & New features ---

async function fetchInterestedJobs() {
    const res = await apiRequest('/api/jobs?is_interested=true');
    if (res) {
        state.interestedJobs = res;
        const countEl = document.getElementById('interested-results-count');
        if (countEl) {
            countEl.textContent = `${res.length} interested roles saved`;
        }
        if (state.activePanel === 'panel-interested') {
            filterAndRenderJobs();
        }
    }
}

async function toggleInterestedJob(job, starBtn) {
    const isStarred = state.interestedJobs.some(j => j.id === job.id);
    starBtn.disabled = true;
    try {
        if (isStarred) {
            const res = await apiRequest(`/api/jobs/interested/${job.id}`, 'DELETE');
            if (res) {
                state.interestedJobs = state.interestedJobs.filter(j => j.id !== job.id);
                showToast("Job removed from Interested list.");
                
                // Toggle classes
                starBtn.classList.remove('starred');
                const icon = starBtn.querySelector('i');
                if (icon) icon.className = 'fa-regular fa-star';
            }
        } else {
            const res = await apiRequest('/api/jobs/interested', 'POST', job);
            if (res) {
                state.interestedJobs.push(job);
                showToast("Job saved to Interested list.");
                
                // Toggle classes
                starBtn.classList.add('starred');
                const icon = starBtn.querySelector('i');
                if (icon) icon.className = 'fa-solid fa-star';
            }
        }
        
        // Sync star buttons across UI
        document.querySelectorAll(`.job-card[data-id="${job.id}"] .btn-star-job`).forEach(btn => {
            const starred = state.interestedJobs.some(j => j.id === job.id);
            if (starred) {
                btn.classList.add('starred');
                btn.querySelector('i').className = 'fa-solid fa-star';
            } else {
                btn.classList.remove('starred');
                btn.querySelector('i').className = 'fa-regular fa-star';
            }
        });
        
        const detailsStar = document.querySelector(`.tab-panel.active .btn-star-details`);
        if (detailsStar && state.selectedJobId === job.id) {
            const starred = state.interestedJobs.some(j => j.id === job.id);
            if (starred) {
                detailsStar.classList.add('starred');
                detailsStar.querySelector('i').className = 'fa-solid fa-star';
            } else {
                detailsStar.classList.remove('starred');
                detailsStar.querySelector('i').className = 'fa-regular fa-star';
            }
        }
        
        // Update tab views
        const interestedCount = document.getElementById('interested-results-count');
        if (interestedCount) {
            interestedCount.textContent = `${state.interestedJobs.length} interested roles saved`;
        }
        if (state.activePanel === 'panel-interested') {
            filterAndRenderJobs();
        }
    } finally {
        starBtn.disabled = false;
    }
}

function renderInternshipJobs() {
    const slider = document.getElementById('intern-score-slider');
    const minScore = slider ? parseInt(slider.value) : 0;
    const remoteTypes = Array.from(document.querySelectorAll('#panel-internship input[name="intern-remote-filter"]:checked')).map(c => c.value);
    
    const searchInput = document.getElementById('internship-search-input');
    const searchVal = searchInput ? searchInput.value.trim().toLowerCase() : '';
    
    // Check if the search term is a specific search (not empty and not the placeholder word 'internship')
    const isSpecificSearch = searchVal && searchVal !== 'internship';
    
    let filtered = state.internshipJobs.filter(job => {
        if ((job.score || 0) < minScore) return false;
        if (remoteTypes.length > 0) {
            const jobRemote = job.remote_type || 'remote';
            if (!remoteTypes.includes(jobRemote)) return false;
        }
        
        // When searching with specific, look for specific title
        if (isSpecificSearch) {
            const titleLower = (job.title || '').toLowerCase();
            if (!titleLower.includes(searchVal)) return false;
        }
        
        return true;
    });
    
    // If not a specific search, show only the top 30 list
    if (!isSpecificSearch) {
        filtered = filtered.slice(0, 30);
    }
    
    const countEl = document.getElementById('internship-results-count');
    if (countEl) {
        countEl.textContent = `${filtered.length} internships matching`;
    }
    
    renderJobList(filtered);
}

function populateInterviewJobSelector() {
    const select = document.getElementById('interview-job-select');
    if (!select) return;
    select.innerHTML = '<option value="">-- Choose a job from list or paste custom --</option>';
    
    const allJobs = [];
    const ids = new Set();
    const lists = [state.interestedJobs, state.jobs, state.internshipJobs];
    lists.forEach(list => {
        if (list) {
            list.forEach(job => {
                if (!ids.has(job.id)) {
                    ids.add(job.id);
                    allJobs.push(job);
                }
            });
        }
    });
    
    allJobs.forEach(job => {
        const opt = document.createElement('option');
        opt.value = job.id;
        opt.textContent = `${job.title} at ${job.company || 'Unknown'}`;
        select.appendChild(opt);
    });
    
    // Setup listener to toggle custom row
    const customRow = document.getElementById('custom-interview-job-row');
    if (customRow) {
        select.addEventListener('change', () => {
            if (select.value) {
                customRow.style.display = 'none';
            } else {
                customRow.style.display = 'block';
            }
        });
    }
}

function populateResumeJobSelector() {
    const select = document.getElementById('resume-job-select');
    if (!select) return;
    select.innerHTML = '<option value="">-- Choose a job from list or paste custom --</option>';
    
    const allJobs = [];
    const ids = new Set();
    const lists = [state.interestedJobs, state.jobs, state.internshipJobs];
    lists.forEach(list => {
        if (list) {
            list.forEach(job => {
                if (!ids.has(job.id)) {
                    ids.add(job.id);
                    allJobs.push(job);
                }
            });
        }
    });
    
    allJobs.forEach(job => {
        const opt = document.createElement('option');
        opt.value = job.id;
        opt.textContent = `${job.title} at ${job.company || 'Unknown'}`;
        select.appendChild(opt);
    });
    
    // Setup listener to toggle custom row
    const customRow = document.getElementById('custom-resume-job-row');
    if (customRow) {
        select.addEventListener('change', () => {
            if (select.value) {
                customRow.style.display = 'none';
            } else {
                customRow.style.display = 'block';
            }
        });
    }
    
    // Also auto fill candidate history if empty
    const baseExp = document.getElementById('resume-base-experience');
    if (baseExp && !baseExp.value) {
        baseExp.value = state.settings.resume_text || '';
    }
}

let speechRecognition = null;
let isListening = false;
let speechTranscript = '';

// Initialize browser native Speech Recognition
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
if (SpeechRecognition) {
    speechRecognition = new SpeechRecognition();
    speechRecognition.continuous = false;
    speechRecognition.interimResults = false;
    speechRecognition.lang = 'en-US';
    
    speechRecognition.onstart = () => {
        isListening = true;
        const micBtn = document.getElementById('btn-mic-interview');
        if (micBtn) {
            micBtn.innerHTML = '<i class="fa-solid fa-microphone-lines"></i>';
            micBtn.classList.add('mic-pulsing');
        }
        showToast("Listening... speak your answer.", 2000);
    };
    
    speechRecognition.onresult = (event) => {
        const text = event.results[0][0].transcript;
        const chatInput = document.getElementById('chat-message-input');
        if (chatInput) {
            chatInput.value = text;
        }
        speechTranscript = text;
    };
    
    speechRecognition.onerror = (event) => {
        console.error("Speech recognition error:", event.error);
        isListening = false;
        const micBtn = document.getElementById('btn-mic-interview');
        if (micBtn) {
            micBtn.innerHTML = '<i class="fa-solid fa-microphone"></i>';
            micBtn.classList.remove('mic-pulsing');
        }
    };
    
    speechRecognition.onend = () => {
        isListening = false;
        const micBtn = document.getElementById('btn-mic-interview');
        if (micBtn) {
            micBtn.innerHTML = '<i class="fa-solid fa-microphone"></i>';
            micBtn.classList.remove('mic-pulsing');
        }
        
        // Auto-submit in voice mode if we transcribed something non-empty
        const voiceCheckbox = document.getElementById('interview-voice-mode');
        if (voiceCheckbox && voiceCheckbox.checked && speechTranscript.trim()) {
            speechTranscript = ''; // Reset
            sendChatMessage();
        }
    };
}

function speakText(text) {
    const voiceCheckbox = document.getElementById('interview-voice-mode');
    if (!voiceCheckbox || !voiceCheckbox.checked) return;
    
    if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel(); // Stop any previous speech
        
        // Clean up text for nicer pronunciation (e.g. remove markdown, bullets, formatting, score annotations)
        const cleanText = text.replace(/[*#`_-]/g, '').replace(/(\d+)\s*\/\s*100/g, '$1 out of 100');
        
        const utterance = new SpeechSynthesisUtterance(cleanText);
        
        // Try to select a nice English voice
        const voices = window.speechSynthesis.getVoices();
        const preferredVoice = voices.find(v => v.lang.startsWith('en') && (v.name.includes('Google') || v.name.includes('Natural') || v.name.includes('Microsoft')));
        if (preferredVoice) {
            utterance.voice = preferredVoice;
        }
        
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        
        // Automatically start listening (Speech-to-Text) when the assistant finishes speaking!
        utterance.onend = () => {
            const isDone = interviewHistory.length > 0 && interviewHistory[interviewHistory.length - 1].content && interviewHistory[interviewHistory.length - 1].content.includes("Interview complete!");
            if (!isDone && speechRecognition && !isListening) {
                speechTranscript = '';
                speechRecognition.start();
            }
        };
        
        window.speechSynthesis.speak(utterance);
    }
}

function updateInterviewAssistantSubtitle() {
    const subtitle = document.getElementById('interview-ai-subtitle');
    if (!subtitle) return;
    
    const providersStr = state.settings.ai_provider || "AI";
    const firstProvider = providersStr.split(',')[0].trim();
    let providerDisplay = firstProvider.charAt(0).toUpperCase() + firstProvider.slice(1);
    if (providerDisplay.toLowerCase() === "openai") {
        providerDisplay = "ChatGPT";
    }
    subtitle.textContent = `${providerDisplay} Powered Technical Recruiter`;
}

let interviewHistory = [];
let selectedInterviewJob = null;

async function startInterviewSession() {
    const select = document.getElementById('interview-job-select');
    const customDesc = document.getElementById('interview-custom-desc');
    const startBtn = document.getElementById('btn-start-interview');
    const chatContainer = document.getElementById('chat-messages-container');
    const chatInput = document.getElementById('chat-message-input');
    const chatSendBtn = document.getElementById('btn-submit-chat-message');
    
    if (!select || !startBtn || !chatContainer) return;
    
    let title = "Custom Role";
    let company = "Custom Company";
    let description = "";
    
    if (select.value) {
        const allJobs = [...state.interestedJobs, ...state.jobs, ...state.internshipJobs];
        selectedInterviewJob = allJobs.find(j => j.id === select.value);
        if (!selectedInterviewJob) {
            showToast("Job details not found.");
            return;
        }
        title = selectedInterviewJob.title;
        company = selectedInterviewJob.company || 'Company';
        description = selectedInterviewJob.description || '';
    } else {
        description = customDesc ? customDesc.value.trim() : "";
        if (!description) {
            showToast("Please enter a custom job description or select a saved position.");
            return;
        }
        selectedInterviewJob = { title, company, description };
    }
    
    startBtn.disabled = true;
    startBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Loading...';
    
    chatContainer.innerHTML = '';
    interviewHistory = [];
    
    // Hide scorecard if visible
    const scoreCard = document.getElementById('interview-performance-card');
    if (scoreCard) scoreCard.style.display = 'none';
    
    const indicator = appendTypingIndicator(chatContainer);
    
    const res = await apiRequest('/api/jobs/ai/interview-chat', 'POST', {
        title,
        company,
        description,
        conversation_history: interviewHistory
    });
    
    removeTypingIndicator(indicator);
    startBtn.disabled = false;
    startBtn.innerHTML = '<i class="fa-solid fa-play"></i> Start AI Interview Session';
    
    if (res) {
        if (chatInput) chatInput.disabled = false;
        if (chatSendBtn) chatSendBtn.disabled = false;
        const micBtn = document.getElementById('btn-mic-interview');
        if (micBtn) micBtn.disabled = false;
        
        appendChatMessage('assistant', res.message);
        interviewHistory.push({ role: 'assistant', content: res.message });
        speakText(res.message);
    }
}

async function sendChatMessage() {
    const input = document.getElementById('chat-message-input');
    const chatContainer = document.getElementById('chat-messages-container');
    const chatSendBtn = document.getElementById('btn-submit-chat-message');
    const micBtn = document.getElementById('btn-mic-interview');
    
    if (!input || !chatContainer || !selectedInterviewJob) return;
    
    const msg = input.value.trim();
    if (!msg) return;
    
    input.value = '';
    input.disabled = true;
    if (chatSendBtn) chatSendBtn.disabled = true;
    if (micBtn) micBtn.disabled = true;
    
    appendChatMessage('user', msg);
    interviewHistory.push({ role: 'user', content: msg });
    
    const indicator = appendTypingIndicator(chatContainer);
    
    const res = await apiRequest('/api/jobs/ai/interview-chat', 'POST', {
        title: selectedInterviewJob.title,
        company: selectedInterviewJob.company || 'Company',
        description: selectedInterviewJob.description || '',
        conversation_history: interviewHistory
    });
    
    removeTypingIndicator(indicator);
    
    if (res) {
        appendChatMessage('assistant', res.message);
        interviewHistory.push({ role: 'assistant', content: res.message });
        speakText(res.message);
        
        if (res.is_done) {
            input.disabled = true;
            if (chatSendBtn) chatSendBtn.disabled = true;
            if (micBtn) micBtn.disabled = true;
            showToast("Interview complete!");
            
            // Display scorecard if available
            if (res.summary) {
                const scoreCard = document.getElementById('interview-performance-card');
                const scoreVal = document.getElementById('performance-score-val');
                if (scoreCard && scoreVal) {
                    scoreCard.style.display = 'block';
                    const scoreMatch = res.summary.feedback.match(/(\d+)\s*\/\s*100/);
                    if (scoreMatch) {
                        scoreVal.textContent = `${scoreMatch[1]}/100`;
                    } else {
                        scoreVal.textContent = "Complete";
                    }
                }
            }
        } else {
            input.disabled = false;
            if (chatSendBtn) chatSendBtn.disabled = false;
            if (micBtn) micBtn.disabled = false;
            input.focus();
        }
    } else {
        input.disabled = false;
        if (chatSendBtn) chatSendBtn.disabled = false;
        if (micBtn) micBtn.disabled = false;
    }
}

function appendChatMessage(role, text) {
    const chatContainer = document.getElementById('chat-messages-container');
    if (!chatContainer) return;
    
    // Clear initial greeting / empty state if it's the first message
    const emptyState = chatContainer.querySelector('.chat-empty-state');
    if (emptyState) {
        emptyState.remove();
    }
    
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${role === 'user' ? 'bubble-user' : 'bubble-assistant'}`;
    
    const formattedText = escapeHTML(text).replace(/\n/g, '<br>');
    
    bubble.innerHTML = `
        <div class="bubble-header">${role === 'user' ? 'You' : 'Interviewer'}</div>
        <div class="bubble-content">${formattedText}</div>
    `;
    
    chatContainer.appendChild(bubble);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function appendTypingIndicator(container) {
    // Clear initial greeting / empty state if it's the first message
    const emptyState = container.querySelector('.chat-empty-state');
    if (emptyState) {
        emptyState.remove();
    }
    
    const ind = document.createElement('div');
    ind.className = 'chat-bubble bubble-assistant typing-indicator-bubble';
    ind.innerHTML = `
        <div class="bubble-header">Interviewer</div>
        <div class="typing-indicator">
            <span></span><span></span><span></span>
        </div>
    `;
    container.appendChild(ind);
    container.scrollTop = container.scrollHeight;
    return ind;
}

function removeTypingIndicator(ind) {
    if (ind && ind.parentNode) {
        ind.parentNode.removeChild(ind);
    }
}

async function generateTailoredResume() {
    const select = document.getElementById('resume-job-select');
    const customDesc = document.getElementById('resume-custom-desc');
    const baseExp = document.getElementById('resume-base-experience');
    const buildBtn = document.getElementById('btn-build-resume');
    const emptyMsg = document.getElementById('resume-empty-message');
    const outputPaper = document.getElementById('resume-output-content');
    const copyBtn = document.getElementById('btn-copy-tailored-resume');
    const downloadBtn = document.getElementById('btn-download-tailored-resume');
    
    if (!baseExp || !buildBtn || !emptyMsg || !outputPaper) return;
    
    const experience = baseExp.value.trim();
    if (!experience) {
        showToast("Please enter your base profile experience text on the left first.");
        return;
    }
    
    let title = "Custom Role";
    let company = "Custom Company";
    let description = "";
    
    if (select.value) {
        const allJobs = [...state.interestedJobs, ...state.jobs, ...state.internshipJobs];
        const selectedJob = allJobs.find(j => j.id === select.value);
        if (!selectedJob) {
            showToast("Job details not found.");
            return;
        }
        title = selectedJob.title;
        company = selectedJob.company || 'Company';
        description = selectedJob.description || '';
    } else {
        description = customDesc ? customDesc.value.trim() : "";
        if (!description) {
            showToast("Please enter a custom job description or select a saved position.");
            return;
        }
    }
    
    buildBtn.disabled = true;
    buildBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Generating tailored draft...';
    
    const res = await apiRequest('/api/jobs/ai/build-resume', 'POST', {
        title,
        company,
        description,
        user_experience: experience
    });
    
    buildBtn.disabled = false;
    buildBtn.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Generate Tailored Resume';
    
    if (res && res.resume_text) {
        emptyMsg.style.display = 'none';
        outputPaper.style.display = 'block';
        
        outputPaper.style.whiteSpace = 'pre-wrap';
        outputPaper.textContent = res.resume_text;
        
        if (copyBtn) copyBtn.disabled = false;
        if (downloadBtn) downloadBtn.disabled = false;
        
        showToast("Resume tailored successfully!");
    }
}

// --- Captcha and MFA Helpers ---
function initSliderCaptcha(trackId, handleId, labelId, submitBtnId, onVerify) {
    const track = document.getElementById(trackId);
    const handle = document.getElementById(handleId);
    const label = document.getElementById(labelId);
    const submitBtn = document.getElementById(submitBtnId);
    if (!track || !handle || !label || !submitBtn) return;

    let isDragging = false;
    let startX = 0;
    let currentLeft = 0;
    let isVerified = false;

    // Reset slider
    const resetSlider = () => {
        isDragging = false;
        currentLeft = 0;
        isVerified = false;
        handle.style.left = '1px';
        track.classList.remove('verified');
        label.innerHTML = 'Slide to Verify';
        label.style.opacity = '1';
        submitBtn.style.display = 'none';
        submitBtn.disabled = true;
    };

    handle.addEventListener('mousedown', startDrag);
    handle.addEventListener('touchstart', startDrag, { passive: true });

    function startDrag(e) {
        if (isVerified) return;
        isDragging = true;
        startX = e.type === 'touchstart' ? e.touches[0].clientX : e.clientX;
        handle.style.transition = 'none';
        document.addEventListener('mousemove', drag);
        document.addEventListener('mouseup', stopDrag);
        document.addEventListener('touchmove', drag, { passive: false });
        document.addEventListener('touchend', stopDrag);
    }

    function drag(e) {
        if (!isDragging || isVerified) return;
        if (e.type === 'touchmove') e.preventDefault(); // prevent scrolling while dragging

        const clientX = e.type === 'touchmove' ? e.touches[0].clientX : e.clientX;
        const deltaX = clientX - startX;
        const maxDelta = track.clientWidth - handle.clientWidth - 2;
        let newLeft = currentLeft + deltaX;

        if (newLeft < 1) newLeft = 1;
        if (newLeft > maxDelta) newLeft = maxDelta;

        handle.style.left = newLeft + 'px';

        // Fade out label as we slide
        const progress = newLeft / maxDelta;
        label.style.opacity = Math.max(0, 1 - progress * 1.5).toString();

        // Check verification threshold
        if (newLeft >= maxDelta - 2) {
            isVerified = true;
            isDragging = false;
            handle.style.transition = 'all 0.2s ease';
            handle.style.left = maxDelta + 'px';
            track.classList.add('verified');
            label.innerHTML = '<i class="fa-solid fa-circle-check"></i> Verification Complete';
            label.style.opacity = '1';
            
            // Show submit button, hide proceed button, etc.
            if (onVerify) onVerify();
            
            document.removeEventListener('mousemove', drag);
            document.removeEventListener('mouseup', stopDrag);
            document.removeEventListener('touchmove', drag);
            document.removeEventListener('touchend', stopDrag);
        }
    }

    function stopDrag(e) {
        if (!isDragging || isVerified) return;
        isDragging = false;
        handle.style.transition = 'left 0.2s ease-out';
        handle.style.left = '1px';
        label.style.opacity = '1';
        document.removeEventListener('mousemove', drag);
        document.removeEventListener('mouseup', stopDrag);
        document.removeEventListener('touchmove', drag);
        document.removeEventListener('touchend', stopDrag);
    }

    track.reset = resetSlider;
}

function setupOtpInputTabbing() {
    const inputs = document.querySelectorAll('.otp-digit-input');
    inputs.forEach((input, index) => {
        input.addEventListener('input', (e) => {
            // Allow only numbers
            input.value = input.value.replace(/[^0-9]/g, '');
            if (input.value.length === 1 && index < inputs.length - 1) {
                inputs[index + 1].focus();
            }
            // Auto submit removed
        });

        input.addEventListener('keydown', (e) => {
            if (e.key === 'Backspace') {
                if (input.value === '' && index > 0) {
                    inputs[index - 1].value = '';
                    inputs[index - 1].focus();
                } else {
                    input.value = '';
                }
            }
        });

        input.addEventListener('paste', (e) => {
            e.preventDefault();
            const pasteData = e.clipboardData.getData('text').replace(/[^0-9]/g, '').slice(0, 6);
            if (pasteData.length > 0) {
                for (let i = 0; i < inputs.length; i++) {
                    if (pasteData[i]) {
                        inputs[i].value = pasteData[i];
                    }
                }
                const lastIndex = Math.min(pasteData.length - 1, inputs.length - 1);
                inputs[lastIndex].focus();
                
                // Auto submit removed
            }
        });
    });
}

let mfaCountdownInterval = null;
function startMfaCountdown() {
    if (mfaCountdownInterval) clearInterval(mfaCountdownInterval);
    const countdownEl = document.getElementById('mfa-timer-countdown');
    if (!countdownEl) return;
    
    let totalSeconds = 10 * 60; // 10 minutes
    countdownEl.textContent = "10:00";
    
    mfaCountdownInterval = setInterval(() => {
        totalSeconds--;
        if (totalSeconds <= 0) {
            clearInterval(mfaCountdownInterval);
            countdownEl.textContent = "00:00";
            showToast("MFA verification code has expired. Please go back and request a new one.");
            return;
        }
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;
        countdownEl.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }, 1000);
}

function stopMfaCountdown() {
    if (mfaCountdownInterval) {
        clearInterval(mfaCountdownInterval);
        mfaCountdownInterval = null;
    }
}

window.handleAutoApplyClick = function(jobId) {
    const container = document.getElementById("auto-apply-status-container");
    const log = document.getElementById("auto-apply-status-log");
    const tag = document.getElementById("auto-apply-status-tag");
    const actions = document.getElementById("auto-apply-status-actions");
    const header = document.getElementById("auto-apply-status-header");
    
    if (!container || !log || !tag || !actions || !header) return;
    
    container.style.display = "block";
    header.innerHTML = `<i class="fa-solid fa-sliders"></i> Select Apply Mode:`;
    tag.textContent = "pending";
    tag.style.background = "#ffd700";
    tag.style.color = "#333";
    
    log.textContent = "Configure your candidate details under the 'Profile & CV' settings tab first.\n\nChoose an application mode to proceed:\n\n- Preview Mode: Launches a visible browser window, fills form fields & uploads your resume, then pauses for 5 minutes so you can review and click submit manually.\n\n- Fully Auto: Runs a headless browser in the background and automatically submits the application.";
    
    actions.innerHTML = `
        <button class="btn btn-secondary" style="font-size: 11px; padding: 4px 8px;" onclick="window.startAutoApply('${jobId}', 'preview')">Preview Mode</button>
        <button class="btn btn-primary" style="font-size: 11px; padding: 4px 8px;" onclick="window.startAutoApply('${jobId}', 'auto')">Fully Auto</button>
        <button class="btn btn-secondary" style="font-size: 11px; padding: 4px 8px; background: transparent; border: 1px solid var(--border-color);" onclick="window.cancelAutoApply()">Cancel</button>
    `;
};

window.cancelAutoApply = function() {
    const container = document.getElementById("auto-apply-status-container");
    if (container) container.style.display = "none";
};

window.startAutoApply = async function(jobId, mode) {
    const log = document.getElementById("auto-apply-status-log");
    const tag = document.getElementById("auto-apply-status-tag");
    const actions = document.getElementById("auto-apply-status-actions");
    const header = document.getElementById("auto-apply-status-header");
    
    if (!log || !tag || !actions || !header) return;
    
    header.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Auto-Apply Status:`;
    tag.textContent = "running";
    tag.style.background = "#8a2be2";
    tag.style.color = "white";
    
    log.textContent = `Initializing browser automation agent in ${mode} mode...\nLoading candidate profile details...\n`;
    actions.innerHTML = "";
    
    try {
        const token = localStorage.getItem("token") || "";
        const profileId = localStorage.getItem("activeProfileId") || "default";
        
        const response = await fetch(`/api/jobs/${jobId}/apply`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`,
                "X-Profile-ID": profileId
            },
            body: JSON.stringify({ mode: mode })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            tag.textContent = "success";
            tag.style.background = "var(--success)";
            tag.style.color = "white";
            header.innerHTML = `<i class="fa-solid fa-check"></i> Auto-Apply Complete`;
            log.textContent += `\n[SUCCESS] ${data.message}\n`;
            
            if (mode === "preview") {
                log.textContent += `\nForm pre-filled successfully! Keep the browser window open and complete the submission manually. The browser will remain active for 5 minutes.`;
            } else {
                log.textContent += `\nApplication submitted automatically.`;
            }
            
            const pipelineSelect = document.getElementById("details-pipeline-select");
            if (pipelineSelect) {
                pipelineSelect.value = "applied";
                pipelineSelect.dispatchEvent(new Event('change'));
            }
            
            showToast("Auto-apply completed successfully!");
        } else {
            throw new Error(data.detail || "Server failed to execute auto-apply.");
        }
    } catch (err) {
        tag.textContent = "failed";
        tag.style.background = "var(--danger)";
        tag.style.color = "white";
        header.innerHTML = `<i class="fa-solid fa-circle-exclamation"></i> Auto-Apply Failed`;
        log.textContent += `\n[ERROR] ${err.message}\n`;
        showToast("Auto-apply failed.", "error");
    } finally {
        actions.innerHTML = `
            <button class="btn btn-secondary" style="font-size: 11px; padding: 4px 8px; background: transparent; border: 1px solid var(--border-color);" onclick="window.cancelAutoApply()">Close</button>
        `;
    }
};


// --- Market Analyst Insights Logic ---
let marketInsightsLoaded = false;

async function fetchMarketInsights() {
    const loadingDiv = document.getElementById('market-loading');
    const dashboardDiv = document.getElementById('market-dashboard');
    
    loadingDiv.style.display = 'flex';
    dashboardDiv.style.display = 'none';
    
    try {
        const response = await fetch('/api/market-insights', {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('sessionToken')}` }
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
