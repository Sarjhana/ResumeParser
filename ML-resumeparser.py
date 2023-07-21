import fitz  # PyMuPDF
import re
import spacy
import nltk
import phonenumbers
import pandas as pd

from nltk.corpus import wordnet

# Download the NLTK wordnet data (if not already downloaded)
nltk.download('wordnet')

def extract_details_from_resume(pdf_path):
    nlp = spacy.load("en_core_web_sm")

    # Open the PDF file using PyMuPDF
    pdf_document = fitz.open(pdf_path)

    # Initialize variables to store extracted details
    name = ""
    email = ""
    phone = ""
    skills = []
    education = []
    work_experience = []

    # Loop through each page in the PDF
    for page_num in range(pdf_document.page_count):
        # Extract text from the page
        page = pdf_document.load_page(page_num)
        text = page.get_text()

        # Use spaCy NER for named entity extraction
        doc = nlp(text)

        # Extract name using spaCy NER
        for ent in doc.ents:
            if ent.label_ == "PERSON" and not name:
                name = ent.text.strip()
                break

        # Regular expression for extracting email
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        if email_match:
            email = email_match.group()

        # Robust phone number extraction using phonenumbers library
        for match in phonenumbers.PhoneNumberMatcher(text, "US"):
            phone_number = phonenumbers.format_number(match.number, phonenumbers.PhoneNumberFormat.E164)
            if phone_number:
                phone = phone_number
                break

        # Keyword matching for extracting skills, education, and work experience
        if re.search(r'\bSkills\b', text, re.IGNORECASE):
            skills_section = re.split(r'\bSkills\b', text, flags=re.IGNORECASE)[-1]
            skills = [skill.strip().lstrip('•') for skill in re.split(r'\n|•', skills_section) if skill.strip()]

        if re.search(r'\bEducation\b', text, re.IGNORECASE):
            education_section = re.split(r'\bEducation\b', text, flags=re.IGNORECASE)[-1]
            education = [edu.strip().lstrip('•') for edu in re.split(r'\n|•', education_section) if edu.strip()]

        if re.search(r'\bWork Experience\b', text, re.IGNORECASE):
            work_experience_section = re.split(r'\bWork Experience\b', text, flags=re.IGNORECASE)[-1]
            work_experience = [exp.strip().lstrip('•') for exp in re.split(r'\n|•', work_experience_section) if exp.strip()]

    # Close the PDF document
    pdf_document.close()

    # Return the extracted details as a dictionary
    details = {
        'name': name,
        'email': email,
        'phone': phone,
        'skills': skills,
        'education': education,
        'work_experience': work_experience
    }
    return details

# Example usage:
resume_path = '/Users/sarjhana/Desktop/CV:Resume/NaveenKandagatla.pdf'
resume_details = extract_details_from_resume(resume_path)

# Convert the details to a Pandas DataFrame
df = pd.DataFrame([resume_details])

# Save the DataFrame to a CSV file
df.to_csv('resume_details.csv', index=False)

# Print the DataFrame
print(df)
