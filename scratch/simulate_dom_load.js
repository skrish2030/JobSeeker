const fs = require('fs');

// Mock browser global environment
global.window = global;
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

const elements = {
    'job-list-container': {},
    'details-panel-container': {},
    'header-search-input': { value: '' },
    'header-location-input': { value: '' },
    'btn-find-jobs': { addEventListener: () => {} },
    'score-slider': { value: '50' },
    'score-val': { textContent: '50' },
    'feed-results-count': { textContent: '' },
    'settings-modal': null, // missing in HTML!
    'btn-settings': null, // missing in HTML!
    'settings-close': null, // missing in HTML!
    'settings-cancel': { addEventListener: () => {} },
    'settings-save': { addEventListener: () => {} },
    'btn-email-now': { addEventListener: () => {} },
    'btn-test-smtp': { addEventListener: () => {} },
    'btn-add-company': { addEventListener: () => {} },
    'company-add-input': { value: '' },
    'companies-tags-container': { appendChild: () => {} },
    'company-url-input': { value: '' },
    'sidebar-username': { textContent: '' },
    'auth-overlay': { style: {} },
    'login-captcha-track': {},
    'login-captcha-handle': { addEventListener: () => {} },
    'login-captcha-label': {},
    'btn-submit-login': { addEventListener: () => {} },
    'register-captcha-track': {},
    'register-captcha-handle': { addEventListener: () => {} },
    'register-captcha-label': {},
    'btn-submit-register': { addEventListener: () => {} },
    'btn-login-proceed': { addEventListener: () => {} },
    'btn-register-proceed': { addEventListener: () => {} },
    'tab-login-btn': { addEventListener: () => {} },
    'tab-register-btn': { addEventListener: () => {} },
    'login-form-panel': { classList: { add: () => {}, remove: () => {} } },
    'register-form-panel': { classList: { add: () => {}, remove: () => {} } },
    'mfa-form-panel': { classList: { add: () => {}, remove: () => {} } },
    'btn-submit-mfa': { addEventListener: () => {} },
    'btn-back-to-login': { addEventListener: () => {} },
    'btn-logout': { addEventListener: () => {} },
    'btn-start-interview': { addEventListener: () => {} },
    'btn-submit-chat-message': { addEventListener: () => {} },
    'chat-message-input': { addEventListener: () => {} },
    'btn-build-resume': { addEventListener: () => {} },
    'btn-copy-tailored-resume': { addEventListener: () => {} },
    'btn-download-tailored-resume': { addEventListener: () => {} }
};

global.document = {
    getElementById: (id) => {
        // console.log(`[DOM] getElementById(${id})`);
        if (id in elements) return elements[id];
        return { style: {}, addEventListener: () => {}, classList: { add: () => {}, remove: () => {} } };
    },
    querySelectorAll: (selector) => {
        console.log(`[DOM] querySelectorAll(${selector})`);
        return {
            forEach: (cb) => {
                // Return mock elements
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
        return { classList: { add: () => {}, remove: () => {} } };
    },
    addEventListener: (event, callback) => {
        console.log(`[DOM] addEventListener(${event})`);
        if (event === 'DOMContentLoaded') {
            // Run the DOMContentLoaded event callback immediately to trace execution
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
