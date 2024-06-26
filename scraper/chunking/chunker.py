import os
import json

"""
Modify scraped judgments: Concatenate bullet points into the previous paragraph
judgments/ --> modified_judgments/
"""
for file_name in os.listdir("judgments/"):
    with open(os.path.join("judgments", file_name), "r") as file:
        json_file = json.load(file)
        
        full_text = json_file.get("ordered list", [])
        
        para_index = 0

        while para_index < len(full_text):
            para = full_text[para_index]            
            if para.startswith("<table"):
                para_index += 1
            # If the paragraph starts with a bullet point, it likely belongs to the previous paragraph
            elif para.startswith("(") and not full_text[para_index-1].startswith("<table"):
                full_text[para_index-1] += para
                full_text.remove(para)
            else:
                para_index += 1
        
        json_data = {
            "case_name": json_file.get("case_name", ""),
            "citation": json_file.get("citation", ""),
            "full_text": full_text
        }
        
        with open(os.path.join("modified_judgments/" + file_name), "w") as outfile:
            json.dump(json_data, outfile, indent=4)

"""
Chunk judgments
modified_judgments/ --> chunked_judgments/
"""
for file_name in os.listdir("modified_judgments/"):
    with open(os.path.join("modified_judgments", file_name), "r") as file:
        # Load judgment contents
        json_file = json.load(file)
        
        CASE_NAME = json_file.get("case_name", "")
        CITATION = json_file.get("citation", "")
        
        full_text = json_file.get("full_text", [])
        chunks = []
        chunk_temp = ""
        table_number = 0
        tables = dict()
        while full_text:
            if full_text[0].startswith("<table"):
                # Scenario where chunk_temp contains text and a table is encountered. Append chunk_temp to chunks and reset chunk_temp.
                if chunk_temp:
                    chunks.append(chunk_temp + "<<table_no" + str(table_number) + ">>")
                    chunk_temp = ""
                tables["<<table_no" + str(table_number) + ">>"] = full_text.pop(0)
                chunks.append("<<table_no" + str(table_number) + ">>")
                table_number += 1
            #! Change the token limit if context limit is reached
            elif len(chunk_temp) + len(full_text[0]) < 4000:
                chunk_temp += full_text.pop(0)
            else:
                chunks.append(chunk_temp)
                chunk_temp = full_text.pop(0)
        
        # Append any remaining chunk_temp to chunks
        if chunk_temp:
            chunks.append(chunk_temp)
        
        # Create a new json file with the chunked judgment
        chunked_judgment = {
            "case_name": CASE_NAME,
            "citation": CITATION,
            "chunks": chunks,
            "tables": tables
        }
        
        with open(("chunked_judgments/" + file_name), "w") as outfile:
            json.dump(chunked_judgment, outfile, indent=4)