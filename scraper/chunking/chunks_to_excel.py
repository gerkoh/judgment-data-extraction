import os
import json
import pandas as pd

label = "Length of marriage till IJ (include separation period): NA;Length of marriage (exclude separation period): NA;Number of children: NA;Wife's income (monthly): NA;Husband's income (monthly): NA;Single or dual income marriage: NA;Direct contribution (Wife): NA;Indirect contribution (Wife): NA;Average ratio (Wife): NA;Final ratio (post-adjustments): NA;Adjustments were for: NA;"
# label = "null_value"

# Open CSV file in write mode
with open("chunked_judgments.csv", "w") as file:
    # Load chunked_judgments data into csv file
    for file_name in os.listdir("chunked_judgments/"):
        with open(os.path.join("chunked_judgments/", file_name), "r", encoding="utf-8") as json_file:
            json_data = json.load(json_file)
            judgment_name = json_data.get("case_name", "")
            judgment_citation = json_data.get("citation", "")
            chunks = json_data.get("chunks", [])
            
            # Write each chunk to the CSV file
            for chunk in chunks:
                if chunk.startswith("<<table_no"):
                    chunk = json_data.get("tables", {}).get(chunk, "")
                chunk = chunk.replace("\"", "\\\"")  # Escape double quotes within the chunk string
                file.write(f"{judgment_name} {judgment_citation}\t{chunk}\t{label}\n")# Enclose chunk in quotes and add null label
                

# Convert CSV file to Excel file
# Read the CSV file into a pandas DataFrame
names = ["judgment", "chunk", "label"]
df = pd.read_csv("chunked_judgments.csv", sep='\t', names=names, encoding="utf-8")

# Convert the DataFrame to an Excel file
df.to_excel("chunked_judgments.xlsx", index=False)