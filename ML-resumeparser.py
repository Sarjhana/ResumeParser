import fitz  # PyMuPDF
import re
import spacy
import nltk
import phonenumbers
import pandas as pd
import os
import json

from nltk.corpus import wordnet

# Download the NLTK wordnet data (if not already downloaded)
nltk.download('wordnet')

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
    return ""

def extract_email(text):
    email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
    if email_match:
        return email_match.group()
    return ""

def extract_url(text, regex):
    url_match = re.search(regex, text)
    if url_match:
        return url_match.group()
    return ""

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

def extract_education_section(text):
    nlp = spacy.load("en_core_web_sm")
    education_details = []

    # Education section identification
    education_section_pattern = r'(?i)(?:Education|Academic Qualifications|Educational Background)(.*?)(?:(?:Experience|Work Experience|Professional Experience)|$)'
    education_section_match = re.search(education_section_pattern, text, re.DOTALL)
    print(education_section_match, "eve")

    if education_section_match:
        education_section_text = education_section_match.group(1)

        # Education information extraction using regex
        doc = nlp(education_section_text)

        # Extract dates from spaCy entities
        dates = extract_dates_from_spacy(doc)

        # Education information extraction using regex
        education_pattern = r'(?P<university_name>[^\n-]+)\s*-?\s*(?P<course_name>[^\n-]+)?(?:\s*-\s*(?P<dates_attended>[^\n-]+))?(?:\s*-\s*(?P<marks_or_percentage>[^\n-]+))?(?:\s*-\s*(?P<additional_info>[^\n-]+))?'

        for match in re.finditer(education_pattern, education_section_text):
            university_name = match.group('university_name').strip() if match.group('university_name') else ''
            course_name = match.group('course_name').strip() if match.group('course_name') else ''
            dates_attended = match.group('dates_attended').strip() if match.group('dates_attended') else ''
            marks_or_percentage = match.group('marks_or_percentage').strip() if match.group('marks_or_percentage') else ''
            additional_info = match.group('additional_info').strip() if match.group('additional_info') else ''

            if not dates_attended:
                # If dates_attended is not found using regex, use dates extracted from spaCy entities in order
                dates_attended = dates.pop(0) if dates else ''

            education_details.append({
                'university_name': university_name,
                'course_name': course_name,
                'dates_attended': dates_attended,
                'marks_or_percentage': marks_or_percentage,
                'additional_info': additional_info
            })

    return education_details

def extract_work_experience_section(text):
    work_experience_details = []

    # Work Experience section identification
    work_experience_section_pattern = r'(?i)(?:Work Experience|Experience|Professional Experience)(.*?)(?:Education|Academic Qualifications|$)'
    work_experience_section_match = re.search(work_experience_section_pattern, text)

    if work_experience_section_match:
        work_experience_section_text = work_experience_section_match.group(1)

        # Work experience information extraction using regex
        work_experience_pattern = r'(\d{4})\s*-\s*(\d{4}|Present)?\s*:\s*(.*?)(?:\s*-\s*(.*?))?(?:\s*-\s*(.*?))?(?:\s*-\s*(.*?))?\s*(?:-|$)'
        work_experience_matches = re.findall(work_experience_pattern, work_experience_section_text)

        for match in work_experience_matches:
            start_year, end_year, title, company, location, description = match
            work_experience_details.append({
                'start_year': int(start_year),
                'end_year': int(end_year) if end_year and end_year.lower() != 'present' else 'Present',
                'title': title.strip(),
                'company': company.strip(),
                'location': location.strip(),
                'description': description.strip()
            })
        print(work_experience_details, "----")
    return work_experience_details


def extract_details_from_text(text):
    nlp = spacy.load("en_core_web_sm")

    name = extract_name(nlp(text))
    email = extract_email(text)

    linkedin_regex = r'https?://(www\.)?linkedin\.com/\S+'
    github_regex = r'https?://(www\.)?github\.com/\S+'
    linkedin = extract_url(text, linkedin_regex)
    github = extract_url(text, github_regex)

    phone = extract_phone_number(text)

    education_details = extract_education_section(text)
    work_experience_details = extract_work_experience_section(text)

    section_headers = {
        'Skills': {'Skills'},
        #'Education': {'Education'},
        #'Work Experience': {'Work Experience', 'Experience', 'Work History'},
        # Add other possible synonyms for section headers here
    }

    skills = []
    #education = []
    #work_experience = []

    for section_name, section_synonyms in section_headers.items():
        if section_name == 'Skills':
            skills = search_for_section(text, section_name, section_synonyms)
        #elif section_name == 'Work Experience':
            #work_experience = search_for_section(text, section_name, section_synonyms)

    details = {
        'name': name,
        'email': email,
        'phone': phone,
        'skills': skills,
        'education': education_details,
        'work_experience': work_experience_details,
        'linkedin': linkedin,
        'github': github
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
    input_directory = '/Users/sarjhana/Projects/Campuzzz/CV Archive'  # Specify the directory containing the PDF files
    output_directory_txt = '/Users/sarjhana/Projects/Campuzzz/CV-text-files'  # Specify the desired output directory for text files
    output_directory_csv = '/Users/sarjhana/Projects/Campuzzz/CV-processed-csv-files'  # Specify the desired output directory for CSV files
    output_directory_json = '/Users/sarjhana/Projects/Campuzzz/CV-processed-json-files' # Specify the desired output directory for JSON files
    
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
        # Extract details from the text using extract_details_from_text
        resume_details = extract_details_from_text(pdf_text)
        print(resume_details['education'])

        # Save the details to a CSV file
        output_file = os.path.splitext(pdf_file)[0] + '_details.csv'
        save_details_to_csv(resume_details, output_file, output_directory_csv)

        # Save the details to a JSON file
        output_file = os.path.splitext(pdf_file)[0] + '_details.json'
        save_details_to_json(resume_details, output_file, output_directory_json)

if __name__ == "__main__":
    main()
