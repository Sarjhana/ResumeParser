import fitz  # PyMuPDF
import re
import spacy
import nltk
import phonenumbers
import pandas as pd
import os
import json
import datetime

from nltk.corpus import wordnet

# Download the NLTK wordnet data (if not already downloaded)
nltk.download('wordnet')
nlp = spacy.load("en_core_web_sm")

def pdf_to_text(pdf_path, output_directory):
    pdf_document = fitz.open(pdf_path)
    full_text = ""
    for page in pdf_document:
        full_text += page.get_text()
    pdf_document.close()

    # Generate the output .txt file name based on the PDF file name
    txt_file_name = os.path.splitext(os.path.basename(pdf_path))[0] + ".txt"

    # Save the extracted text to a new .txt file in the specified output directory
    txt_file_path = os.path.join(output_directory, txt_file_name)
    with open(txt_file_path, 'w', encoding='utf-8') as f:
        f.write(full_text)
        print(f"Writing txt file for {txt_file_name}")

    return txt_file_path

def extract_name(doc):
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text.strip()
    return "Unknown"  # Return Unknown if no name is found

def extract_email(text):
    email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
    if email_match:
        return email_match.group()
    return ""

def extract_linkedin_url(text):
    # Regular expression pattern to extract LinkedIn URLs
    linkedin_pattern = r'https?://(?:www\.)?linkedin\.com/[\w\-/]+'
    match = re.search(linkedin_pattern, text)
    return match.group(0) if match else ""

def extract_github_url(text):
    # Regular expression pattern to extract GitHub URLs
    github_pattern = r'https?://(?:www\.)?github\.com/[\w\-]+'
    match = re.search(github_pattern, text)
    return match.group(0) if match else ""

def extract_phone_number(text):
    for match in phonenumbers.PhoneNumberMatcher(text, "US"):
        phone_number = phonenumbers.format_number(match.number, phonenumbers.PhoneNumberFormat.E164)
        if phone_number:
            return phone_number
    return ""

def extract_dates_from_spacy(doc):
    dates = []
    for ent in doc.ents:
        if ent.label_ == "DATE":
            dates.append(ent.text.strip())
    return dates

def extract_section_items(text, section_name):
    section_header = rf"\b{section_name}\b"
    section_match = re.split(section_header, text, flags=re.IGNORECASE)[-1]
    return [item.strip().lstrip('•') for item in re.split(r'\n|•', section_match) if item.strip()]

def search_for_section(page_text, section_name, section_synonyms):
    for synonym in section_synonyms:
        if re.search(rf'\b{synonym}\b', page_text, re.IGNORECASE):
            return extract_section_items(page_text, section_name)
    return []

def extract_start_end_years(years_range):
    if 'Present' in years_range:
        end_year = datetime.datetime.now().year
    else:
        end_year = None

    year_parts = re.findall(r'(\d{4}|\d{2}-\d{4})', years_range)
    
    start_year = int(year_parts[0].split('-')[0]) if year_parts else None
    if not end_year:
        end_year = int(year_parts[0].split('-')[-1]) if year_parts else None

    return start_year, end_year

def divide_into_sections(text):
    sections = {}
    
    # Each main section has its possible variations
    section_variations = {
        "Skills": ["Skills", "Technical Skills", "Key Skills"],
        "Education": ["Education", "Educational Background", "Academic Qualifications"],
        "Work Experience": ["Work Experience", "Experience", "Professional Experience"],
        "Projects": ["Projects", "Key Projects"],
        "Certifications":["Certifications"],
        "Extra":["Extracurricular", "Leadership", "Leadership roles and responsibilities", "Additional responsibilities"]
    }

    text_lower = text.lower()
    section_indexes = {}

    # Search for each variation and keep the earliest index
    for main_title, variations in section_variations.items():
        for variation in variations:
            idx = text_lower.find(variation.lower())
            if idx != -1:
                # If the section title hasn't been found yet or a new earlier index is found, update
                if main_title not in section_indexes or idx < section_indexes[main_title]:
                    section_indexes[main_title] = idx

    # If no sections are found, return an empty dictionary
    if not section_indexes:
        return {}

    # Sort the section titles based on their order in the text
    sorted_titles = sorted(section_indexes, key=section_indexes.get)

    # Slice the text to extract each section
    for i in range(len(sorted_titles)):
        start_index = section_indexes[sorted_titles[i]]

        # Move start index to the next line after the heading
        next_line_start = text.find('\n', start_index) + 1
        if next_line_start != -1:  # If there's a new line after the heading
            start_index = next_line_start

        end_index = section_indexes[sorted_titles[i + 1]] if i + 1 < len(sorted_titles) else len(text)
        sections[sorted_titles[i]] = text[start_index:end_index].strip()

    return sections

