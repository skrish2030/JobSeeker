from bs4 import BeautifulSoup

with open('c:/Users/skris/OneDrive/Desktop/JobSeeker/frontend/index.html', 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f.read(), 'html.parser')

elements_to_check = {
    'job-list-container': 'id',
    'details-panel-container': 'id',
    'header-search-input': 'id',
    'header-location-input': 'id',
    'btn-find-jobs': 'id',
    'score-slider': 'id',
    'score-val': 'id',
    'feed-results-count': 'id',
    'settings-modal': 'id',
    'btn-settings': 'id',
    'settings-close': 'id',
    'settings-cancel': 'id',
    'settings-save': 'id',
    'tab-btn': 'class',
    'tab-content': 'class',
    'btn-email-now': 'id',
    'btn-test-smtp': 'id',
    'btn-add-company': 'id',
    'company-add-input': 'id',
    'companies-tags-container': 'id',
    'company-url-input': 'id'
}

print("--- Checking elements in index.html ---")
for el, type_ in elements_to_check.items():
    if type_ == 'id':
        found = soup.find(id=el) is not None
    else:
        found = soup.find(class_=el) is not None
    print(f"{type_.upper()} '{el}': {'FOUND' if found else 'NOT FOUND'}")
