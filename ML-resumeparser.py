import fitz  # PyMuPDF
import re
import spacy
import nltk
import phonenumbers
import pandas as pd
import os

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
        #print(f"Writing txt file for {txt_file_name}")

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

def extract_section_items(text, section_name):
    section_header = rf"\b{section_name}\b"
    section_match = re.split(section_header, text, flags=re.IGNORECASE)[-1]
    return [item.strip().lstrip('•') for item in re.split(r'\n|•', section_match) if item.strip()]

def search_for_section(page_text, section_name, section_synonyms):
    for synonym in section_synonyms:
        if re.search(rf'\b{synonym}\b', page_text, re.IGNORECASE):
            return extract_section_items(page_text, section_name)
    return []

def extract_details_from_text(text):
    nlp = spacy.load("en_core_web_sm")

    name = extract_name(nlp(text))
    email = extract_email(text)

    linkedin_regex = r'https?://(www\.)?linkedin\.com/\S+'
    github_regex = r'https?://(www\.)?github\.com/\S+'
    linkedin = extract_url(text, linkedin_regex)
    github = extract_url(text, github_regex)

    phone = extract_phone_number(text)

    section_headers = {
        'Skills': {'Skills'},
        'Education': {'Education'},
        'Work Experience': {'Work Experience', 'Experience', 'Work History'},
        # Add other possible synonyms for section headers here
    }

    skills = []
    education = []
    work_experience = []

    for section_name, section_synonyms in section_headers.items():
        if section_name == 'Skills':
            skills = search_for_section(text, section_name, section_synonyms)
        elif section_name == 'Education':
            education = search_for_section(text, section_name, section_synonyms)
        elif section_name == 'Work Experience':
            work_experience = search_for_section(text, section_name, section_synonyms)

    details = {
        'name': name,
        'email': email,
        'phone': phone,
        'skills': skills,
        'education': education,
        'work_experience': work_experience,
        'linkedin': linkedin,
        'github': github
    }
    return details

def save_details_to_csv(details, output_file, output_directory):
    df = pd.DataFrame([details])
    output_file_path = os.path.join(output_directory, output_file)
    df.to_csv(output_file_path, index=False)

def extract_named_entities(text):
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    named_entities = [(ent.text, ent.label_) for ent in doc.ents]
    return named_entities

def save_named_entities_to_file(named_entities, output_file, output_directory):
    output_file_path = os.path.join(output_directory, output_file)
    with open(output_file_path, 'w', encoding='utf-8') as f:
        for entity, label in named_entities:
            f.write(f"{entity}\t{label}\n")

def main():
    input_directory = '/Users/sarjhana/Projects/Campuzzz/CV Archive'  # Specify the directory containing the PDF files
    output_directory_txt = '/Users/sarjhana/Projects/Campuzzz/CV-text-files'  # Specify the desired output directory for text files
    output_directory_csv = '/Users/sarjhana/Projects/Campuzzz/CV-processed-csv-files'  # Specify the desired output directory for CSV files
    output_directory_entities = '/Users/sarjhana/Projects/Campuzzz/CV-named-entities'  # Specify the desired output directory for named entities

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

        # Extract named entities using spaCy
        named_entities = extract_named_entities(pdf_text)

        # Save the named entities to a separate text file
        output_file_entities = os.path.splitext(pdf_file)[0] + '_named_entities.txt'
        save_named_entities_to_file(named_entities, output_file_entities, output_directory_entities)

        # Extract details from the text using extract_details_from_text
        resume_details = extract_details_from_text(pdf_text)

        # Save the details to a CSV file
        output_file_csv = os.path.splitext(pdf_file)[0] + '_details.csv'
        #print(resume_details['education'], "------------------------")
        save_details_to_csv(resume_details, output_file_csv, output_directory_csv)

if __name__ == "__main__":
    main()
