from bs4 import BeautifulSoup
import urllib.request

url = 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=Backend+Engineer&location=Bengaluru&start=0'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
html = urllib.request.urlopen(req).read()
soup = BeautifulSoup(html, 'html.parser')
cards = soup.find_all('li')
print(f"Found {len(cards)} LinkedIn live jobs for Bengaluru:")
for c in cards[:5]:
    t = c.find('h3', class_='base-search-card__title')
    comp = c.find('h4', class_='base-search-card__subtitle')
    loc = c.find('span', class_='job-search-card__location')
    link = c.find('a', class_='base-card__full-link')
    if t and comp:
        title = t.get_text(strip=True)
        company = comp.get_text(strip=True)
        place = loc.get_text(strip=True) if loc else ""
        href = link['href'] if link and 'href' in link.attrs else ""
        print(f"• {title} | {company} ({place})")
