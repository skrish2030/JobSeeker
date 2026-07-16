try:
    import selenium
    print("Selenium is installed")
except ImportError:
    print("Selenium is NOT installed")

try:
    import playwright
    print("Playwright is installed")
except ImportError:
    print("Playwright is NOT installed")
