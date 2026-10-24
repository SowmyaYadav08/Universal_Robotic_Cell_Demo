import unittest
import numpy as np
from compare_models import nearest_distances


class DistanceTests(unittest.TestCase):
    def test_normal_references_exclude_identical_self_match(self):
        refs = np.array([[1.,0.],[0.,1.]])
        scores, nearest = nearest_distances(refs, refs, exclude_self=True)
        np.testing.assert_allclose(scores, [1,1])
        np.testing.assert_array_equal(nearest, [1,0])

    def test_query_can_match_a_normal_reference(self):
        refs = np.array([[1.,0.],[0.,1.]])
        scores, _ = nearest_distances(np.array([[1.,0.],[-1.,0.]]), refs)
        np.testing.assert_allclose(scores, [0,1])
