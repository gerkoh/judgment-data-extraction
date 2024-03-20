import requests
import boto3
# import logging
from bs4 import BeautifulSoup
from datetime import date
from urllib.parse import urljoin
import pandas as pd
from openai import OpenAI

from io import StringIO
import re
import json
import csv
import os

"""
todo on aws lambda function:
- runtime must be python 3.9
- increase timeout
- add AWS layer to lambda function - pandas
- add openai layer https://medium.com/@aalc928/2024-guide-to-deploying-openai-in-aws-lambda-the-essential-checklist-f58cd24e0c36
    - pip install openai -t . --only-binary=:all: --upgrade --platform manylinux2014_x86_64
    - zip -r openai-package.zip openai
    - pip install tabulate -t . --only-binary=:all: --upgrade --platform manylinux2014_x86_64
    - zip -r tabulate-package.zip python
- increase max memory to 512GB
- set environment variables in aws config
- check permissions given to function
"""

# Create S3 Client
s3 = boto3.client('s3')
sns = boto3.client('sns')

S3_BUCKET = os.environ.get('JUDGMENT_SCRAPER_S3_BUCKET')
JUDGMENT_CSV = os.environ.get('LAWNET_JUDGMENT_CSV')
SNS_ARN = os.environ.get('SNS_ARN')

# logger = logging.getLogger()
today = date.today()
log_subject = 'Upload Notification for ' + str(today)

# Set the log level to .INFO, so only messages with level .INFO or higher will be logged. Toggle DEBUG for debugging.
# logger.setLevel(logging.INFO)
# logger.setLevel(logging.DEBUG)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

client = OpenAI()
client.api_key = OPENAI_API_KEY

def gpt4_api_call(judgment_full_text):
    completion = client.chat.completions.create(
            # model="gpt-4-turbo-preview",
            model="gpt-3.5-turbo-0125",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a helpful assistant designed to output JSON. Take the judgment data and extract the required information from it."},
                {"role": "user", "content": 
                    f"""
                    Judgment data:\n
                    ```{judgment_full_text}```
                    \n\n
                    Extract data from the judgment according to the fixed headers given. Follow the output format strictly.\n
                    Length of marriage till Interim Judgment for divorce (including separation period): <if judgment contains the information, then provide the extracted data as an integer. Otherwise, 'Undisclosed'.>\n
                    Length of marriage (exclude separation period): <if judgment contains the information, then provide the extracted data as an integer. Otherwise, 'Undisclosed'.\n
                    Number of children: <extracted data, an integer>\n
                    Wife's income (monthly): <extracted data, an integer>\n
                    Husband's income (monthly): <extracted data, an integer>\n
                    Single or dual income marriage: <extracted data, 'Undisclosed', 'dual' or 'single'>\n
                    Direct contribution (Wife): <extracted data, in percentage>\n
                    Indirect contribution (Wife): <extracted data, in percentage>\n
                    Average ratio (Wife): <if judgment contains the information, then provide the extracted data as an integer. Otherwise, calculate as (direct + indirect contribution)/2, in percentage>\n
                    Final ratio (post-adjustments): <extracted data>\n
                    Adjustments: <(final ratio - average ratio), as integer>\n
                    Adjustments were for: <extracted data, reasons given from the judgment>
                    """
                }
            ]
        )
    response = completion.choices[0].message.content
    
    return response

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

def get_latest_case_from_lawnet(soup):
    for link in soup.find_all('a', href=True):
        # find <a> tag with href starting with 'javascript:viewContent('
        if link['href'].startswith("javascript:viewContent('"):
            citation_and_casename = link.text
            break
    formatted_citation = citation_and_casename.split(" - ")[1].strip().replace(" ", "_").replace("[","").replace("]","")
    return formatted_citation

