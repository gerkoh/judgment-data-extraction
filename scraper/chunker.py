import os
import json

for file_name in os.listdir("judgments/"):
    with open(os.path.join("judgments", file_name), "r") as file:
        # Load judgment contents
        json_file = json.load(file)
        
        CASE_NAME = json_file.get("case_name", "")
        CITATION = json_file.get("citation", "")
        
        paragraphs = json_file.get("paragraphs", [])
        chunks = []
        chunk_temp = ""
        while paragraphs:
            if len(chunk_temp) + len(paragraphs[0]) < 4000:
                chunk_temp += paragraphs.pop(0)
            else:
                chunks.append(chunk_temp)
                chunk_temp = paragraphs.pop(0)
        
        # Append any remaining chunk_temp to chunks
        if chunk_temp:
            chunks.append(chunk_temp)
        
        # Create a new json file with the chunked judgment
        chunked_judgment = {
            "case_name": CASE_NAME,
            "citation": CITATION,
            "chunks": chunks
        }
        
        with open(("chunked_judgments/" + file_name), "w") as outfile:
            json.dump(chunked_judgment, outfile, indent=4)