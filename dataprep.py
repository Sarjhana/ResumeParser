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

def extract_details_from_text(text):

    name = extract_name(nlp(text))
    email = extract_email(text)

    linkedin_url = extract_linkedin_url(text)
    github_url = extract_github_url(text)

    phone = extract_phone_number(text)


    details = {
        'name': name,
        'email': email,
        'phone': phone,
        'linkedin': linkedin_url,
        'github': github_url,
    }
    return details


def save_details_to_json(details, output_file, output_directory):
    output_file_path = os.path.join(output_directory, output_file)
    with open(output_file_path, 'w', encoding='utf-8') as f:
        json.dump(details, f, indent=4)

def main():

    input_directory = '/Users/sarjhana/Projects/Campuzzz/Testing'  # Specify the directory containing the PDF files
    output_directory_txt = '/Users/sarjhana/Projects/Campuzzz/CV-text-files-test'  # Specify the desired output directory for text files
    output_directory_csv = '/Users/sarjhana/Projects/Campuzzz/CV-processed-csv-files-test'  # Specify the desired output directory for CSV files
    output_directory_json = '/Users/sarjhana/Projects/Campuzzz/CV-processed-json-files-test' # Specify the desired output directory for JSON files
    
    '''
    input_directory = '/Users/sarjhana/Projects/Campuzzz/CV Archive'  # Specify the directory containing the PDF files
    output_directory_txt = '/Users/sarjhana/Projects/Campuzzz/CV-text-files'  # Specify the desired output directory for text files
    output_directory_csv = '/Users/sarjhana/Projects/Campuzzz/CV-processed-csv-files'  # Specify the desired output directory for CSV files
    output_directory_json = '/Users/sarjhana/Projects/Campuzzz/CV-processed-json-files' # Specify the desired output directory for JSON files
    '''
    
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


        # Save the details to a JSON file
        output_file = os.path.splitext(pdf_file)[0] + '_details.json'
        save_details_to_json(resume_details, output_file, output_directory_json)

if __name__ == "__main__":
    main()
