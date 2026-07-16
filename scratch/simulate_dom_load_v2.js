const fs = require('fs');

// Mock browser global environment
global.window = global;

const baseElement = {
    addEventListener: (ev, cb) => {},
    style: {},
    classList: {
        add: (cls) => {},
        remove: (cls) => {},
        toggle: (cls) => {}
    },
    value: '',
    textContent: '',
    innerHTML: '',
    appendChild: (el) => {},
    querySelector: (sel) => {
        return Object.create(baseElement);
    },
    querySelectorAll: (sel) => {
        return [Object.create(baseElement)];
    }
};

global.localStorage = {
    getItem: (key) => {
        console.log(`[LocalStorage] getItem(${key})`);
        if (key === 'sessionToken') return 'mock-token';
        if (key === 'username') return 'saikrishna';
        return null;
    },
    setItem: (key, val) => console.log(`[LocalStorage] setItem(${key}, ${val})`),
    removeItem: (key) => console.log(`[LocalStorage] removeItem(${key})`)
};

global.navigator = {
    clipboard: {
        writeText: (txt) => console.log(`[Clipboard] writeText(${txt})`)
    }
};

const elements = {};
const ids_to_mock = [
    'job-list-container', 'details-panel-container', 'header-search-input', 
    'header-location-input', 'btn-find-jobs', 'score-slider', 'score-val', 
    'feed-results-count', 'settings-modal', 'btn-settings', 'settings-close', 
    'settings-cancel', 'settings-save', 'btn-email-now', 'btn-test-smtp', 
    'btn-add-company', 'company-add-input', 'companies-tags-container', 
    'company-url-input', 'sidebar-username', 'auth-overlay', 
    'login-captcha-track', 'login-captcha-handle', 'login-captcha-label', 
    'btn-submit-login', 'register-captcha-track', 'register-captcha-handle', 
    'register-captcha-label', 'btn-submit-register', 'btn-login-proceed', 
    'btn-register-proceed', 'tab-login-btn', 'tab-register-btn', 
    'login-form-panel', 'register-form-panel', 'mfa-form-panel', 
    'btn-submit-mfa', 'btn-back-to-login', 'btn-logout', 'btn-start-interview', 
    'btn-submit-chat-message', 'chat-message-input', 'btn-build-resume', 
    'btn-copy-tailored-resume', 'btn-download-tailored-resume'
];

ids_to_mock.forEach(id => {
    elements[id] = Object.create(baseElement);
});

// Explicitly set null for elements missing in HTML to test if it crashes the app
const missing_in_html = [
    'settings-modal', 'settings-close', 'btn-settings',
    'btn-manage-profiles', 'create-profile-modal', 'profile-dropdown-menu',
    'profile-grid-container', 'profile-name-input', 'profile-selection-overlay'
];

missing_in_html.forEach(id => {
    elements[id] = null;
});

global.document = {
    getElementById: (id) => {
        // console.log(`[DOM] getElementById(${id})`);
        if (id in elements) return elements[id];
        const el = Object.create(baseElement);
        return el;
    },
    querySelectorAll: (selector) => {
        console.log(`[DOM] querySelectorAll(${selector})`);
        return {
            forEach: (cb) => {
                if (selector.includes('.nav-sidebar .nav-item')) {
                    cb({ getAttribute: () => 'panel-home', addEventListener: () => {} });
                }
                if (selector.includes('.main-content .tab-panel')) {
                    cb({ classList: { add: () => {}, remove: () => {} } });
                }
            }
        };
    },
    querySelector: (selector) => {
        console.log(`[DOM] querySelector(${selector})`);
        return Object.create(baseElement);
    },
    addEventListener: (event, callback) => {
        console.log(`[DOM] addEventListener(${event})`);
        if (event === 'DOMContentLoaded') {
            setTimeout(async () => {
                try {
                    console.log("\n--- Triggering DOMContentLoaded Callback ---");
                    await callback();
                    console.log("--- DOMContentLoaded Callback Completed Successfully ---");
                } catch (e) {
                    console.error("\n[CRASH] DOMContentLoaded Callback crashed with error:");
                    console.error(e);
                }
            }, 100);
        }
    }
};

// Mock fetch global
global.fetch = async (url, options) => {
    console.log(`[Fetch] ${options.method || 'GET'} ${url}`);
    if (url.includes('/api/settings')) {
        return {
            status: 200,
            ok: true,
            json: async () => ({ min_relevance_score: 50 })
        };
    }
    if (url.includes('/api/target-companies')) {
        return {
            status: 200,
            ok: true,
            json: async () => ([])
        };
    }
    if (url.includes('/api/jobs')) {
        return {
            status: 200,
            ok: true,
            json: async () => ([])
        };
    }
    return {
        status: 200,
        ok: true,
        json: async () => ({})
    };
};

console.log("Loading app.js...");
try {
    const js = fs.readFileSync('c:/Users/skris/OneDrive/Desktop/JobSeeker/frontend/app.js', 'utf-8');
    eval(js);
    console.log("app.js evaluated successfully.");
} catch (e) {
    console.error("[CRASH] Failed to evaluate app.js:");
    console.error(e);
}
