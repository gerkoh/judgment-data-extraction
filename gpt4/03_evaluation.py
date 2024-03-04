import os
import json
import pandas as pd
import openai
from dotenv import load_dotenv


with open('results2.json', 'r') as load_file:
    generated_data = json.load(load_file)
with open('gold_standard.json', 'r') as load_file:
    gold_standard = json.load(load_file)

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY
def gpt4_api_call(gold_standard_holding, generated_holding):
    completion = openai.ChatCompletion.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are a helpful assistant comparing 2 paragraphs and identify if they are similar."},
                {"role": "user", "content": 
                    f"""
                    Paragraph 1:\n
                    ```{gold_standard_holding}```
                    \n
                    Paragraph 2:\n
                    ```{generated_holding}```
                    \n\n
                    Compare the 2 paragraphs and confirm if they are similar. Output should be 'True' or 'False' only.
                    If they are similar on some aspects but differ on others, output 'False'.
                    'N.A.', 'NA', 'nan', 'undisclosed', or empty should be considered similar.
                    """
                }
            ]
        )
    tokens = completion.usage.total_tokens
    response = completion.choices[0].message.content
    return response, tokens

df = pd.DataFrame(columns=['Case', 'Source', 'Length of marriage till IJ (include separation period)', 'Length of marriage (exclude separation period)', 'Number of children', 'Wife\'s income (monthly)', 'Husband\'s income (monthly)', 'Single or dual income marriage', 'Direct contribution (Wife)', 'Indirect contribution (Wife)', 'Average ratio (Wife)', 'Final ratio (post-adjustments)', 'Adjustments were for'])
total_score = 0
cases_matched = 0
formatting_errors = 0
not_found = []
for case in generated_data:
    if case[:-5] in gold_standard:
        cases_matched += 1
        print('\n')
        print(case[:-5])
        print('Errors:')
        score = 0
        row_data = [case[:-5], 'Extracted data']
        row_score = ['','']
        if 'Length of marriage till Interim Judgment for divorce (including separation period)' in generated_data[case].keys():
            if str(generated_data[case]['Length of marriage till Interim Judgment for divorce (including separation period)']).lower() in str(gold_standard[case[:-5]]['Length of marriage till IJ (include separation period)']).lower() or str(gold_standard[case[:-5]]['Length of marriage till IJ (include separation period)']).lower() in str(generated_data[case]['Length of marriage till Interim Judgment for divorce (including separation period)']).lower():
                score += 1
                row_score += ['1/1']
            elif str(generated_data[case]['Length of marriage till Interim Judgment for divorce (including separation period)']).lower() == 'undisclosed' and (str(gold_standard[case[:-5]]['Length of marriage till IJ (include separation period)']).lower() == 'na' or str(gold_standard[case[:-5]]['Length of marriage till IJ (include separation period)']).lower() == 'nan' or str(gold_standard[case[:-5]]['Length of marriage till IJ (include separation period)']).lower() == 'n.a.'):
                score += 1
                row_score += ['1/1']
            else:
                print('Extracted Length of marriage till IJ: ' + str(generated_data[case]['Length of marriage till Interim Judgment for divorce (including separation period)']))
                print('Gold Length of marriage till IJ: ' + str(gold_standard[case[:-5]]['Length of marriage till IJ (include separation period)']))
                row_score += ['0/1']
            row_data += [generated_data[case]['Length of marriage till Interim Judgment for divorce (including separation period)']]
        else:
            formatting_errors += 1
            row_data += ['Key error']
            row_score += ['0/1']
            print('Length of marriage till Interim Judgment for divorce (including separation period) key not found')
        if 'Length of marriage (exclude separation period)' in generated_data[case].keys():
            if str(generated_data[case]['Length of marriage (exclude separation period)']).lower() in str(gold_standard[case[:-5]]['Length of marriage (exclude separation period)']).lower() or str(gold_standard[case[:-5]]['Length of marriage (exclude separation period)']).lower() in str(generated_data[case]['Length of marriage (exclude separation period)']).lower():
                score += 1
                row_score += ['1/1']
            elif str(generated_data[case]['Length of marriage (exclude separation period)']).lower() == 'undisclosed' and (str(gold_standard[case[:-5]]['Length of marriage (exclude separation period)']).lower() == 'na' or str(gold_standard[case[:-5]]['Length of marriage (exclude separation period)']).lower() == 'nan' or str(gold_standard[case[:-5]]['Length of marriage (exclude separation period)']).lower() == 'n.a.'):
                score += 1
                row_score += ['1/1']
            else:
                print('Extracted Length of marriage: ' + str(generated_data[case]['Length of marriage (exclude separation period)']))
                print('Gold Length of marriage: ' + str(gold_standard[case[:-5]]['Length of marriage (exclude separation period)']))
                row_score += ['0/1']
            row_data += [generated_data[case]['Length of marriage (exclude separation period)']]
        else:
            formatting_errors += 1
            row_data += ['Key error']
            row_score += ['0/1']
            print('Length of marriage till Interim Judgment for divorce (excluding separation period) key not found')
        if 'Number of children' in generated_data[case].keys():
            if str(generated_data[case]['Number of children']).lower() in str(gold_standard[case[:-5]]['Number of children']).lower() or str(gold_standard[case[:-5]]['Number of children']).lower() in str(generated_data[case]['Number of children']).lower():
                score += 1
                row_score += ['1/1']
            elif str(generated_data[case]['Number of children']).lower() == 'undisclosed' and (str(gold_standard[case[:-5]]['Number of children']).lower() == 'na' or str(gold_standard[case[:-5]]['Number of children']).lower() == 'nan' or str(gold_standard[case[:-5]]['Number of children']).lower() == 'n.a.'):
                score += 1
                row_score += ['1/1']
            else:
                print('Extracted Number of children: ' + str(generated_data[case]['Number of children']))
                print('Gold Number of children: ' + str(gold_standard[case[:-5]]['Number of children']))
                row_score += ['0/1']
            row_data += [generated_data[case]['Number of children']]
        else:
            formatting_errors += 1
            row_data += ['Key error']
            row_score += ['0/1']
            print('Number of children key not found')
        if 'Wife\'s income (monthly)' in generated_data[case].keys():
            if str(generated_data[case]["Wife's income (monthly)"]).lower() in str(gold_standard[case[:-5]]["Wife's income (monthly)"]).lower() or str(gold_standard[case[:-5]]["Wife's income (monthly)"]).lower() in str(generated_data[case]["Wife's income (monthly)"]).lower():
                score += 1
                row_score += ['1/1']
            elif str(generated_data[case]["Wife's income (monthly)"]).lower() == 'undisclosed' and (str(gold_standard[case[:-5]]["Wife's income (monthly)"]).lower() == 'na' or str(gold_standard[case[:-5]]["Wife's income (monthly)"]).lower() == 'nan' or str(gold_standard[case[:-5]]["Wife's income (monthly)"]).lower() == 'n.a.'):
                score += 1
                row_score += ['1/1']
            else:
                print('Extracted Wife\'s income: ' + str(generated_data[case]["Wife's income (monthly)"]))
                print('Gold Wife\'s income: ' + str(gold_standard[case[:-5]]["Wife's income (monthly)"]))
                row_score += ['0/1']
            row_data += [generated_data[case]["Wife's income (monthly)"]]
        else:
            formatting_errors += 1
            row_data += ['Key error']
            row_score += ['0/1']
            print('Wife\'s income (monthly) key not found')
        if 'Husband\'s income (monthly)' in generated_data[case].keys():
            if str(generated_data[case]["Husband's income (monthly)"]).lower() in str(gold_standard[case[:-5]]["Husband's income (monthly)"]).lower() or str(gold_standard[case[:-5]]["Husband's income (monthly)"]).lower() in str(generated_data[case]["Husband's income (monthly)"]).lower():
                score += 1
                row_score += ['1/1']
            elif str(generated_data[case]["Husband's income (monthly)"]).lower() == 'undisclosed' and (str(gold_standard[case[:-5]]["Husband's income (monthly)"]).lower() == 'na' or str(gold_standard[case[:-5]]["Husband's income (monthly)"]).lower() == 'nan' or str(gold_standard[case[:-5]]["Husband's income (monthly)"]).lower() == 'n.a.'):
                score += 1
                row_score += ['1/1']
            else:
                print('Extracted Husband\'s income: ' + str(generated_data[case]["Husband's income (monthly)"]))
                print('Gold Husband\'s income: ' + str(gold_standard[case[:-5]]["Husband's income (monthly)"]))
                row_score += ['0/1']
            row_data += [generated_data[case]["Husband's income (monthly)"]]
        else:
            formatting_errors += 1
            row_data += ['Key error']
            row_score += ['0/1']
            print('Husband\'s income (monthly) key not found')
        if 'Single or dual income marriage' in generated_data[case].keys():
            if str(generated_data[case]["Single or dual income marriage"]).lower() in str(gold_standard[case[:-5]]["Single or dual income marriage"]).lower() or str(gold_standard[case[:-5]]["Single or dual income marriage"]).lower() in str(generated_data[case]["Single or dual income marriage"]).lower():
                score += 1
                row_score += ['1/1']
            elif str(generated_data[case]["Single or dual income marriage"]).lower() == 'undisclosed' and (str(gold_standard[case[:-5]]["Single or dual income marriage"]).lower() == 'na' or str(gold_standard[case[:-5]]["Single or dual income marriage"]).lower() == 'nan' or str(gold_standard[case[:-5]]["Single or dual income marriage"]).lower() == 'n.a.'):
                score += 1
                row_score += ['1/1']
            else:
                print('Extracted Single or dual income marriage: ' + str(generated_data[case]["Single or dual income marriage"]))
                print('Gold Single or dual income marriage: ' + str(gold_standard[case[:-5]]["Single or dual income marriage"]))
                row_score += ['0/1']
            row_data += [generated_data[case]["Single or dual income marriage"]]
        else:
            formatting_errors += 1
            row_data += ['Key error']
            row_score += ['0/1']
            print('Single or dual income marriage key not found')
        if 'Direct contribution (Wife)' in generated_data[case].keys():
            if str(generated_data[case]["Direct contribution (Wife)"]).lower() in str(gold_standard[case[:-5]]["Direct contribution (Wife)"]).lower() or str(gold_standard[case[:-5]]["Direct contribution (Wife)"]).lower() in str(generated_data[case]["Direct contribution (Wife)"]).lower():
                score += 1
                row_score += ['1/1']
            elif str(generated_data[case]["Direct contribution (Wife)"]).lower() == 'undisclosed' and (str(gold_standard[case[:-5]]["Direct contribution (Wife)"]).lower() == 'na' or str(gold_standard[case[:-5]]["Direct contribution (Wife)"]).lower() == 'nan' or str(gold_standard[case[:-5]]["Direct contribution (Wife)"]).lower() == 'n.a.'):
                score += 1
                row_score += ['1/1']
            else:
                print('Extracted Direct contribution: ' + str(generated_data[case]["Direct contribution (Wife)"]))
                print('Gold Direct contribution: ' + str(gold_standard[case[:-5]]["Direct contribution (Wife)"]))
                row_score += ['0/1']
            row_data += [generated_data[case]["Direct contribution (Wife)"]]
        else:
            formatting_errors += 1
            row_data += ['Key error']
            row_score += ['0/1']
            print('Direct contribution (Wife) key not found')
        if 'Indirect contribution (Wife)' in generated_data[case].keys():
            if str(generated_data[case]["Indirect contribution (Wife)"]).lower() in str(gold_standard[case[:-5]]["Indirect contribution (Wife)"]).lower() or str(gold_standard[case[:-5]]["Indirect contribution (Wife)"]).lower() in str(generated_data[case]["Indirect contribution (Wife)"]).lower():
                score += 1
                row_score += ['1/1']
            elif str(generated_data[case]["Indirect contribution (Wife)"]).lower() == 'undisclosed' and (str(gold_standard[case[:-5]]["Indirect contribution (Wife)"]).lower() == 'na' or str(gold_standard[case[:-5]]["Indirect contribution (Wife)"]).lower() == 'nan' or str(gold_standard[case[:-5]]["Indirect contribution (Wife)"]).lower() == 'n.a.'):
                score += 1
                row_score += ['1/1']
            else:
                print('Extracted Indirect contribution: ' + str(generated_data[case]["Indirect contribution (Wife)"]))
                print('Gold Indirect contribution: ' + str(gold_standard[case[:-5]]["Indirect contribution (Wife)"]))
                row_score += ['0/1']
            row_data += [generated_data[case]["Indirect contribution (Wife)"]]
        else:
            formatting_errors += 1
            row_data += ['Key error']
            row_score += ['0/1']
            print('Indirect contribution (Wife) key not found')
        if 'Average ratio (Wife)' in generated_data[case].keys():
            if str(generated_data[case]["Average ratio (Wife)"]).lower() in str(gold_standard[case[:-5]]["Average ratio (Wife)"]).lower() or str(gold_standard[case[:-5]]["Average ratio (Wife)"]).lower() in str(generated_data[case]["Average ratio (Wife)"]).lower():
                score += 1
                row_score += ['1/1']
            elif str(generated_data[case]["Average ratio (Wife)"]).lower() == 'undisclosed' and (str(gold_standard[case[:-5]]["Average ratio (Wife)"]).lower() == 'na' or str(gold_standard[case[:-5]]["Average ratio (Wife)"]).lower() == 'nan' or str(gold_standard[case[:-5]]["Average ratio (Wife)"]).lower() == 'n.a.'):
                score += 1
                row_score += ['1/1']
            else:
                print('Extracted Average ratio: ' + str(generated_data[case]["Average ratio (Wife)"]))
                print('Gold Average ratio: ' + str(gold_standard[case[:-5]]["Average ratio (Wife)"]))
                row_score += ['0/1']
            row_data += [generated_data[case]["Average ratio (Wife)"]]
        else:
            formatting_errors += 1
            row_data += ['Key error']
            row_score += ['0/1']
            print('Average ratio (Wife) key not found')
        if 'Final ratio (post-adjustments)' in generated_data[case].keys():
            if str(generated_data[case]["Final ratio (post-adjustments)"]).lower() in str(gold_standard[case[:-5]]["Final ratio (post-adjustments)"]).lower() or str(gold_standard[case[:-5]]["Final ratio (post-adjustments)"]).lower() in str(generated_data[case]["Final ratio (post-adjustments)"]).lower():
                score += 1
                row_score += ['1/1']
            elif str(generated_data[case]["Final ratio (post-adjustments)"]).lower() == 'undisclosed' and (str(gold_standard[case[:-5]]["Final ratio (post-adjustments)"]).lower() == 'na' or str(gold_standard[case[:-5]]["Final ratio (post-adjustments)"]).lower() == 'nan' or str(gold_standard[case[:-5]]["Final ratio (post-adjustments)"]).lower() == 'n.a.'):
                score += 1
                row_score += ['1/1']
            else:
                print('Extracted Final ratio: ' + str(generated_data[case]["Final ratio (post-adjustments)"]))
                print('Gold Final ratio: ' + str(gold_standard[case[:-5]]["Final ratio (post-adjustments)"]))
                row_score += ['0/1']
            row_data += [generated_data[case]["Final ratio (post-adjustments)"]]
        else:
            formatting_errors += 1
            row_data += ['Key error']
            row_score += ['0/1']
            print('Final ratio (post-adjustments) key not found')
        if 'Adjustments were for' in generated_data[case].keys():
            row_data += [generated_data[case]["Adjustments were for"]]
            is_similar = gpt4_api_call(gold_standard[case[:-5]]["Adjustments were for"], generated_data[case]["Adjustments were for"])
            if is_similar[0] == 'True':
                score += 1
                row_score += ['1/1']
            else:
                print('Extracted Adjustments were for: ' + str(generated_data[case]["Adjustments were for"]))
                print('Gold Adjustments were for: ' + str(gold_standard[case[:-5]]["Adjustments were for"]))
                print(is_similar)
                row_score += ['0/1']
        else:
            formatting_errors += 1
            row_data += ['Key error']
            row_score += ['0/1']
            print('Adjustments were for key not found')
        row_score[0] = 'Score: ' + str(score) + '/11'
        print(row_data)
        print(row_score)
        print(len(row_score))
        print(len(row_data))
        df.loc[len(df)] = [case[:-5], 'Gold Standard', gold_standard[case[:-5]]['Length of marriage till IJ (include separation period)'], gold_standard[case[:-5]]['Length of marriage (exclude separation period)'], gold_standard[case[:-5]]['Number of children'], gold_standard[case[:-5]]["Wife's income (monthly)"], gold_standard[case[:-5]]["Husband's income (monthly)"], gold_standard[case[:-5]]["Single or dual income marriage"], gold_standard[case[:-5]]["Direct contribution (Wife)"], gold_standard[case[:-5]]["Indirect contribution (Wife)"], gold_standard[case[:-5]]["Average ratio (Wife)"], gold_standard[case[:-5]]["Final ratio (post-adjustments)"], gold_standard[case[:-5]]["Adjustments were for"]]
        df.loc[len(df)] = row_data
        df.loc[len(df)] = row_score
        print(f'{case[:-5]} score: {score}/11')
        total_score += score
        print('\n')
        df.loc[len(df)] = ['','','','','','','','','','','','','']

    else:
        print(f'{case[:-5]} not found in gold standard')
        if 'Length of marriage till Interim Judgment for divorce (including separation period)' in generated_data[case].keys():
            lomtij = generated_data[case]['Length of marriage till Interim Judgment for divorce (including separation period)']
        else:
            lomtij = 'Key error'
        if 'Length of marriage (exclude separation period)' in generated_data[case].keys():
            lom = generated_data[case]['Length of marriage (exclude separation period)']
        else:
            lom = 'Key error'
        if 'Number of children' in generated_data[case].keys():
            noc = generated_data[case]['Number of children']
        else:
            noc = 'Key error'
        if "Wife's income (monthly)" in generated_data[case].keys():
            wi = generated_data[case]["Wife's income (monthly)"]
        else:
            wi = 'Key error'
        if "Husband's income (monthly)" in generated_data[case].keys():
            hi = generated_data[case]["Husband's income (monthly)"]
        else:
            hi = 'Key error'
        if "Single or dual income marriage" in generated_data[case].keys():
            sdim = generated_data[case]["Single or dual income marriage"]
        else:
            sdim = 'Key error'
        if "Direct contribution (Wife)" in generated_data[case].keys():
            dcw = generated_data[case]["Direct contribution (Wife)"]
        else:
            dcw = 'Key error'
        if "Indirect contribution (Wife)" in generated_data[case].keys():
            icw = generated_data[case]["Indirect contribution (Wife)"]
        else:
            icw = 'Key error'
        if "Average ratio (Wife)" in generated_data[case].keys():
            arw = generated_data[case]["Average ratio (Wife)"]
        else:
            arw = 'Key error'
        if "Final ratio (post-adjustments)" in generated_data[case].keys():
            frpa = generated_data[case]["Final ratio (post-adjustments)"]
        else:
            frpa = 'Key error'
        if "Adjustments were for" in generated_data[case].keys():
            awf = generated_data[case]["Adjustments were for"]
        else:
            awf = 'Key error'
        not_found.append([case[:-5], 'Extracted data', lomtij, lom, noc, wi, hi, sdim, dcw, icw, arw, frpa, awf])

df.loc[len(df)] = ['Total score:', str(total_score) + '/' + str(cases_matched*11),'','','','','','','','','','','']
print('\n')
print(f'Total score: {total_score}/{cases_matched*11}')
print(f'Formatting errors: {formatting_errors}')

df.loc[len(df)] = ['','','','','','','','','','','','','']
df.loc[len(df)] = ['Cases not found in given data:','','','','','','','','','','','','']
for case in not_found:
    df.loc[len(df)] = case

with pd.ExcelWriter('results.xlsx', mode='a') as writer:
    df.to_excel(writer, sheet_name='')