import json

with open('results.json', 'r') as load_file:
    generated_data = json.load(load_file)
with open('gold_standard.json', 'r') as load_file:
    gold_standard = json.load(load_file)

for case in generated_data:
    if case in gold_standard:
        print(generated_data[case])
        print(gold_standard[case[:-5]])
        print('\n\n\n')
    else:
        print(f'{case[:-5]} not found in gold standard')