def get_judgment_urls_to_scrape(url, latest_case_citation_from_csv):
    try:
        # Send an HTTP GET request to the URL
        response = requests.get(url)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the HTML content of the page using BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # list contains tuples (case citation, url)
            all_citations_and_urls_on_page = []
            base = "https://www.lawnet.sg/lawnet/web/lawnet/free-resources?p_p_id=freeresources_WAR_lawnet3baseportlet&p_p_lifecycle=1&p_p_state=normal&p_p_mode=view&p_p_col_id=column-1&p_p_col_pos=2&p_p_col_count=3&_freeresources_WAR_lawnet3baseportlet_action=openContentPage&_freeresources_WAR_lawnet3baseportlet_docId="
            
            # Find all links on the page
            for link in soup.find_all('a', href=True):
                if link['href'].startswith("javascript:viewContent('"):
                    case_url = base + link['href'].replace("javascript:viewContent('", "").replace("'", "")
                    citation = link.text.split(" - ")[1].strip().replace(" ", "_").replace("[","").replace("]","")
                    all_citations_and_urls_on_page.append((citation, case_url))
            
            urls_to_scrape = []
            for tup in all_citations_and_urls_on_page:
                citation = tup[0]
                link = tup[1]
                if latest_case_citation_from_csv in citation:
                    break
                urls_to_scrape.append(link)
            return urls_to_scrape

        else:
            log_msg = f"Failed to fetch the web page '{url}'. Status code: {response.status_code}"
            sns.publish(
                TopicArn=SNS_ARN,
                Message=log_msg,
                Subject=log_subject
            )

    except Exception as e:
        log_msg = f"An error occurred: {str(e)}"
        sns.publish(
                TopicArn=SNS_ARN,
                Message=log_msg,
                Subject=log_subject
            )