def extract_dates_from_regex(text):
    # Extract dates with formats like "2022 - Present", "2021 - 2023", "2021 - Now"
    return re.findall(r'\d{4} - (?:\d{4}|Present|Now)', text, re.I)

def extract_work_experience_section(text):
    work_experience_details = []

    # Extract dates from the section using both spaCy and regex
    doc = nlp(text)
    dates_spacy = extract_dates_from_spacy(doc)
    dates_regex = extract_dates_from_regex(text)
    dates = list(set(dates_spacy + dates_regex))

    lines = text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Check with SpaCy if it's recognized as a company
        doc_line = nlp(line)
        if any(ent.label_ == "ORG" for ent in doc_line.ents):
            company_name = line

            job_title = ''
            date_worked = ''
            # Check the next line for job title or date
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                doc_next_line = nlp(next_line)
                if any(ent.label_ == "DATE" for ent in doc_next_line.ents) or any(date in next_line for date in dates):
                    date_worked = next_line
                    i += 2
                else:
                    job_title = next_line
                    # Check the line after the job title for a date
                    if i + 2 < len(lines) and (any(date in lines[i + 2] for date in dates) or any(ent.label_ == "DATE" for ent in nlp(lines[i + 2].strip()).ents)):
                        date_worked = lines[i + 2].strip()
                        i += 3
                    else:
                        i += 2

            # Gather additional details until the next company or the end of the list
            additional_details = []
            max_iterations = len(lines) * 20
            current_iterations = 0

            while i < len(lines) and current_iterations < max_iterations:
                current_iterations += 1
                additional_details.append(lines[i].strip())
                i += 1

            work_experience_details.append({
                'company_name': company_name,
                'job_title': job_title,
                'dates_worked': date_worked,
                'additional_info': additional_details
            })
        else:
            i += 1

    return work_experience_details

def extract_education_section(text):
    education_details = []
    
    education_section_text = text
    doc = nlp(education_section_text)
    dates = extract_dates_from_spacy(doc)
    
    university_pattern = r"((?:[\w\s'’]+?(?: University| College))(?=[\s,;]|\n))"
    university_matches = re.split(university_pattern, education_section_text)[1:]

    for i in range(0, len(university_matches), 2):
        uni_name = university_matches[i].strip()
        uni_section = university_matches[i+1].strip()

        course_name_pattern = r'(?i)(bachelors|b\.?a|b\.?sc|b\.?e|b\.?tech|masters|m\.?a|m\.?sc|m\.?e|m\.?tech|ph\.?d)[\w\s.&]+'
        course_match = re.search(course_name_pattern, uni_section)
        course_name = course_match.group().strip() if course_match else ''
        uni_section = uni_section.replace(course_name, "", 1).strip()

        marks_pattern = r'(\d{1,2}\.\d{1,2}/\d{1,2}|\d{1,2}%|Pass with [\w\s]+)'
        marks_match = re.search(marks_pattern, uni_section)
        marks = marks_match.group().strip() if marks_match else ''

        additional_details = [info for info in re.split(r'\s*\u25cb\s*|\s*\u25cf\s*', uni_section) if info and not info.startswith(('Github', 'LinkedIn'))]

        date_attended = dates.pop(0) if dates else ''

        education_details.append({
            'university_name': uni_name,
            'course_name': course_name,
            'dates_attended': date_attended,
            'marks_or_percentage': marks,
            'additional_info': additional_details
        })

    return education_details

