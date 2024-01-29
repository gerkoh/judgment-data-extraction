import requests
from bs4 import BeautifulSoup
import json
import os
from urllib.parse import urljoin
import re

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
                    case_to_json(next_url, output_directory)

        else:
            print(f"Failed to fetch the web page '{url}'. Status code: {response.status_code}")

    except Exception as e:
        print(f"An error occurred: {str(e)}")

#extract case name from html content
def extract_case_name(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    case_title_tag = soup.find('span', class_='caseTitle')
    if case_title_tag:
        case_title = ' '.join(case_title_tag.stripped_strings)
        return case_title
    return ""

#extract case citation from html content
def extract_citation(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    citation_tag = soup.find('span', class_='Citation offhyperlink')
    if citation_tag:
        citation = citation_tag.get_text(strip=True)
        return citation
    return ""

#extract case_number,decision_date from html content
def extract_case_info(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    case_info_table = soup.find('table', id='info-table')
    
    if case_info_table:
        case_info = {}
        rows = case_info_table.find_all('tr', class_='info-row')
        
        for row in rows:
            label = row.find('td', class_='txt-label')
            value = row.find('td', class_='txt-body')
            
            if label and value:
                case_info[label.get_text(strip=True)] = value.get_text(strip=True)

        # Extract Case Number and Decision Date
        case_number = case_info.get('Case Number', '')
        decision_date = case_info.get('Decision Date', '')
        
        return case_number, decision_date
    
    return '', ''

def extract_paragraphs(html_content, class_name):
    
    soup = BeautifulSoup(html_content, 'html.parser')
    paragraphs = []

    # Find all paragraphs with the specified class
    matching_paragraphs = soup.find_all('p', class_=class_name)


    for paragraph in matching_paragraphs:
        # Remove non-visible characters
        cleaned_text = re.sub(r'\s+', ' ', paragraph.get_text(strip=True))
        paragraphs.append(cleaned_text)

    return paragraphs

#convert cases to json file
def case_to_json(case_url, output_directory, visited_urls=set()):
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

            # Extract HTML content
            html_content = str(soup)
            
            case_name = extract_case_name(html_content)
            citation = extract_citation(html_content)
            case_number,decision_date = extract_case_info(html_content)
            
            class_name_to_extract = "Judg-1"
            paragraphs = extract_paragraphs(html_content, class_name_to_extract)
            #extract the para, heading and table

            # Extract text content inside each paragraph
            paragraph_texts = [paragraph.get_text(strip=True) for paragraph in soup.find_all('p')]

            # Construct the full output file path for the case content
            case_output_file = os.path.join(output_directory, f'{citation}.json')

            # Create a dictionary with case information
            case_data = {
                'case_name': case_name,
                'citation': citation,
                'case_number': case_number,
                'decision_date': decision_date,
                'url': case_url,
                'paragraphs': paragraphs,
                #headings = fill up,
                #table = fill up
                'html_content': html_content,
                # 'paragraph_texts': paragraph_texts
            }

            # Write the dictionary as JSON to the output file
            with open(case_output_file, 'w', encoding='utf-8') as file:
                json.dump(case_data, file, ensure_ascii=False, indent=2)

            print(f"Content from case '{case_url}' extracted and saved to '{case_output_file}'")

        else:
            print(f"Failed to fetch the case page '{case_url}'. Status code: {response.status_code}")

    except Exception as e:
        print(f"An error occurred: {str(e)}")

# Function to get the next page URL
def get_next_page_url(base_url, current_page, search_phrase):
    return f"{base_url}Index?Filter=SUPCT&YearOfDecision=All&SortBy=Score&SearchPhrase={search_phrase}&CurrentPage={current_page}&SortAscending=False&PageSize=0&Verbose=False&SearchQueryTime=0&SearchTotalHits=0&SearchMode=False&SpanMultiplePages=False"

# Change the correct directory
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
