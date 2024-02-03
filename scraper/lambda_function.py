import requests
import json
import boto3
import logging
import csv
import os
from bs4 import BeautifulSoup
from datetime import datetime

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

def get_latest_case_in_csv():
    # Get the CSV file from the S3 bucket
    response = s3.get_object(Bucket=S3_BUCKET, Key=JUDGMENT_CSV)
    csv_data = response['Body'].read().decode('utf-8')

    # Parse the CSV data
    csv_rows = csv_data.split('\n')
    csv_reader = csv.reader(csv_rows)

    # Get the latest case in CSV
    latest_case = list(csv_reader)[-1]

    # Get the casename of the latest case in CSV
    casename = latest_case[0]

    return casename

def get_latest_case_from_url(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Get the latest case from url
    for a_tag in soup.find_all('a', href=True):
        if a_tag['href'].startswith('/gd/s/'):
            casename = a_tag.text.strip()
            break
    return casename

def get_cases_from_url_page(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Initialise empty list to store casenames
    ls_cases = []
    
    # Get list of cases from url
    for a_tag in soup.find_all('a', href=True):
        if a_tag['href'].startswith('/gd/s/'):
            casename = a_tag.text.strip()
            ls_cases.append(casename)
    return ls_cases

def lambda_handler(event, context):
    # Get the latest casename in CSV
    latest_casename_csv = get_latest_case_in_csv()

    # Get the latest casename from url
    latest_casename_url = get_latest_case_from_url(url="https://www.elitigation.sg/gd/Home/Index?filter=SUPCT&yearOfDecision=All&sortBy=Score&currentPage=1&sortAscending=False&searchPhrase=%22division%20of%20matrimonial%20assets%22&verbose=False")
    
    # If the latest case in CSV is the same as the latest case from url, there are no new cases
    if latest_casename_csv == latest_casename_url:
        message = 'There are no new judgments.'
        logger.info(message)

    # If the latest casename in CSV is not the same as the latest casename from url, there are new cases to scrape
    else:
        #! TODO: Check how many new cases there are
        #! TODO: For each new case, check in CSV if the case has been processed (comparing citations)
            #! TODO: If the case has not been processed, scrape the case and upload to S3
            #! TODO: Elif case has been processed previously, add the citation to previous citations column