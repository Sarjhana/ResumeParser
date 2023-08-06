import spacy
import gensim.downloader as api
from collections import Counter
import json

def load_word2vec_model():
    # Load the word2vec model (this may take some time as the model is large)
    return api.load('word2vec-google-news-300')

def find_similar_terms(word2vec_model, heading, top_n=5):
    # Get the word vector for the given heading
    try:
        heading_vector = word2vec_model[heading]
    except KeyError:
        print(f"Heading '{heading}' not found in the word2vec model.")
        return []

    # Find similar words using word embeddings
    similar_terms = word2vec_model.similar_by_vector(heading_vector, topn=top_n+1)
    similar_terms = [(word, similarity) for word, similarity in similar_terms if word != heading]

    return similar_terms

def process_resume_text(all_resumes_text):
    nlp = spacy.load("en_core_web_sm")

    # Process the text in smaller chunks using spaCy
    chunk_size = 100000  # Adjust this value as needed
    num_chunks = len(all_resumes_text) // chunk_size + 1
    tokens_counter = Counter()

    for i in range(num_chunks):
        start_idx = i * chunk_size
        end_idx = (i + 1) * chunk_size
        chunk_text = all_resumes_text[start_idx:end_idx]
        doc = nlp(chunk_text)
        chunk_tokens_counter = Counter(token.text for token in doc if not token.is_stop and not token.is_punct)
        tokens_counter += chunk_tokens_counter

    # Get the top 50 most common tokens and their frequencies
    top_50_tokens = tokens_counter.most_common(50)

    return top_50_tokens

def save_top_50_tokens_to_json(top_50_tokens, education_similar_terms, work_experience_similar_terms):
    data = {
        'top_50_tokens': top_50_tokens,
        'similar_terms_education': education_similar_terms,
        'similar_terms_work_experience': work_experience_similar_terms
    }
    with open('top_50_tokens.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def save_synonyms_to_txt(filename, heading, similar_terms):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"Different terms for '{heading}':\n")
        for term, similarity in similar_terms:
            f.write(f"{term}: Similarity = {similarity:.2f}\n")

def main():
    nlp = spacy.load("en_core_web_sm")

    # Read the contents of the all_resumes_text.txt file
    all_resumes_text_file = '/Users/sarjhana/Projects/Campuzzz/all_resumes_text.txt'
    with open(all_resumes_text_file, 'r', encoding='utf-8') as f:
        all_resumes_text = f.read()

    # Load word2vec model
    word2vec_model = load_word2vec_model()

    # Process the resume text
    top_50_tokens = process_resume_text(all_resumes_text)

    # Find similar terms for the heading "education"
    heading_to_find_terms_for_education = "education"
    education_similar_terms = find_similar_terms(word2vec_model, heading_to_find_terms_for_education)

    # Find similar terms for the heading "work experience"
    heading_to_find_terms_for_work_experience = "work experience"
    work_experience_similar_terms = find_similar_terms(word2vec_model, heading_to_find_terms_for_work_experience)

    # Save the top 50 tokens and similar terms to a JSON file
    save_top_50_tokens_to_json(top_50_tokens, education_similar_terms, work_experience_similar_terms)

    # Print the top 50 tokens
    print("Top 50 tokens:")
    for token, freq in top_50_tokens:
        print(f"{token}: {freq}")

    # Save synonyms for the heading "education" to a text file
    education_synonyms_file = 'education_synonyms.txt'
    save_synonyms_to_txt(education_synonyms_file, heading_to_find_terms_for_education, education_similar_terms)

    # Save synonyms for the heading "work experience" to a text file
    work_experience_synonyms_file = 'work_experience_synonyms.txt'
    save_synonyms_to_txt(work_experience_synonyms_file, heading_to_find_terms_for_work_experience, work_experience_similar_terms)

if __name__ == "__main__":
    main()
