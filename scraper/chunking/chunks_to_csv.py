import os
import json
import pandas as pd

# Open CSV file in write mode
with open("chunked_judgments.csv", "w") as file:
    # Write headers: chunk, label
    file.write("chunk,label\n")
    
    # Load chunked_judgments data into csv file
    for file_name in os.listdir("chunked_judgments/"):
        with open(os.path.join("chunked_judgments/", file_name), "r") as json_file:
            json_data = json.load(json_file)
            chunks = json_data.get("chunks", [])
            for chunk in chunks:
                # Write each chunk to the CSV file
                if not chunk.startswith("<<table_no"):
                    file.write(f'"{chunk}",null\n')  # Enclose chunk in quotes and add null label

# Convert CSV file to Excel file
# Read the CSV file into a pandas DataFrame
df = pd.read_csv("chunked_judgments.csv")

# Convert the DataFrame to an Excel file
df.to_excel("chunked_judgments.xlsx", index=False)