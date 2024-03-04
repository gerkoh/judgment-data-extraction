import requests
import json
import boto3
import logging
import csv
import os
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin
import re

# Create S3 Client
s3 = boto3.client('s3')
sns = boto3.client('sns')

S3_BUCKET = os.environ.get('JUDGMENT_SCRAPER_S3_BUCKET')
JUDGMENT_CSV = os.environ.get('JUDGMENT_CSV')

# Create a logging object
logger = logging.getLogger()

# Set the log level to .INFO, so only messages with level .INFO or higher will be logged. Toggle DEBUG for debugging.
logger.setLevel(logging.INFO)
# logger.setLevel(logging.DEBUG)

"""
Lambda function runs every __ days to check for new judgments on the eLitigation website.
If there are new judgments,
    i. the function will scrape the judgment and upload it to the S3 bucket;
    ii. which will invoke the DSPy pipeline to process the judgment and update the CSV file,
    iii. which is subsequently re-uploaded to the S3 bucket.
"""

def get_latest_case_citation_from_csv():
    # Get the CSV file from the S3 bucket
    response = s3.get_object(Bucket=S3_BUCKET, Key=JUDGMENT_CSV)
    csv_data = response['Body'].read().decode('utf-8')

    # Parse the CSV data
    csv_rows = csv_data.split('\n')
    csv_reader = csv.reader(csv_rows)

    # Get the latest case in CSV
    latest_case = list(csv_reader)[-1]

    # Get the casename of the latest case in CSV
    citation = latest_case[1]

    formatted_citation = citation.replace("[", "").replace("]", "").replace(" ", "_")

    return formatted_citation

def get_latest_case_citation_from_url(soup):
    # Get the latest case from url
    for a_tag in soup.find_all('a', href=True):
        if a_tag['href'].startswith('/gd/s/'):
            casename = a_tag.text.strip()
            break
    return casename

def is_valid_case_url(url):
    # Check if the URL is a case URL based on the pattern
    return "elitigation.sg/gd/s/" in url

def get_judgment_urls_to_scrape(url, soup, latest_case_citation_from_csv):
    all_urls_on_page = []
    for link in soup.find_all('a', href=True):
        formatted_link = urljoin(url, link['href'])
        if is_valid_case_url(formatted_link):
            all_urls_on_page.append(formatted_link)
    
    urls_to_scrape = []
    for link in all_urls_on_page:
        if latest_case_citation_from_csv in link:
            break
        urls_to_scrape.append(link)
    return urls_to_scrape

def get_judgment_urls_to_scrape(url, soup, latest_case_citation_from_csv):
    all_urls_on_page = []
    for link in soup.find_all('a', href=True):
        formatted_link = urljoin(url, link['href'])
        if is_valid_case_url(formatted_link):
            all_urls_on_page.append(formatted_link)
    
    urls_to_scrape = []
    for link in all_urls_on_page:
        if latest_case_citation_from_csv in link:
            break
        urls_to_scrape.append(link)
    return urls_to_scrape

