import requests
from bs4 import BeautifulSoup
import json
import os
from urllib.parse import urljoin
import re

response = requests.get('https://www.lawnet.sg/lawnet/web/lawnet/free-resources?p_p_id=freeresources_WAR_lawnet3baseportlet&p_p_lifecycle=1&p_p_state=normal&p_p_mode=view&p_p_col_id=column-1&p_p_col_pos=2&p_p_col_count=3&_freeresources_WAR_lawnet3baseportlet_action=openContentPage&_freeresources_WAR_lawnet3baseportlet_docId=/Judgment/30720-SSP.xml#Ftn_39')

soup = BeautifulSoup(response.text, 'html.parser')
html_content = str(soup)

def extract_paragraph_classes(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    paragraph_classes = set()
    for tag in soup.find_all(class_=True):
        if tag.name == 'p':
            for class_name in tag.get('class', []):
                if any(prefix in class_name for prefix in ['Judg-1', 'Judg-2', 'Judg-3', 'Judg-Quote']):
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
            #remove numbering of para
            while len(paragraph_text)>=1 and paragraph_text[0].isdigit():
                paragraph_text = paragraph_text[1:]
            #ensure no empty paragraph strings are appended to the list
            if len(paragraph_text)>0:
                paragraphs.append((tag,paragraph_text))

    return paragraphs
x = extract_paragraph_classes(html_content)

y=extract_paragraphs_in_order(html_content,x)

print(y)