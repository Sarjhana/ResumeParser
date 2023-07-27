import fitz  # PyMuPDF
import re
import spacy
import nltk
import phonenumbers
import pandas as pd

from nltk.corpus import wordnet

# Download the NLTK wordnet data (if not already downloaded)
nltk.download('wordnet')

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

def extract_details_from_resume(pdf_path):
    nlp = spacy.load("en_core_web_sm")
    pdf_document = fitz.open(pdf_path)

    name = ""
    email = ""
    phone = ""
    skills = []
    education = []
    work_experience = []
    linkedin = ""
    github = ""

    linkedin_regex = r'https?://(www\.)?linkedin\.com/\S+'
    github_regex = r'https?://(www\.)?github\.com/\S+'
    
    section_headers = {
        'Skills': {'Skills'},
        'Education': {'Education'},
        'Work Experience': {'Work Experience', 'Experience', 'Work History'},
        # Add other possible synonyms for section headers here
    }

    for page_num in range(pdf_document.page_count):
        page = pdf_document.load_page(page_num)
        text = page.get_text()
        doc = nlp(text)

        if not name:
            name = extract_name(doc)
        if not email:
            email = extract_email(text)
        if not linkedin:
            linkedin = extract_url(text, linkedin_regex)
        if not github:
            github = extract_url(text, github_regex)
        if not phone:
            phone = extract_phone_number(text)

        # Check for section headers and update the current section accordingly
        current_section = None
        for section_name, section_synonyms in section_headers.items():
            for synonym in section_synonyms:
                if re.search(rf'\b{synonym}\b', text, re.IGNORECASE):
                    current_section = section_name
                    break
            if current_section is not None:
                break

        if current_section == "Education":
            # Extract education details from the current page
            education.extend(extract_section_items(text, 'Education'))
            print("Education on page", page_num, ":", extract_section_items(text, 'Education'))

        elif current_section == "Work Experience":
            work_experience.extend(extract_section_items(text, 'Work Experience'))
            print("Work Experience on page", page_num, ":", extract_section_items(text, 'Work Experience'))

        # Add handling for other sections (e.g., "Skills") here

    pdf_document.close()

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

# Example usage:
resume_path = '/Users/sarjhana/Desktop/CV:Resume/NaveenKandagatla.pdf'
resume_details = extract_details_from_resume(resume_path)

df = pd.DataFrame([resume_details])
df.to_csv('resume_details.csv', index=False)
print(df['education'].values)
