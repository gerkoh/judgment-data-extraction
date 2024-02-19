# Test file for automation

import requests
from bs4 import BeautifulSoup
import re

current_page = 1

target = "Surindar Singh s/o Jaswant Singh v Sita Jaswant Kaur"
found = False

ls_a_tags = []
ls_hrefs = []


i = 1

while found != True:
    response = requests.get(f"https://www.elitigation.sg/gd/Home/Index?filter=SUPCT&yearOfDecision=All&sortBy=Score&currentPage={current_page}&sortAscending=False&searchPhrase=%22division%20of%20matrimonial%20assets%22&verbose=False")
    soup = BeautifulSoup(response.text, 'html.parser')
    for a_tag in soup.find_all('a', href=True):
        if a_tag['href'].startswith('/gd/s/'):
            ls_hrefs.append(a_tag['href'])
            casename = a_tag.text.strip()
            print(f"{i}:" + casename)
            if casename.lower() == target.lower():
                found = True
                break
            ls_a_tags.append(casename)
    current_page += 1

print(len(ls_a_tags))
print(len(ls_hrefs))