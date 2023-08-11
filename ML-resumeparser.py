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

    # Handle and remove special characters
    full_text = full_text.replace("\u2022", " ")  # Bullet
    full_text = full_text.replace("\u25cf", " ")  # Black Circle
    full_text = full_text.replace("\u25cb", " ")  # White Circle
    full_text = full_text.replace('\u2019', "'")  # Apostrophe
    full_text = full_text.replace('\u2013', '-')  # Hyphen or Dash
    full_text = full_text.replace('\ufffd', '')   # Unknown special character

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

def extract_dates_from_regex(text):
    # Extract dates with formats like "2022 - Present", "2021 - 2023", "2021 - Now"
    return re.findall(r'\d{4} - (?:\d{4}|Present|Now)', text, re.I)

def extract_dates_from_spacy(doc):
    dates = []
    
    # Pattern to match various date formats
    date_pattern = re.compile(r'''
    (?:
        # DD/MM/YYYY or MM/DD/YYYY format
        (?:[0-2]?[0-9]|3[0-1])[/\-](?:0?[1-9]|1[0-2])[/\-]\d{4}
    )|
    (?:
        # MM/YYYY format
        (?:0?[1-9]|1[0-2])/\d{4}
    )|
    (?:
        # Month DD, YYYY format
        (?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}
    )|
    (?:
        # DD Month YYYY format
        \d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}
    )|
    (?:
        # YYYY-MM-DD format
        \d{4}[\-](?:0?[1-9]|1[0-2])[\-](?:[0-2]?[0-9]|3[0-1])
    )
    ''', re.VERBOSE)

    for ent in doc.ents:
        # Check if the entity is a date or a valid formatted cardinal
        if ent.label_ == "DATE" or (ent.label_ == "CARDINAL" and date_pattern.match(ent.text.strip())):
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
        "Education": ["Education", "Educational Background", "Academic Qualifications", "Academic details"],
        "Work Experience": ["Work Experience", "Experience", "Professional Experience", "Employment History"],
        "Projects": ["Projects", "Key Projects"],
        "Certifications":["Certifications"],
        "Extra":["Extracurricular", "Leadership", "Leadership roles and responsibilities", "Additional responsibilities", "Interests", "Hobbies", "Interests and Hobbies"]
    }

    text_lower = text.lower()
    section_indexes = []

    # Search for each variation and record the earliest index
    for main_title, variations in section_variations.items():
        for variation in variations:
            idx = text_lower.find(variation.lower())
            if idx != -1:
                section_indexes.append((main_title, idx))

    # If no sections are found, return an empty dictionary
    if not section_indexes:
        return {}

    # Sort the section titles based on their order in the text
    sorted_sections = sorted(section_indexes, key=lambda x: x[1])

    # Slice the text to extract each section
    for i in range(len(sorted_sections)):
        main_title, start_index = sorted_sections[i]
        
        # Move start index to the next line after the heading
        next_line_start = text.find('\n', start_index) + 1
        if next_line_start != -1:  # If there's a new line after the heading
            start_index = next_line_start

        end_index = sorted_sections[i + 1][1] if i + 1 < len(sorted_sections) else len(text)
        section_content = text[start_index:end_index].strip()

        # Check if the section already exists in the dictionary, if so append, otherwise set
        if main_title in sections:
            sections[main_title] += "\n" + section_content
        else:
            sections[main_title] = section_content

    return sections

def is_job_title(line):
    common_identifiers = ["engineer", "developer", "manager", "analyst", "consultant", "specialist", "senior", "junior", "lead", "principal", "assistant", "associate", "executive", "director", "head", "chief", "vp", "vice president", "informatician"]
    line = line.lower()
    return any(identifier in line for identifier in common_identifiers)

def extract_work_experience_section(text):
    work_experience_details = []

    # Extract dates from the section using both spaCy and regex
    doc = nlp(text)
    dates_spacy = extract_dates_from_spacy(doc)
    dates_regex = extract_dates_from_regex(text)
    dates = list(set(dates_spacy + dates_regex))

    lines = [line for line in text.split('\n') if line.strip()]
    i = 0

    while i < len(lines):
        company_name, job_title, date_worked, additional_details = '', '', '', []
        parsed_categories = set()

        while i < len(lines) and len(parsed_categories) < 3:  # Continue until we've found all three categories
            line = lines[i].strip()
            doc_line = nlp(line)

            if 'ORG' not in parsed_categories and any(ent.label_ == "ORG" for ent in doc_line.ents):
                company_name = line
                parsed_categories.add('ORG')
            elif 'TITLE' not in parsed_categories and is_job_title(line):
                job_title = line
                parsed_categories.add('TITLE')
            elif 'DATE' not in parsed_categories and (any(ent.label_ == "DATE" for ent in doc_line.ents) or any(date in line for date in dates)):
                date_worked = line
                parsed_categories.add('DATE')
            else:
                additional_details.append(line)

            i += 1

        if (company_name or job_title) and date_worked:
            work_experience_details.append({
                'company_name': company_name,
                'job_title': job_title,
                'dates_worked': date_worked,
                'additional_info': additional_details
            })

    return work_experience_details

def extract_education_section(text):
    education_details = []
    
    education_section_text = text
    doc = nlp(education_section_text)
    dates = extract_dates_from_spacy(doc)
    
    university_pattern = r"((?:[\w\s'’]+?(?: University| College| Institute| Institution))(?=[\s,;]|\n))"
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

    linkedin_url = extract_linkedin_url(text)
    github_url = extract_github_url(text)

    phone = extract_phone_number(text)

    sections = divide_into_sections(text)

    if 'Education' in sections:
        education_text = sections["Education"]
        education_details = extract_education_section(education_text)
    else:
        education_details = None
        
    if 'Work Experience' in sections:
        work_experience_text = sections["Work Experience"]
        work_experience_details = extract_work_experience_section(work_experience_text)
    else:
        work_experience_details = None

    if 'Skills' in sections:
        skills_text = sections["Skills"]
    else:
        skills_text = None
    
    if 'Projects' in sections:
        projects_text = sections["Projects"]
    else:
        projects_text = None

    if 'Certifications' in sections:
        certifications_text = sections["Certifications"]
    else:
        certifications_text = None

    if 'Extra' in sections:
        extra_text = sections["Extra"]
    else:
        extra_text = None


    details = {
        'name': name,
        'email': email,
        'phone': phone,
        'education': education_details,
        'work_experience': work_experience_details,
        'linkedin': linkedin_url,
        'github': github_url,
        'projects': projects_text,
        'certifications': certifications_text,
        'extra': extra_text,
        'skills': skills_text,
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
        
        resume_details = extract_details_from_text(pdf_text)

        # Save the details to a CSV file
        output_file = os.path.splitext(pdf_file)[0] + '_details.csv'
        save_details_to_csv(resume_details, output_file, output_directory_csv)

        # Save the details to a JSON file
        output_file = os.path.splitext(pdf_file)[0] + '_details.json'
        save_details_to_json(resume_details, output_file, output_directory_json)

if __name__ == "__main__":
    main()