def extract_case_name(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    case_title_tag = soup.find('span', class_='caseTitle')
    if not case_title_tag:
        case_title_tag = soup.find('div', class_="HN-CaseName")
    if case_title_tag:
        case_title = ' '.join(case_title_tag.stripped_strings)
        return case_title
    return ""

def extract_citation(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    case_citation_tag = soup.find('span', class_='Citation')
    if case_citation_tag:
        case_citation = ' '.join(case_citation_tag.stripped_strings)
        return case_citation
    return ""

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

def extract_paragraph_classes(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    paragraph_classes = set()
    for tag in soup.find_all(class_=True):
        if tag.name == 'p':
            for class_name in tag.get('class', []):
                if any(prefix in class_name for prefix in ['Judg-1', 'Judg-2', 'Judg-3', 'Judg-Quote','Judge-Quote','Judg-List']):
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

def extract_paragraphs_in_order(html_content, paragraph_classes):
    soup = BeautifulSoup(html_content, 'html.parser')
    paragraphs = []

    for tag in soup.find_all():
        if any(paragraph_class in tag.get('class', []) for paragraph_class in paragraph_classes):
            #clean text
            paragraph_text = re.sub(r'\s+', ' ', tag.get_text(strip=True))
            #remove numbering of para
            while len(paragraph_text)>=1 and paragraph_text[0].isdigit():
                paragraph_text = paragraph_text[1:]
            #ensure no empty paragraph strings are appended to the list
            if len(paragraph_text)>0:
                paragraphs.append(paragraph_text)

    return paragraphs

def extract_header_classes(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    header_classes = set()

    for tag in soup.find_all(class_=True):
        for class_name in tag.get('class', []):
            if 'Judg-Heading-' in class_name:
                header_classes.add(class_name)

    return list(header_classes)

def extract_headers_in_order(html_content, header_classes):
    soup = BeautifulSoup(html_content, 'html.parser')
    headers = []

    for tag in soup.find_all():
        if any(header_class in tag.get('class', []) for header_class in header_classes):
            header_text = re.sub(r'\s+', ' ', tag.get_text(strip=True))
            headers.append(header_text)
    return headers

def extract_table_classes_from_tag(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    table_classes = set()
    #searches for <table> tag and returns the class unique class names of the table
    for tag in soup.find_all('table', class_=True):
        class_names = tag.get('class', [])
        if class_names:
            table_classes.add(class_names[0])

    return list(table_classes)

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

def convert_to_md(ordered_list):
    md_output = ""
    for string in ordered_list:
        if "<table" in string:
            # Parse HTML table into Pandas DataFrame
            soup = BeautifulSoup(string, 'html.parser')
            table = soup.find('table')
            df = pd.read_html(StringIO(str(table)))[0]  # Assuming there's only one table
            # Convert DataFrame to Markdown
            md_output += df.to_markdown(index=False) + "\n\n"
        else:
            md_output += string + "\n\n"
    md_output = str(md_output)
    return md_output.encode('utf-8')

def case_to_json(case_url):
    try:
        # Send an HTTP GET request to the case URL
        response = requests.get(case_url)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the HTML content of the case page using BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract HTML content
            html_content = str(soup)
            
            #extract citation from html content
            citation = extract_citation(html_content)
    
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
            
            full_text = convert_to_md(ordered_list_para_table).decode('utf-8')
            
            # Construct the full output file path for the case content
            case_data = {
                'case_name': case_name,
                'citation': citation,
                'case_number': case_number,
                'decision_date': decision_date,
                'url': case_url,
                'headers' : headers,
                'paragraphs': paragraphs,
                'tables' : tables,
                'ordered_list': ordered_list_para_table,
                'ordered_dictionary': ordered_dictionary,
                'full_text': full_text
            }
            
            data = json.dumps(case_data, ensure_ascii=False, indent=2)
            
            s3.put_object(Bucket=S3_BUCKET, Key=f'judgments/{citation}.json', Body=data)
            
            # Success message
            log_msg = f"Content from case '{citation}' extracted and saved to 'judgments/{citation}'.\n"
            
            gpt_response = json.loads(gpt4_api_call(full_text))
            gpt_response_list = list(gpt_response.values())
            to_insert = [case_name, citation, decision_date] + gpt_response_list
            
            csv_response = s3.get_object(Bucket=S3_BUCKET, Key=JUDGMENT_CSV)
            csv_response_status = csv_response.get("ResponseMetadata", {}).get("HTTPStatusCode")
            
            if csv_response_status == 200:
                csv_data = pd.read_csv(csv_response.get("Body"), index_col=False)
                # missing_values_count = len(csv_data.columns) - len(to_insert)
                # new_data_extended = to_insert + [""] * missing_values_count
                new_df = pd.DataFrame([to_insert], columns=csv_data.columns)
                csv_data = pd.concat([csv_data, new_df], ignore_index=True).to_csv(encoding='utf-8', index=False)
                s3.put_object(Bucket=S3_BUCKET, Key=JUDGMENT_CSV, Body=csv_data)
                log_msg += "Successfully updated the CSV file with the extracted information."
            else:
                log_msg += f"Failed to update the CSV file with the extracted information, error: {csv_response_status}."
            
            sns.publish(
                TopicArn=SNS_ARN,
                Message=log_msg,
                Subject=log_subject
            )

        else:
            log_msg = f"Failed to fetch the case '{citation}'. Status code: {response.status_code}."
            
            sns.publish(
                TopicArn=SNS_ARN,
                Message=log_msg,
                Subject=log_subject
            )

    except Exception as e:
        log_msg = f"{citation}\nAn error occurred: {str(e)}."
        sns.publish(
                TopicArn=SNS_ARN,
                Message=log_msg,
                Subject=log_subject
            )

def lambda_handler(event, context):
    """
    Logic:
    Get latest casename in CSV
    Get the latest casename from url
    If the latest case in CSV is the same as the latest case from url, there are no new cases, end the process.
    Else, there are new cases to scrape.
        - Get cases to scrape
        - Use scraper to get the judgment in json format
        - Upload json to S3 bucket
        - Run pipeline on case and update CSV with extracted information
    """
    url = 'https://www.lawnet.sg/lawnet/web/lawnet/free-resources?p_p_id=freeresources_WAR_lawnet3baseportlet&p_p_lifecycle=0&p_p_state=normal&p_p_mode=view&p_p_col_id=column-1&p_p_col_pos=2&p_p_col_count=3&_freeresources_WAR_lawnet3baseportlet_action=juvenile'
    
    latest_case_citation_from_csv = get_latest_case_citation_from_csv()
    
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    latest_case_citation_from_lawnet = get_latest_case_from_lawnet(soup=soup)

    if latest_case_citation_from_csv == latest_case_citation_from_lawnet:
        log_msg = "There are no new judgments today. No cases have been uploaded to LAB spreadsheet."
        sns.publish(
            TopicArn=SNS_ARN,
            Message=log_msg,
            Subject=log_subject
        )

    else:
        #! scrape cases and run pipeline
        judgment_urls_to_scrape = get_judgment_urls_to_scrape(url=url, latest_case_citation_from_csv='2024_SGFC_9') # for testing
        # judgment_urls_to_scrape = get_judgment_urls_to_scrape(url=url, latest_case_citation_from_csv=latest_case_citation_from_lawnet)
        
        # Write new judgments to S3 bucket and use new lambda function to process the judgment
        for judgement_url in judgment_urls_to_scrape:
            case_to_json(judgement_url)