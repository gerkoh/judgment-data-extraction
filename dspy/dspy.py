import json
import os

from dspy_classes import DSPyBootstrapFewShot, TestSignature

in_dir = 'input/'
out_dir = 'output/'

number_of_files_processed = 0
total_number_of_files = len(os.listdir(in_dir))

example_question_list =[]
example_answer_list = []

hint = "All information must be retrieved from the given input only"

compiled_cot = DSPyBootstrapFewShot(TestSignature,hint,example_question_list,example_answer_list).compile()

print("Compiled!")

for filename in os.listdir(in_dir):
    with open(in_dir + filename, 'r') as load_file:
        data = json.load(load_file)
    number_of_files_processed += 1
    print(f'{number_of_files_processed}/{total_number_of_files} processed\n\n')
    pred = compiled_cot(question=data)
    print(pred.answer)