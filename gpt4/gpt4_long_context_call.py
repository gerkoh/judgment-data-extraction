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
                    Extract data according to the fixed headers given. Follow the output format strictly.\n
                    Length of marriage till IJ (include separation period): <extracted data>
                    Length of marriage (exclude separation period): <extracted data>
                    Number of children: NA;Wife's income (monthly): <extracted data>
                    Husband's income (monthly): <extracted data>
                    Single or dual income marriage: <extracted data>
                    Direct contribution (Wife): <extracted data>
                    Indirect contribution (Wife): <extracted data>
                    Average ratio (Wife): <extracted data>
                    Final ratio (post-adjustments): <extracted data>
                    Adjustments were for: <extracted data>
                    """
                }
            ]
        )
    response = completion.choices[0].message.content
    # response = json.loads(response)
    return response

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
    startTime = time.time()
    print("Processing file:", file_name)
    
    json_file_path = os.path.join(folder_path, file_name)
    full_text = read_md_judgment(json_file_path)
    gpt_response = gpt4_api_call(full_text)
    append_to_md_judgment(gpt_response, json_file_path)
    print("Completed file:", file_name)
    
    endTime = time.time()
    elapsedTime = endTime - startTime
    
    with open("time_log.csv", "a", newline='') as file:
        writer = csv.writer(file)
        writer.writerow([file_name, elapsedTime])
    
    time.sleep(60) # 3 RPM, to avoid rate limit