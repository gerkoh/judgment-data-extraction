import requests
from bs4 import BeautifulSoup
import html2text
import json
import os
from urllib.parse import urljoin, urlparse

def is_valid_case_url(url):
    # Check if the URL is a case URL based on the pattern
    return "elitigation.sg/gd/s/" in url

def extract_cases_from_page(url, output_directory, visited_urls=set()):
    try:
        # Check if the URL has already been visited to avoid duplicate scraping
        if url in visited_urls:
            return
        visited_urls.add(url)

        # Send an HTTP GET request to the URL
        response = requests.get(url)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the HTML content of the page using BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find all links on the page
            for link in soup.find_all('a', href=True):
                next_url = urljoin(url, link['href'])

                # Check if the link is a valid case URL
                if is_valid_case_url(next_url):
                    extract_case_content(next_url, output_directory, visited_urls)

        else:
            print(f"Failed to fetch the web page '{url}'. Status code: {response.status_code}")

    except Exception as e:
        print(f"An error occurred: {str(e)}")

def extract_case_content(case_url, output_directory, visited_urls=set()):
    try:
        # Check if the case URL has already been visited to avoid duplicate scraping
        if case_url in visited_urls:
            return
        visited_urls.add(case_url)

        # Send an HTTP GET request to the case URL
        response = requests.get(case_url)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the HTML content of the case page using BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')

            # Initialize the HTML to text converter
            h = html2text.HTML2Text()

            # Remove HTML tags and convert to plain text
            plain_text = h.handle(str(soup))

            # Construct the full output file path for the case content
            case_output_file = os.path.join(output_directory, f'{get_case_id(case_url)}.md')

            # Write the extracted text to a markdown file
            with open(case_output_file, 'w', encoding='utf-8') as file:
                file.write(plain_text)

            print(f"Content from case '{case_url}' extracted and saved to '{case_output_file}'")

        else:
            print(f"Failed to fetch the case page '{case_url}'. Status code: {response.status_code}")

    except Exception as e:
        print(f"An error occurred: {str(e)}")

def get_case_id(url):
    # Extract the case ID from the case URL
    # You may need to customize this function based on the actual URL structure
    return url.split('/')[-1]

# Function to get the next page URL
def get_next_page_url(base_url, current_page, search_phrase):
    return f"{base_url}Index?Filter=SUPCT&YearOfDecision=All&SortBy=Score&SearchPhrase={search_phrase}&CurrentPage={current_page}&SortAscending=False&PageSize=0&Verbose=False&SearchQueryTime=0&SearchTotalHits=0&SearchMode=False&SpanMultiplePages=False"


# change the correct directory
source_directory = 'judgments'  # Replace with the actual directory path
base_url = 'https://www.elitigation.sg/gd/Home/'  # Replace with the base URL
search_phrase = '%22division%20of%20matrimonial%20assets%22'

# Start crawling from page 1
current_page = 1
max_pages = 999  # Set the maximum number of pages to crawl (arbitrary number, can be 9999, crawler will stop at last page)

while current_page <= max_pages:
    current_url = get_next_page_url(base_url, current_page, search_phrase)
    extract_cases_from_page(current_url, source_directory)
    current_page += 1
