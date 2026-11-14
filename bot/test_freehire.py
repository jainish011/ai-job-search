import urllib.request
import json

url = 'https://freehire.me/api/v1/jobs/search?q=backend&country=IN&limit=5'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req, timeout=10) as r:
        d = json.loads(r.read())
        results = d.get('results', [])
        print(f"Total Indian jobs returned by freehire: {len(results)}")
        for j in results[:3]:
            print(f"- {j.get('title')} at {j.get('company')} ({j.get('location')}) - {j.get('url')}")
except Exception as e:
    print('Error:', e)
