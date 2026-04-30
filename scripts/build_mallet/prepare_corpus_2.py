import pandas as pd

df = pd.read_csv('dataset.csv')  # or read_excel

# Full corpus: do not filter by use_for_mallet; consistently use model_text.
all_docs = df[df['relevance_tier'].notna()].copy()  # or whichever minimum filter is appropriate

with open('corpus_for_mallet_all.txt', 'w', encoding='utf-8') as f:
    for _, row in all_docs.iterrows():
        text = str(row['model_text']).replace('\n', ' ').replace('\t', ' ')
        if len(text.strip()) < 50:
            continue
        label = row.get('time_bin', 'unknown')
        f.write(f"{row['doc_id']}\t{label}\t{text}\n")
