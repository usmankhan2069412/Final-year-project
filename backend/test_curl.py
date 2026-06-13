from curl_cffi import requests
from bs4 import BeautifulSoup

url = 'https://iac.edu.pk/'

try:
    resp = requests.get(url, impersonate="chrome120", timeout=15.0)
    print(f'Status: {resp.status_code}')
    print(f'Length: {len(resp.text)}')
    
    soup = BeautifulSoup(resp.text, 'html.parser')
    links = soup.find_all('a')
    print(f'Links: {len(links)}')
    if len(links) > 0:
        print("SUCCESS! JavaScript challenge bypassed.")
    print(f'Preview:\n{resp.text[:500]}')
except Exception as e:
    print(f'Error: {e}')
