def is_job_title(line):
    common_identifiers = ["engineer", "developer", "manager", "analyst", "consultant", "specialist", "senior", "junior", "lead", "principal", "assistant", "associate", "executive", "director", "head", "chief", "vp", "vice president", "informatician"]
    line = line.lower()
    return any(identifier in line for identifier in common_identifiers)


def extract_work_experience_section(text):
    work_experience_details = []
    
    # Extract dates as before
    doc = nlp(text)
    dates = extract_dates_from_spacy(doc)

    lines = text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        company_name, job_title, date_worked, additional_details = '', '', '', []

        # Check for company name or job title
        doc_line = nlp(line)
        if any(ent.label_ == "ORG" for ent in doc_line.ents):
            company_name = line
            i += 1
        elif is_job_title(line):
            job_title = line
            i += 1

        # Continue the loop to fetch corresponding company or job title and date worked
        while i < len(lines) and not date_worked:
            line = lines[i].strip()
            doc_line = nlp(line)

            if not company_name and any(ent.label_ == "ORG" for ent in doc_line.ents):
                company_name = line
            elif not job_title and is_job_title(line):
                job_title = line
            elif any(ent.label_ == "DATE" for ent in doc_line.ents) or any(date in line for date in dates):
                date_worked = line
            else:
                additional_details.append(line)

            i += 1

        # Save details
        if company_name or job_title:
            work_experience_details.append({
                'company_name': company_name,
                'job_title': job_title,
                'dates_worked': date_worked,
                'additional_info': additional_details
            })

    return work_experience_details