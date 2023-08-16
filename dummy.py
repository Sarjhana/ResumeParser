import openai

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

print(text)

prompt = f"""Extract details from the text of resume delimited by angle brackets into a JSON. For any details that are blank or not found, use the word 'Unknown'.
                The JSON should have the following keys. 
                {
                    "personal_info": {
                        "name": "",
                        "email": "",
                        "phone": "",
                        "address": ""
                    },
                    "education": [
                        {
                        "degree": "",
                        "university": "",
                        "graduation_year": ""
                        },
                        {
                        "degree": "",
                        "university": "",
                        "graduation_year": ""
                        }
                    ],
                    "work_experience": [
                        {
                        "title": "",
                        "company": "",
                        "start_date": "",
                        "end_date": "",
                        "description": ""
                        },
                        {
                        "title": "",
                        "company": "",
                        "start_date": "",
                        "end_date": "",
                        "description": ""
                        }
                    ],
                    "skills": [],
                    "certifications": [],
                    "projects": [],
                    "extracurricular_activities": [],
                    }

                
                
                <{text}>"""
response = get_completion(prompt)
save_details_to_json(response,'Resume1.json', '/Users/sarjhana/Projects/Campuzzz/CV-GPT-processed-JSON')




prompt = f"""Extract details from the text of resume delimited by angle brackets into a JSON. The details that need to be extracted are: 
                Name, Phone number, email address, linkedin URL, github URL, work experience, education, skills, projects, extracurricular activities, certifications.
                For any details that are blank or not found, use the word 'Unknown' <{text}>"""