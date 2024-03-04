import openai
from dotenv import load_dotenv
import os
import json
import time
import csv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = openai.OpenAI()
client.api_key = OPENAI_API_KEY

def read_md_judgment(file_path):
    with open(file_path, 'r', encoding="utf-8") as file:
        data = json.load(file)
        full_text = data["full_text"]
    return full_text

def gpt4_api_call(judgment_full_text):
    completion = client.chat.completions.create(
            model="gpt-4-turbo-preview",
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
    tokens = completion.usage.total_tokens
    response = completion.choices[0].message.content
    # response = json.loads(response)
    return response, tokens

def append_to_md_judgment(item, file_path):
    with open(file_path, 'r', encoding="utf-8") as file:
        json_data = json.load(file)
    json_data["gpt4_response"] = json.loads(item)
    with open(file_path, 'w', encoding="utf-8") as file:
        json.dump(json_data, file, indent=4, ensure_ascii=False)
    return (file_path + " updated.")

# Insert the folder path with the markdown judgments
folder_path = 'md_judgments/'

for file_name in os.listdir(folder_path):
    # Keeps track of time for each file for comparison
    if file_name.endswith('.json'):
        startTime = time.time()
        print("Processing file:", file_name)
        
        json_file_path = os.path.join(folder_path, file_name)
        full_text = read_md_judgment(json_file_path)
        gpt_response = gpt4_api_call(full_text)
        append_to_md_judgment(gpt_response[0], json_file_path)
        print("Completed file:", file_name)
        
        endTime = time.time()
        elapsedTime = endTime - startTime
        
        with open("logs.csv", "a", newline='') as file:
            writer = csv.writer(file)
            writer.writerow([file_name, elapsedTime, gpt_response[1]])