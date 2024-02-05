# Imports for scraper
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import requests

# Imports for secrets
import os
from dotenv import load_dotenv

# Import API keys
load_dotenv()
SCRAPEOPS_API_KEY = os.getenv('SCRAPEOPS')

# Search term
search_term = "division of matrimonial assets"

# Convert search term to be used in url
def convert_search_term(is_exact_match):
    if is_exact_match:
        converted_search_term = "%22" + search_term.replace(" ", "%20") + "%22"
    else:
        converted_search_term = search_term.replace(" ", "%20")
    return converted_search_term

converted_search_term = convert_search_term(is_exact_match=True)

url = f"https://www.elitigation.sg/gd/Home/Index?filter=SUPCT&yearOfDecision=All&sortBy=Score&currentPage=1&sortAscending=False&searchPhrase={converted_search_term}&verbose=False"

# Get random user agent from ScrapeOps API
def get_user_agent_with_api():
    response = requests.get(
        url='https://headers.scrapeops.io/v1/user-agents',
        params={
            'api_key': SCRAPEOPS_API_KEY,
            'num_results': '1'}
    )

    user_agent = response.json()["result"][0]
    return user_agent

user_agent = get_user_agent_with_api()

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument(f"--user-agent={user_agent}") # for spoofing user agent

# Create a Chrome web driver
driver = webdriver.Chrome(options=chrome_options)

driver.get(url)

# Check page source
# with open("output.html", "w") as file:
#     file.write(driver.page_source)

# Get total number of judgments found
total_judgments_class_name = "gd-csummary"
total_judgments = int(driver.find_element(By.CLASS_NAME, total_judgments_class_name).text.split(" ")[-1])