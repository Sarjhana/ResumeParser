import spacy
from collections import Counter

def main():
    nlp = spacy.load("en_core_web_sm")

    # Read the contents of the all_resumes_text.txt file
    all_resumes_text_file = '/Users/sarjhana/Projects/Campuzzz/all_resumes_text.txt'
    with open(all_resumes_text_file, 'r', encoding='utf-8') as f:
        all_resumes_text = f.read()

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

    # Print the top 50 tokens
    print("Top 50 tokens:")
    for token, freq in top_50_tokens:
        print(f"{token}: {freq}")

if __name__ == "__main__":
    main()
