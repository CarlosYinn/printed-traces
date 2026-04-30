# Convert MALLET output to Gensim-readable format and evaluate topic coherence
from gensim.models import CoherenceModel
from gensim.corpora import Dictionary


def parse_mallet_keys(filepath):
    """Parse MALLET topic keys file, returning a list of word lists per topic."""
    with open(filepath, encoding='utf-8') as f:
        return [line.strip().split('\t')[2].split() for line in f]


def load_corpus_texts(filepath):
    """Load corpus as bag-of-words (tab-separated: doc_id, label, text)."""
    with open(filepath, encoding='utf-8') as f:
        return [
            parts[2].split()
            for line in f
            if len(parts := line.strip().split('\t')) >= 3
        ]


if __name__ == '__main__':
    texts = load_corpus_texts('corpus_for_mallet.txt')
    dictionary = Dictionary(texts)

    for K in [20, 25, 30]:
        for S in [1, 2, 3]:
            topics = parse_mallet_keys(f'output/keys_K{K}_S{S}.txt')
            score = CoherenceModel(
                topics=topics,
                texts=texts,
                dictionary=dictionary,
                coherence='c_v'
            ).get_coherence()
            print(f"K={K}, Seed={S}, Coherence={score:.4f}")
