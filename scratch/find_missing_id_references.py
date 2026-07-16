with open('c:/Users/skris/OneDrive/Desktop/JobSeeker/frontend/app.js', 'r', encoding='utf-8') as f:
    js_content = f.read()

missing_ids = [
    'active-profile-avatar-circle', 'active-profile-name-text', 
    'btn-generate-interview', 'btn-generate-outreach', 'btn-generate-tailoring', 
    'btn-manage-profiles', 'btn-settings', 'create-profile-modal', 
    'details-pipeline-select', 'interview-content-area', 'outreach-content-area', 
    'profile-dropdown-menu', 'profile-grid-container', 'profile-name-input', 
    'profile-selection-overlay', 'settings-close', 'settings-modal', 'tailoring-content-area'
]

lines = js_content.splitlines()

print("--- References to missing elements in app.js ---")
for el_id in missing_ids:
    print(f"\nReferences to '{el_id}':")
    found = False
    for line_no, line in enumerate(lines, 1):
        if el_id in line:
            print(f"{line_no}: {line.strip()}")
            found = True
    if not found:
        print("(None)")
