import requests
from bs4 import BeautifulSoup
import json
import os
import re
import openai
from dotenv import load_dotenv
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI()
client.api_key = OPENAI_API_KEY

#to do
# DONE Run through folder of all cases, filters out appeal cases json files
# DONE extract link from json, scrapes web again, gets data of first instances (messy data)
# TO DO: Implement efficient gpt prompting to extract clean case names and applicagtion number from messy data
# DONE: push back data into the JSON file

sample_input = """
In the APPELLATE DIVISION of the 
HIGH COURT OF THE 
republic of singapore
[2022] SGHC(A) 6
Civil Appeal No 27 of 2021
Between
VOD
… 
Appellant
And
VOC
… 
Respondent
Civil Appeal No 28 of 2021
Between
VOC
… 
Appellant
And
VOD
… 
Respondent
In the matter of Divorce (Transferred) No 3470 of 2018
Between
VOC
… 
Plaintiff
And
VOD
… 
Defendant
judgment
[Family Law — Matrimonial assets — Division]
[Family Law — Maintenance — Child]
"""
sample_output =""" 
[Civil Appeal No 27 of 2021 , VOD V VOC], [Civil Appeal No 28 of 2021,VOC V VOD], [In the matter of Divorce (Transferred) No 3470 of 2018, VOC V VOD]
"""

def find_cases_before_judgment(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    div_judgment = None
    # Find the tag that encompasses the entire judgment
    for tag in soup.find_all(id=["divJudgment", "divJudgement"]):
        div_judgment = tag
        break
    # Identify the immediate next div that is nested, extract that chunk. Judgment only begins in the div after this
    # Returns string to push into llm
    if div_judgment:
        for next_sibling in div_judgment.find_all_next():
            if next_sibling.name == 'div' and 'row' in next_sibling.get('class', []):
                # Split the text content by lines, strip each line, and store them as a string
                return next_sibling.get_text('\n').strip()
    return None

#TO DO: PUT A PROPER PROMPT THAT WILL EXTRACT THE CASES OUT
# def gpt_api_call(full_text):
#     completion = client.chat.completions.create(
#             model="gpt-3.5-turbo-0125",
#             response_format={"type": "json_object"},
#             messages=[
#                 {"role": "system", "content": 
#                     f"""
#                     You are a helpful assistant that will compare a paragraph of text to a sample imput and output. \n
#                     sample input: ```{sample_input}```
                    
#                     sample output: ```{sample_output}```
#                     """
#                 },
#                 {"role": "user", "content": 
#                     f"""
#                     paragraph of text:\n
#                     ```{full_text}```
#                     \n\n
#                     Extract data from paragraph of text. Follow the output format strictly.
#                     Output: <produce an appropriate output exactly to that of the sample output>
#                     """
#                 },
#                 # Ensure that the word 'json' is present in the message content
#                 {"role": "system", "content": "json format"}
            
#             ]
#         )
    # tokens = completion.usage.total_tokens
    response = completion.choices[0].message.content
    # response = json.loads(response)
    return response


# Function to process JSON files in a folder
def process_appeal_case_files(folder_path):
    full_text = None
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.json'):
            file_path = os.path.join(folder_path, file_name)
            with open(file_path, 'r') as f:
                try:
                    json_data = json.load(f)
                    appeal_case = json_data.get('appeal_case')
                    if appeal_case == 'yes':
                        url = str(json_data.get('url'))
                        full_text = find_cases_before_judgment(url)  
                        print(str(full_text)) 
                except json.JSONDecodeError as e:
                    print(f"Error reading JSON file {file_name}: {e}\n")
            #prompt gpt for the proper values to be extracted from the list of values
        if full_text != None:
            prior_cases = []
            response = gpt_api_call(full_text)
            data = json.loads(response)
            for i in data['data']:
                prior_cases.append(i)  
            #sample: prior_cases = [{'case': 'High Court — District Court Appeal from the Family Courts No 150 of 2018', 'parties': 'UUV V UUU'}, {'case': 'In the matter of Divorce Suit No 3340 of 2017', 'parties': 'UUU V UUV'}]
            
            #inscribe data back onto the file
            with open(file_path, 'r+') as f:
                try:
                    json_data = json.load(f)
                    json_data['processed_cases'] = prior_cases
                    # Move the file pointer to the beginning of the file
                    f.seek(0)
                    # Write the updated JSON data back to the file
                    json.dump(json_data, f, indent=4)
                except json.JSONDecodeError as e:
                    print(f"Error reading JSON file {file_name}: {e}\n")
                except Exception as e:
                    print(f"Error processing JSON file {file_name}: {e}\n")
              

# Provide the path to the folder containing JSON files
folder_path = '/Users/ranveerbains/Documents/GitHub/judgment-data-extraction/judgments/test_cases'
# Call the function to process JSON files in the folder
process_appeal_case_files(folder_path)
