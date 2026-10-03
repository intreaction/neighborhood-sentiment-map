# Advanced unstructured-text analysis

This pass adds learned text structure alongside the provisional aspect rules.
The two methods answer different questions: explicit rules identify candidate
place/access complaints; an unsupervised topic model discovers recurring language
without assuming reviews are about civic infrastructure.

## Corpus and representation

The core pipeline scored 1,063,956 distinct reviews across early, baseline and
post-opening project windows. The learned topic analysis uses a separate,
reproducible sample of nearby baseline and post reviews: 23,691 unique reviews
from 136,807 eligible reviews. Each project/period contributes up to 1,200 reviews,
selected by a stable SHA-256 rank of review ID. Shared selected reviews are deduplicated.
Coverage counts travel with each project result. This is a sample, not a topic
analysis of every review in the archive.

TF-IDF represents unigrams and bigrams with sublinear term frequency, English stop
words, Unicode accent normalization, minimum document frequency 2, maximum document
frequency 95%, and an 8,000-feature cap. Nonnegative matrix factorization learns five
topics with a fixed random seed. The descriptive basis is fit to 10,971 distinct
sampled baseline reviews. Post-opening reviews are projected through that frozen
vocabulary and topic basis; they never determine the descriptive topics.

The site displays the actual leading terms instead of assigning unverified civic
labels. Several learned patterns are food, service, pizza and dessert language.
This is a substantive coverage finding: Yelp often describes businesses more directly
than public infrastructure. Do not relabel these as neighborhood satisfaction.

## Project features

- **Topic mixture:** mean of normalized review-topic weights over mapped reviews.
  These are model weights, not calibrated probabilities or literal mention shares.
  Unmapped reviews are counted and excluded from mixture aggregation.
- **Topic diversity:** Shannon entropy of the aggregate mixture, divided by log(5).
  Zero means concentrated in one topic; one means an even mixture. It is not a
  measure of demographic, business or economic diversity.
- **Review length:** mean word count in the sampled reviews.
- **Lexical diversity:** mean per-review unique-word/word ratio. It depends on review
  length and is descriptive, not a reading-quality or sentiment score.
- **Negation frequency:** negation tokens per 100 words. Negation is not negative
  sentiment; phrases such as “not bad” illustrate why they differ.

The earlier full-coverage extraction also retains whole-review VADER sentiment,
topic-specific provisional clause polarity, and business/area/unclear targets.
Area-negative shares require explicit area context. All three model text-share
features use all nearby baseline reviews as their denominator.

## Evaluation and limitations

Descriptive topics fit on the full baseline sample cannot be used directly to claim
held-out predictive performance. The advanced CE challenger refits TF-IDF and NMF
inside each project/city validation fold and excludes held-out/shared review IDs.
Its held-out review texts are transformed using only the training basis. Only
baseline text enters prediction; post-opening counts define the outcome.

The predictive text basis is separate from the descriptive view: it uses up to 500
baseline reviews per eligible project (5,000 unique reviews for the final fit) and
has its own fingerprint. Topic values from the descriptive basis cannot be substituted.
When conservative shared-catchment exclusion removes all sampled text from a
training project, that project's advanced features are imputed from other training
projects inside the fold and recorded in the audit. This occurred for two training
project/fold memberships across two of the 17 folds (Crescent when Lafitte was held
out, and Rail Park when Schuylkill was held out). All folds had zero held-out review
ID overlap in representation training.

On the common ten-project sample, the advanced text challenger has project-held-out
MAE **53.04** and city-held-out MAE **46.67** reviews/$1M. The three-input baseline
has **49.33** and **45.61**, respectively. Advanced text failed both improvement
checks, so it remains an explicitly evaluated challenger and a substantive analysis
layer; it does not silently replace the better-performing baseline. Reduced-case
timing sensitivity was not run for this nonselected challenger.

The number of projects, not the number of reviews, limits CE model evaluation.
Ten eligible projects provide little evidence of generalization. Model selection
from the same held-out results remains exploratory; no independent final test set
or calibrated prediction interval exists. Unsupervised coherence, rule accuracy
and predictive utility are different claims.

Independent human annotation is still pending. The local task set contains 731
blank-label items: 200 randomly sampled reviews, 200 candidate clauses and 331
project/period/topic-stratified items. Semantic unit tests do not substitute for
human precision/recall estimates.

## Reproduction

```sh
../.venv/bin/python src/build_project_evidence.py --workers 4
../.venv/bin/python src/build_advanced_text.py
../.venv/bin/python src/train_project_model.py
../.venv/bin/python src/build_evidence_site.py
```

Raw text, review IDs, sampled corpus and annotation tasks remain in ignored
`data/interim/project_evidence/`. The public aggregate artifact is
`data/derived/advanced_text.json`; it contains topic terms, aggregate features,
short illustrative excerpts and provenance.