def extract_details_from_text(text):

    name = extract_name(nlp(text))
    email = extract_email(text)

    linkedin_regex = r'https?://(www\.)?linkedin\.com/'
    github_regex = r'https?://(www\.)?github\.com/'
    linkedin_url = extract_linkedin_url(text)
    github_url = extract_github_url(text)

    phone = extract_phone_number(text)

    sections = divide_into_sections(text)

    if 'Education' in sections:
        education_text = sections["Education"]
        education_details = extract_education_section(education_text)
        
    if 'Work Experience' in sections:
        work_experience_text = sections["Work Experience"]
        work_experience_details = extract_work_experience_section(work_experience_text)


    details = {
        'name': name,
        'email': email,
        'phone': phone,
        #'skills': skills,
        'education': education_details,
        'work_experience': work_experience_details,
        'linkedin': linkedin_url,
        'github': github_url
    }
    return details


def save_details_to_csv(details, output_file, output_directory):
    df = pd.DataFrame([details])
    output_file_path = os.path.join(output_directory, output_file)
    df.to_csv(output_file_path, index=False)

def save_details_to_json(details, output_file, output_directory):
    output_file_path = os.path.join(output_directory, output_file)
    with open(output_file_path, 'w', encoding='utf-8') as f:
        json.dump(details, f, indent=4)

def main():
    input_directory = '/Users/sarjhana/Projects/Campuzzz/Testing'  # Specify the directory containing the PDF files
    output_directory_txt = '/Users/sarjhana/Projects/Campuzzz/CV-text-files-test'  # Specify the desired output directory for text files
    output_directory_csv = '/Users/sarjhana/Projects/Campuzzz/CV-processed-csv-files-test'  # Specify the desired output directory for CSV files
    output_directory_json = '/Users/sarjhana/Projects/Campuzzz/CV-processed-json-files-test' # Specify the desired output directory for JSON files
    
    # Create a single text file to store all the converted text
    all_text_file = '/Users/sarjhana/Projects/Campuzzz/all_resumes_text.txt'
    with open(all_text_file, 'w', encoding='utf-8') as f:
        pass  # Create an empty file

    # Get a list of all PDF files in the input directory
    pdf_files = [file for file in os.listdir(input_directory) if file.endswith('.pdf')]

    # Initialize a counter variable to keep track of the file number
    file_count = 0

    for pdf_file in pdf_files:
        file_count += 1
        print(f"Processing File {file_count}/{len(pdf_files)} - {pdf_file}")

        # Construct the full path of the PDF file
        pdf_path = os.path.join(input_directory, pdf_file)

        # Convert the PDF to text and save it as a .txt file
        txt_file_path = pdf_to_text(pdf_path, output_directory_txt)

        # Read the content of the text file
        with open(txt_file_path, 'r', encoding='utf-8') as f:
            pdf_text = f.read()
            with open(all_text_file, 'a', encoding='utf-8') as f:
                f.write(pdf_text + "\n")

        with open(txt_file_path, 'r', encoding='utf-8') as f:
            pdf_text = f.read()
        
        '''# Extract details from the text using extract_details_from_text
        sections = divide_into_sections(pdf_text)

        if 'Education' in sections:
            education_text = sections["Education"]
            print(education_text)
            education_details = extract_education_section(education_text)
        if 'Work Experience' in sections:
            work_experience_text = sections["Work Experience"]
            work_experience = extract_work_experience_section(work_experience_text)'''
        
        resume_details = extract_details_from_text(pdf_text)
        #print(resume_details['education'])

        # Save the details to a CSV file
        output_file = os.path.splitext(pdf_file)[0] + '_details.csv'
        save_details_to_csv(resume_details, output_file, output_directory_csv)

        # Save the details to a JSON file
        output_file = os.path.splitext(pdf_file)[0] + '_details.json'
        save_details_to_json(resume_details, output_file, output_directory_json)

if __name__ == "__main__":
    main()