def extract_case_name(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    case_title_tag = soup.find('span', class_='caseTitle')
    if not case_title_tag:
        case_title_tag = soup.find('div', class_="HN-CaseName")
    if case_title_tag:
        case_title = ' '.join(case_title_tag.stripped_strings)
        return case_title
    return ""

# extract case name from html content
def extract_case_name(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    case_title_tag = soup.find('span', class_='caseTitle')
    if not case_title_tag:
        case_title_tag = soup.find('div', class_="HN-CaseName")
    if case_title_tag:
        case_title = ' '.join(case_title_tag.stripped_strings)
        return case_title
    return ""

#extract citation from url
def extract_citation(url):
    # Extract the case ID from the case URL
    # Customize this function based on the actual URL structure
    url_parts = url.split('/')
    citation = url_parts[-1]
    return citation

#extract case_number,decision_date from html content
def extract_case_number(html_content):
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
        return case_number
    #if infor table not found, use tag and extract first index from it
    case_number_tag = soup.find('div', class_='HN-Coram')
    if case_number_tag:
        first_element = case_number_tag.contents[0]
        case_number = ' '.join(first_element.stripped_strings)
        return case_number

    return ""

def extract_decision_date(html_content):
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
        
        decision_date = case_info.get('Decision Date', '')
        
        return decision_date
      
    #if info table not found, try finding using tag
    decision_date_tag = soup.find('div', class_='Judg-Date-Reserved')
    if decision_date_tag:
        decision_date = ' '.join(decision_date_tag.stripped_strings)
        return decision_date
    
    return ''

#extract paragraph classes
def extract_paragraph_classes(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    paragraph_classes = set()
    for tag in soup.find_all(class_=True):
        for class_name in tag.get('class', []):
            if any(prefix in class_name for prefix in ['Judg-1', 'Judg-2', 'Judg-3', 'Judge-Quote-','Judg-Quote']):
                paragraph_classes.add(class_name)
    paragraph_classes = list(paragraph_classes)
    
    #if a table tag is collected, we have to remove it from the class list, to ensure no stripped tables in paragraph classes
    class_names = []
    for tag in soup.find_all('table', class_=True):
        class_names = tag.get('class', [])
    if class_names:
        for class_name in class_names:
            if class_name in paragraph_classes:
                paragraph_classes.remove(class_name)
        
    return paragraph_classes

#extract paragraphs in order
def extract_paragraphs_in_order(html_content, paragraph_classes):
    soup = BeautifulSoup(html_content, 'html.parser')
    paragraphs = []

    for tag in soup.find_all():
        if any(paragraph_class in tag.get('class', []) for paragraph_class in paragraph_classes):
            #clean text
            paragraph_text = re.sub(r'\s+', ' ', tag.get_text(strip=True))
            while len(paragraph_text)>=1 and paragraph_text[0].isdigit():
                paragraph_text = paragraph_text[1:]
            #ensure no empty paragraph strings are appended to the list
            if len(paragraph_text)>0:
                paragraphs.append(paragraph_text)

    return paragraphs

#extract header classes
def extract_header_classes(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    header_classes = set()

    for tag in soup.find_all(class_=True):
        for class_name in tag.get('class', []):
            if 'Judg-Heading-' in class_name:
                header_classes.add(class_name)

    return list(header_classes)

#extract headers in order
def extract_headers_in_order(html_content, header_classes):
    soup = BeautifulSoup(html_content, 'html.parser')
    headers = []

    for tag in soup.find_all():
        if any(header_class in tag.get('class', []) for header_class in header_classes):
            header_text = re.sub(r'\s+', ' ', tag.get_text(strip=True))
            headers.append(header_text)
    return headers

# extract table classes from <table> tags
def extract_table_classes_from_tag(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    table_classes = set()
    #searches for <table> tag and returns the class unique class names of the table
    for tag in soup.find_all('table', class_=True):
        class_names = tag.get('class', [])
        if class_names:
            table_classes.add(class_names[0])

    return list(table_classes)

#extract tables in order
def extract_tables_in_order(html_content, table_classes):
    soup = BeautifulSoup(html_content, 'html.parser')
    tables= []

    for tag in soup.find_all():
        if any(table_tag in tag.get('class', []) for table_tag in table_classes):
            tables.append(str(tag))

    return tables

#extracts_everything in order, returns as a list of tuples. (e.g.)[('header',"content of header"),('paragraph'),('content of paragraph')]
def extract_everything_in_order(html_content, header_classes, paragraph_classes,table_classes):
    soup = BeautifulSoup(html_content, 'html.parser')
    result_list = []

    for tag in soup.find_all():
        if any(header_class in tag.get('class', []) for header_class in header_classes):
            header_text = re.sub(r'\s+', ' ', tag.get_text(strip=True))
            result_list.append(('header', header_text))
        if any(paragraph_class in tag.get('class', []) for paragraph_class in paragraph_classes):
            #clean para from html tag and remove the initial paragraph numbering
            paragraph_text = re.sub(r'\s+', ' ', tag.get_text(strip=True))
            while len(paragraph_text)>=1 and paragraph_text[0].isdigit():
                paragraph_text = paragraph_text[1:]  
            #ensure no empty paragraph strings are appended to the list
            if len(paragraph_text)>0:
                result_list.append(('paragraph', paragraph_text))
            
        if any(table_tag in tag.get('class', []) for table_tag in table_classes):
            result_list.append(('table',str(tag)))
            
    return result_list

#extract paragraphs and table in order in an ordered list
def extract_paragraphs_and_tables_in_order(html_content, paragraph_classes, table_classes):
    soup = BeautifulSoup(html_content, 'html.parser')
    result_list = []
    for tag in soup.find_all():
        if any(paragraph_class in tag.get('class', []) for paragraph_class in paragraph_classes):
            #clean para from html tag and remove the initial paragraph numbering
            paragraph_text = re.sub(r'\s+', ' ', tag.get_text(strip=True))
            while len(paragraph_text)>=1 and paragraph_text[0].isdigit():
                paragraph_text = paragraph_text[1:] 
            #ensure no empty paragraph strings are appended to the list
            if len(paragraph_text)>0:
                result_list.append(paragraph_text)
              
        if any(table_tag in tag.get('class', []) for table_tag in table_classes):
            result_list.append(str(tag))
    return result_list    

#convert the tuple from everything in order into an ordered dictionary header:paragraphs/table
def convert_to_dictionary(tuple_list):
    my_dict = {}

    for i in tuple_list:
      #if the dictionary is empty and first element is a paragraph/table, append paragraph to value of "preliminary" key
        if not my_dict:
            if i[0] in ['paragraph', 'table']:
                my_dict['preliminary'] = [i[1]]
                continue  
            #if the dictionary is empty and first element is a header, append header name to key  
            elif i[0] == 'header':
                my_dict[i[1]] = []
                continue  # Skip to the next iteration
        else:
            last_key, last_value = list(my_dict.items())[-1]
            # if the last key in the dict is 'preliminary' and the following items in tuple are still paragraphs or table
            if last_key == 'preliminary' and i[0] in ['paragraph', 'table']:
                my_dict['preliminary'].append(i[1])
                continue
            # if the last key in the dict is a header and the following item is paragraph or table
            if last_key != 'preliminary' and i[0] in ['paragraph', 'table']:
                my_dict[last_key].append(i[1])
                continue
            #if the last key in the dict is a preliminary and the following item is  a header. the new header becomes the latest key
            if last_key in ['preliminary'] and i[0] in ['header']:
                my_dict[i[1]] = []
                continue
            #if the last key in the dict is a header and the following item is also a header. the new header becomes the latest key
            if last_key not in ['preliminary'] and i[0] in ['header']:
                my_dict[i[1]] = []
                continue

    return my_dict

#convert cases to json file
def case_to_json(case_url, output_directory):
    try:
        #extract citation from url
        citation = extract_citation(case_url)
        
        # Send an HTTP GET request to the case URL
        response = requests.get(case_url)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the HTML content of the case page using BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract HTML content
            html_content = str(soup)
    
            case_name = extract_case_name(html_content)
            
            #extract case_number and decision date
            case_number = extract_case_number(html_content)
            decision_date = extract_decision_date(html_content)
            
            #extract_paragraphs in order
            paragraph_classes = extract_paragraph_classes(html_content)
            paragraphs = extract_paragraphs_in_order(html_content, paragraph_classes)
            
            #extract headers in order
            header_classes =extract_header_classes(html_content)
            headers = extract_headers_in_order(html_content, header_classes)
            
            #extracts tables in order
            table_classes = extract_table_classes_from_tag(html_content)
            tables = extract_tables_in_order(html_content, table_classes)
            
            #extract everything in order into a tuple_list
            everything_tuplelist = extract_everything_in_order(html_content, header_classes, paragraph_classes,table_classes)
            
            #convert everything into ordered dictionary format by header:para/table
            ordered_dictionary = convert_to_dictionary(everything_tuplelist)
            
            #ordered list of paragraphs and tables
            ordered_list_para_table = extract_paragraphs_and_tables_in_order(html_content, paragraph_classes, table_classes)
            
            # Construct the full output file path for the case content
            case_output_file = os.path.join(output_directory, f'{citation}.json')
            case_data = {
                'case_name': case_name,
                'citation': citation,
                'case_number': case_number,
                'decision_date': decision_date,
                'url': case_url,
                'headers' : headers,
                'paragraphs': paragraphs,
                'tables' : tables,
                'ordered list': ordered_list_para_table,
                'ordered_dictionary': ordered_dictionary
            }
             
            # Write the dictionary as JSON to the output file
            with open(case_output_file, 'w', encoding='utf-8') as file:
                json.dump(case_data, file, ensure_ascii=False, indent=2)
                

            print(f"Content from case '{case_url}' extracted and saved to '{case_output_file}'")

        else:
            print(f"Failed to fetch the case page '{case_url}'. Status code: {response.status_code}")

    except Exception as e:
        print(f"An error occurred: {str(e)}")

def lambda_handler(event, context):
    """
    Get latest casename in CSV
    Get the latest casename from url
    If the latest case in CSV is the same as the latest case from url, there are no new cases, end the process.
    Else, if the latest casename in CSV is not the same as the latest casename from url, there are new cases to scrape.
        Get cases to scrape
        Use scraper to get json
        Upload json
        Run GPT code
    """
    page = 1
    url = f"https://www.elitigation.sg/gd/Home/Index?filter=SUPCT&yearOfDecision=All&sortBy=DateOfDecision&currentPage={page}&sortAscending=False&searchPhrase=%22division%20of%20matrimonial%20assets%22&verbose=False"
    
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    latest_case_citation_from_csv = get_latest_case_citation_from_csv()

    latest_case_citation_from_url = get_latest_case_citation_from_url(soup=soup)
    
    if latest_case_citation_from_csv == latest_case_citation_from_url:
        # message = 'There are no new judgments.'
        # logger.info(message)
        print("There are no new judgments")

    else:
        #! TODO: Check how many new cases there are
        #! TODO: For each new case, check in CSV if the case has been processed (comparing citations)
            #! TODO: If the case has not been processed, scrape the case and upload to S3
            #! TODO: Elif case has been processed previously, add the citation to previous citations column
            
        
        judgment_urls_to_scrape = get_judgment_urls_to_scrape(url=url, soup=soup, latest_case_citation_from_csv=latest_case_citation_from_csv)

        #! 2 options: immediately convert to full text and run GPT pipeline / write to S3 bucket and use new lambda function
        for judgment_url in judgment_urls_to_scrape: # run scraper on list of cases to scrape
            json_data = case_to_json(judgment_url, "scraped_data_from_aws/")