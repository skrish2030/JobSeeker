import sqlite3

DEFAULT_DB_PATH = r"C:\Users\skris\OneDrive\Desktop\JobSeeker\jobs.db"

COMPANIES_TO_ADD = [
    "Continental Finance Company",
    "Continental Finance",
    "CFC",
    "Discover Financial Services",
    "Synchrony Financial",
    "Ally Financial",
    "Chime",
    "SoFi",
    "Plaid",
    "Stripe",
    "Square",
    "Block",
    "Affirm",
    "Klarna",
    "Afterpay",
    "Robinhood",
    "Coinbase",
    "Vanguard",
    "Fidelity Investments",
    "Charles Schwab",
    "E-Trade",
    "TD Ameritrade",
    "Interactive Brokers",
    "Capital One",
    "American Express",
    "JPMorgan Chase",
    "Bank of America",
    "Citigroup",
    "Wells Fargo",
    "Goldman Sachs",
    "Morgan Stanley",
    "U.S. Bancorp",
    "Truist",
    "PNC Financial Services",
    "TD Bank",
    "BNY Mellon",
    "State Street",
    "BlackRock",
    "AIG",
    "Prudential Financial",
    "MetLife",
    "New York Life",
    "MassMutual",
    "Northwestern Mutual",
    "State Farm",
    "Allstate",
    "Progressive",
    "Geico",
    "Liberty Mutual",
    "Travelers",
    "USAA",
    "Navy Federal Credit Union",
    "PenFed Credit Union",
    "KeyBank",
    "Citizens Financial Group",
    "Fifth Third Bank",
    "M&T Bank",
    "Regions Financial",
    "Huntington Bancshares",
    "Comerica",
    "First Horizon",
    "Zions Bancorporation",
    "Western Alliance Bancorporation",
    "Webster Financial",
    "Prosper Marketplace",
    "Upstart",
    "LendingClub",
    "Oportun",
    "Avant",
    "Enova",
    "Elevate",
    "OneMain Financial",
    "Springleaf",
    "Navient",
    "Sallie Mae",
    "Nelnet",
    "Credit Karma",
    "NerdWallet",
    "Experian",
    "Equifax",
    "TransUnion",
    "FICO",
    "Fair Isaac Corporation",
    "PayPal",
    "Venmo",
    "Zelle",
    "Early Warning Services"
]

def add_missing_companies():
    print(f"Connecting to {DEFAULT_DB_PATH}")
    conn = sqlite3.connect(DEFAULT_DB_PATH)
    c = conn.cursor()
    
    added_count = 0
    for company in COMPANIES_TO_ADD:
        c.execute("SELECT 1 FROM target_companies WHERE name = ?", (company,))
        if not c.fetchone():
            c.execute("INSERT INTO target_companies (name, portal_url) VALUES (?, ?)", (company, None))
            added_count += 1
            
    conn.commit()
    conn.close()
    print(f"Successfully added {added_count} missing companies to the target list.")

if __name__ == '__main__':
    add_missing_companies()
