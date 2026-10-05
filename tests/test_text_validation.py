import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from text_validation import binary_scores, embedding_benchmark, evaluate, merge, review_key, rule_view, wilson


def row(text, frame='candidate_clause', business='b1', review='r1'):
    return {'review_id': review, 'business_id': business, 'text': text, 'sampling_frame': frame}


def label(i, target='area', topics=('parking',), polarity='negative'):
    return {'item': i, 'label_target': target, 'label_topics': list(topics), 'label_polarity': polarity, 'confidence': 'high'}


class TextValidationTest(unittest.TestCase):
    def test_wilson_interval_brackets_rate(self):
        low, high = wilson(7, 10)
        self.assertLess(low, .7)
        self.assertGreater(high, .7)
        self.assertIsNone(wilson(0, 0))

    def test_binary_scores_count_errors(self):
        s = binary_scores([(True, True), (True, False), (False, True), (False, False)])
        self.assertEqual((s['tp'], s['fp'], s['fn']), (1, 1, 1))
        self.assertEqual(s['precision'], .5)
        self.assertEqual(s['recall'], .5)

    def test_rule_view_separates_area_and_business(self):
        self.assertEqual(rule_view('Parking is impossible on this street.')['target'], 'area')
        self.assertTrue(rule_view('Parking is impossible on this street.')['negative_area'])
        self.assertEqual(rule_view('Great pizza.')['target'], 'none')

    def test_merge_requires_complete_labels(self):
        with self.assertRaises(ValueError):
            merge([row('a'), row('b')], [label(0)])
        merged = merge([row('a')], [label(0)])
        self.assertEqual(merged[0]['reviewer_type'], 'agent')

    def test_evaluate_separates_frames(self):
        rows = [row('Parking is impossible on this street.'),
                row('The staff were friendly.', frame='stratified_project_period_topic'),
                row('We walked from the park nearby.', frame='random_review')]
        labels = [label(0), label(1, target='business', topics=('food_service_value',), polarity='positive'),
                  label(2, target='area', topics=('public_space',), polarity='neutral')]
        metrics = evaluate(merge(rows, labels))
        self.assertEqual(metrics['labels']['n_clauses'], 2)
        self.assertEqual(metrics['random_reviews']['with_place_mention'], 1)
        self.assertEqual(metrics['negative_area']['tp'], 1)

    def test_embedding_benchmark_groups_by_business(self):
        texts = ['Parking is impossible here.', 'The burger was great.'] * 6
        rows = [row(t, business=f'b{i % 6}', review=f'r{i}') for i, t in enumerate(texts)]
        labels = [label(i) if i % 2 == 0 else label(i, target='business', topics=('food_service_value',), polarity='positive') for i in range(len(rows))]
        encode = lambda batch: [[1.0, 0.0] if 'Parking' in t else [0.0, 1.0] for t in batch]
        result = embedding_benchmark(merge(rows, labels), encode, folds=3)
        self.assertEqual(result['grouping'], 'business_id')
        self.assertEqual(result['area_target']['embedding_lr']['f1'], 1.0)

    def test_review_key_matches_repository_convention(self):
        self.assertEqual(len(review_key('abc')), 16)


if __name__ == '__main__':
    unittest.main()
