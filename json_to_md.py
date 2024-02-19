import json
import pandas as pd
from bs4 import BeautifulSoup
import os

def extract_ordered_list(json_file_path):
    try:
        with open(json_file_path, 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        print(f"File '{json_file_path}' not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error decoding JSON from '{json_file_path}'.")
        return None
    ordered_list = data["ordered list"]
    return ordered_list


def convert_to_md(ordered_list):
    md_output = ""
    for string in ordered_list:
        if "<table" in string:
            # Parse HTML table into Pandas DataFrame
            soup = BeautifulSoup(string, 'html.parser')
            table = soup.find('table')
            df = pd.read_html(str(table))[0]  # Assuming there's only one table
            # Convert DataFrame to Markdown
            md_output += df.to_markdown(index=False) + "\n\n"
        else:
            md_output += string + "\n\n"
    return md_output



folder_path = 'xyz'
# Iterate through all files in the folder
for filename in os.listdir(folder_path):
    if filename.endswith('.json'):
        json_file_path = os.path.join(folder_path, filename)
        ordered_list = extract_ordered_list(json_file_path)
        # Convert the list of strings to Markdown
        md_result = convert_to_md(ordered_list)

        output_file_path = 'output_path'
        with open(output_file_path, 'w') as file:
            json.dump({'markdown': md_result}, file)
        print("Markdown output has been written to:", output_file_path)

        # print(md_result)

