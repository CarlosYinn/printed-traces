import pandas as pd

df = pd.read_csv('dataset.csv')

# Strategy 1: deduplicated corpus
deduped = df[df['use_for_mallet'].astype(str).str.strip().str.lower() == 'yes'].copy()

with open('corpus_for_mallet.txt', 'w', encoding='utf-8') as f:
    for _, row in deduped.iterrows():
        text = str(row['mallet_ready_text']).replace('\n', ' ').replace('\t', ' ')
        if len(text.strip()) < 50:
            continue
        # use time_bin as label for later time-period analysis
        label = row['time_bin'] if 'time_bin' in row and str(row['time_bin']).strip() else 'unknown'
        f.write(f"{row['doc_id']}\t{label}\t{text}\n")