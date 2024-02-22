import csv
import json
import pandas

load_csv = "logs.csv"
df = pandas.read_csv(load_csv)

count = 0

json_obj = {}

for item in df["case_name"]:
    with open("md_judgments/" + item, 'r', encoding="utf-8") as file:
        json_data = json.load(file)
        json_obj[item] = json_data["gpt4_response"]

with open("results.json", 'w', encoding="utf-8") as file:
    json.dump(json_obj, file, indent=4, ensure_ascii=False)