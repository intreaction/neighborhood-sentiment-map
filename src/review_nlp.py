"""Executed review-text methods for the research notebook.

Runs on the 413 short review excerpts already published in
data/derived/project_evidence.json, so it needs no raw Yelp archive. The excerpts
were selected by the clause rules (area-targeted topic mentions), so they are not
a random sample of reviews.
"""
import numpy as np
import pandas as pd

EXCERPT_CHARS = 240  # build_project_evidence.py truncates excerpts to this length
EMBEDDING_MODEL = 'sentence-transformers/all-MiniLM-L6-v2'  # the Lab 4 BERTopic embedding model


def load_excerpts(evidence):
    rows = [{**e, 'project': p['project']} for p in evidence['projects'] for e in p.get('excerpts', [])]
    frame = pd.DataFrame(rows)
    frame['chars'] = frame['text'].str.len()
    frame['truncated'] = frame['chars'] >= EXCERPT_CHARS
    return frame


def star_sentiment_benchmark(excerpts, embeddings, folds=5, seed=0):
    """Predict review-level star polarity (4-5 vs 1-2 stars) from each excerpt.

    Compares VADER (Lab 2 lexicon), bag-of-words Naive Bayes (Lab 2) and logistic
    regression on BERT sentence embeddings, with a majority-class reference.
    Three-star reviews are dropped. Stars rate the whole visit, not the clause.
    """
    from sklearn.feature_extraction.text import CountVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, f1_score
    from sklearn.model_selection import StratifiedKFold, cross_val_predict
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.pipeline import make_pipeline

    keep = (excerpts['stars'] != 3).to_numpy()
    y = (excerpts.loc[keep, 'stars'] >= 4).astype(int).to_numpy()
    texts = excerpts.loc[keep, 'text'].tolist()
    cv = StratifiedKFold(folds, shuffle=True, random_state=seed)
    predictions = {
        'Majority class': np.full_like(y, int(round(y.mean()))),
        'VADER (compound ≥ 0.05)': (excerpts.loc[keep, 'vader'] >= .05).astype(int).to_numpy(),
        'Bag of words + Naive Bayes': cross_val_predict(make_pipeline(CountVectorizer(stop_words='english', min_df=2), MultinomialNB()), texts, y, cv=cv),
        'MiniLM embeddings + logistic regression': cross_val_predict(LogisticRegression(max_iter=2000, class_weight='balanced'), np.asarray(embeddings)[keep], y, cv=cv),
    }
    return pd.DataFrame([{'method': name, 'n': len(y), 'accuracy': accuracy_score(y, p), 'macro_f1': f1_score(y, p, average='macro')}
                         for name, p in predictions.items()])


def fit_bertopic(texts, embeddings, encoder, seed=42, min_topic_size=8):
    """BERTopic as in Lab 4: MiniLM embeddings, UMAP, HDBSCAN, c-TF-IDF labels."""
    from bertopic import BERTopic
    from hdbscan import HDBSCAN
    from sklearn.feature_extraction.text import CountVectorizer
    from umap import UMAP

    model = BERTopic(embedding_model=encoder,
                     umap_model=UMAP(n_neighbors=10, n_components=5, min_dist=0.0, metric='cosine', random_state=seed),
                     hdbscan_model=HDBSCAN(min_cluster_size=min_topic_size, metric='euclidean', prediction_data=True),
                     vectorizer_model=CountVectorizer(stop_words='english', min_df=2))
    topics, _ = model.fit_transform(texts, np.asarray(embeddings))
    return model, topics
