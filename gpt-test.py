import openai
import os
import json


openai.api_key = "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"

def get_completion(prompt, model="gpt-3.5-turbo", temperature=0): 
    messages = [{"role": "user", "content": prompt}]
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature, 
    )
    return response.choices[0].message["content"]

def save_details_to_json(details, output_file, output_directory):
    output_file_path = os.path.join(output_directory, output_file)
    with open(output_file_path, 'w', encoding='utf-8') as f:
        json.dump(details, f, indent=4)

file_path = '/Users/sarjhana/Projects/Campuzzz/CV-text-files-test/Resume - Sarjhana.txt'
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
response = get_completion(prompt)
print("response received")
save_details_to_json(response,'Resume1.json', '/Users/sarjhana/Projects/Campuzzz/CV-GPT-processed-JSON')
print("prompt executed, json saved")