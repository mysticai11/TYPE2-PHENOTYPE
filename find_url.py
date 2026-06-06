import urllib.request
from bs4 import BeautifulSoup

def get_xpt_links(url):
    html = urllib.request.urlopen(url).read().decode('utf-8')
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.find_all('a', href=True):
        if a['href'].lower().endswith('.xpt'):
            links.append(a['href'])
    return links

print("DEMO:", get_xpt_links("https://wwwn.cdc.gov/nchs/nhanes/search/datapage.aspx?Component=Demographics&CycleBeginYear=2017"))
print("LAB:", get_xpt_links("https://wwwn.cdc.gov/nchs/nhanes/search/datapage.aspx?Component=Laboratory&CycleBeginYear=2017"))
print("EXAM:", get_xpt_links("https://wwwn.cdc.gov/nchs/nhanes/search/datapage.aspx?Component=Examination&CycleBeginYear=2017"))
