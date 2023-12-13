import openai
import os
import json
import time

openai.api_key = ""

def get_completion(prompt, model="gpt-3.5-turbo", temperature=0): 
    messages = [{"role": "user", "content": prompt}]
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature, 
    )
    return response.choices[0].message["content"]

json_sample = {
                "name": "",
                "email": "",
                "phone": "",
                "address": "",
                "linkedin URL": "",
                "github URL": "",
                "education": [
                    {
                    "education level": "",
                    "specialization": "",
                    "university name": "",
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

def main():

    input_directory = '/Users/sarjhana/Projects/Campuzzz/CV-text-files'  
    output_directory = '/Users/sarjhana/Projects/Campuzzz/CV-GPT-processed-JSON'

    # Get a list of all PDF files in the input directory
    pdf_files = [file for file in os.listdir(input_directory) if file.endswith('.txt')]
    # Initialize a counter variable to keep track of the file number
    file_count = 0

    for pdf_file in pdf_files:
        file_count += 1
        print(f"Processing File {file_count}/{len(pdf_files)} - {pdf_file}")

        # Construct the full path of the PDF file
        txt_file_path = os.path.join(input_directory, pdf_file)

        with open(txt_file_path, 'r', encoding='utf-8') as f:
            pdf_text = f.read()
        
        prompt = f"""Extract details from the text of resume delimited by angle brackets into a JSON. For any details that are not found, use the word 'Unknown'.
                The JSON should have a similar structure to the keys delimited by triple backticks but it can have multiple entries of details in each section. 
                Education section must capture granular details where education level refers to the degree level for example Bachelors, Masters or PhD or such synonymous acronyms and specialisation refers to the major or course name.
                ```{json_sample}``` <{pdf_text}>"""

        start_time = time.time()
        response = get_completion(prompt)
        end_time = time.time()

        execution_time = end_time - start_time
        print(f"Response received in {execution_time:.2f} seconds")

        file_name = os.path.splitext(pdf_file)[0] + '_processed.json'
        output_directory = '/Users/sarjhana/Projects/Campuzzz/CV-GPT-processed-JSON'
        json_file_path = os.path.join(output_directory, file_name)
        with open(json_file_path, 'w', encoding='utf-8') as f:
                f.write(response)

        print("prompt executed, json saved")

if __name__ == "__main__":
    main()
