"""Compare regenerated scientific JSON across platform math libraries."""
import math


def assert_numeric_tree(case, actual, expected, path='$'):
    if isinstance(expected, dict):
        case.assertIsInstance(actual, dict, path)
        case.assertEqual(actual.keys(), expected.keys(), path)
        for key in expected:
            assert_numeric_tree(case, actual[key], expected[key], f'{path}.{key}')
    elif isinstance(expected, list):
        case.assertIsInstance(actual, list, path)
        case.assertEqual(len(actual), len(expected), path)
        for index, (a, e) in enumerate(zip(actual, expected)):
            assert_numeric_tree(case, a, e, f'{path}[{index}]')
    elif isinstance(expected, float):
        case.assertIsInstance(actual, (int, float), path)
        case.assertTrue(math.isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-10),
                        f'{path}: {actual!r} != {expected!r} within numerical tolerance')
    else:
        case.assertEqual(actual, expected, path)
