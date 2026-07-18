import urllib.request
import re

req = urllib.request.Request('https://ieeexplore.ieee.org/document/9679614', headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
try:
    html = urllib.request.urlopen(req).read().decode('utf-8')
    title = re.search(r'"title":"(.*?)"', html)
    authors = re.search(r'"authors":\[(.*?)\]', html)
    year = re.search(r'"publicationYear":"(.*?)"', html)
    print("TITLE:", title.group(1) if title else "Not found")
    print("YEAR:", year.group(1) if year else "Not found")
except Exception as e:
    print("Error:", e)
