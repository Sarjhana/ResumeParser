import openai
import os
import json
import time

openai.api_key = "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"

def get_completion(prompt, model="gpt-3.5-turbo", temperature=0): 
    messages = [{"role": "user", "content": prompt}]
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature, 
    )
    return response.choices[0].message["content"]


file_path = '/Users/sarjhana/Projects/Campuzzz/CV-text-files-test/NaveenKandagatla.txt'
with open(file_path, 'r') as file:
    text = file.read()

json_sample = {
                "name": "",
                "email": "",
                "phone": "",
                "address": "",
                "linkedin URL": "",
                "github URL": "",
                "education": [
                    {
                    "degree": "",
                    "university": "",
                    "duration": "",
                    "marks/percentage/cgpa obtained": "",
                    "additional information": "",
                    },
                ],
                "work_experience": [
                    {
                    "title": "",
                    "company": "",
                    "start_date": "",
                    "end_date": "",
                    "description": ""
                    },
                ],
                "skills": [],
                "certifications": [],
                "projects": [],
                "extracurricular_activities": [],
                }

print("Loading")

prompt = f"""Extract details from the text of resume delimited by angle brackets into a JSON. For any details that are blank or not found, use the word 'Unknown'.
                The JSON should have a similar structure to the keys delimited by triple backticks but it can have multiple entries of details in each section. 
                ```{json_sample}``` <{text}>"""

start_time = time.time()
response = get_completion(prompt)
end_time = time.time()

execution_time = end_time - start_time
print(f"Response received in {execution_time:.2f} seconds")


txt_file_name = 'NaveenKandagatla.json'
output_directory = '/Users/sarjhana/Projects/Campuzzz/CV-GPT-processed-JSON'
txt_file_path = os.path.join(output_directory, txt_file_name)
with open(txt_file_path, 'w', encoding='utf-8') as f:
        f.write(response)

print("prompt executed, json saved")