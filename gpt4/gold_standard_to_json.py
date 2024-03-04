import json
import pandas as pd

in_file = 'LAB Case Bank Division of Matrimonial Assets (October 2021).xlsx - Sheet1.csv'
out_file = 'gold_standard.json'

gold_standard = {}

with open(in_file, 'r', encoding='utf-8') as load_file:
    df = pd.read_csv(load_file)
for i in range(3,len(df),2):
    if type(df['Citation'][i]) == str:
        citation = df['Citation'][i].replace(' ','_').replace('[','').replace(']','')
        gold_standard[citation] = {
            'Length of marriage till IJ (include separation period)': df.loc[i]['Length of marriage till IJ (include separation period)'],
            'Length of marriage (exclude separation period)': df.loc[i]['Length of marriage (exclude separation period)'],
            'Number of children': df.loc[i]['Number of children'],
            'Wife\'s income (monthly)': df.loc[i]['Wife\'s income (monthly)'],
            'Husband\'s income (monthly)': df.loc[i]['Husband\'s income (monthly)'],
            'Single or dual income marriage': df.loc[i]['Single or dual income marriage'],
            'Direct contribution (Wife)': df.loc[i]['Direct contri (Wife)'],
            'Indirect contribution (Wife)': df.loc[i]['Indirect contri (Wife)'],
            'Average ratio (Wife)': df.loc[i]['Average ratio (Wife)'],
            'Final ratio (post-adjustments)': df.loc[i]['Final ratio (post-adjustments)'],
            'Adjustments were for': df.loc[i]['Adjustments were for']
        }

with open(out_file, 'w') as save_file:
    json.dump(gold_standard, save_file)

