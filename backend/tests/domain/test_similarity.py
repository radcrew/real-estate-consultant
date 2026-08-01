"""Tests for cosine similarity helpers."""

from app.domain.similarity import cosine_similarity, similarity_to_match_score


class TestCosineSimilarity:
    def test_identical_vectors(self):
        assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0

    def test_orthogonal_vectors(self):
        assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0

    def test_zero_vector(self):
        assert cosine_similarity([0.0, 0.0], [1.0, 2.0]) == 0.0

    def test_mismatched_length(self):
        assert cosine_similarity([1.0], [1.0, 2.0]) == 0.0


class TestSimilarityToMatchScore:
    def test_maps_unit_interval(self):
        assert similarity_to_match_score(1.0) == 100.0
        assert similarity_to_match_score(0.5) == 50.0
        assert similarity_to_match_score(-0.2) == 0.0
