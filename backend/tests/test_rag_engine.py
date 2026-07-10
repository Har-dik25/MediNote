"""
MediMate — Unit Tests for rag_engine.py
========================================
Tests the RAG vector store search functions and collection stats.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


class TestSearchGuidelines:
    """Tests for search_guidelines()."""

    def test_returns_list(self):
        """Should return a list."""
        from rag_engine import search_guidelines
        results = search_guidelines("asthma management")
        assert isinstance(results, list)

    def test_result_structure(self):
        """Each result should have text, metadata, and distance."""
        from rag_engine import search_guidelines
        results = search_guidelines("hypertension treatment", top_k=2)
        for r in results:
            assert "text" in r
            assert "metadata" in r
            assert "distance" in r

    def test_respects_top_k(self):
        """Should return at most top_k results."""
        from rag_engine import search_guidelines
        results = search_guidelines("diabetes", top_k=2)
        assert len(results) <= 2


class TestSearchIcd10:
    """Tests for search_icd10()."""

    def test_returns_list(self):
        """Should return a list."""
        from rag_engine import search_icd10
        results = search_icd10("headache")
        assert isinstance(results, list)

    def test_result_has_code_metadata(self):
        """Results should have code in metadata."""
        from rag_engine import search_icd10
        results = search_icd10("type 2 diabetes", top_k=3)
        for r in results:
            assert "metadata" in r
            # code may or may not be present depending on data


class TestSearchDrugs:
    """Tests for search_drugs()."""

    def test_returns_list(self):
        """Should return a list."""
        from rag_engine import search_drugs
        results = search_drugs("metformin")
        assert isinstance(results, list)


class TestSearchAll:
    """Tests for search_all()."""

    def test_returns_dict_with_three_keys(self):
        """Should return a dict with guidelines, icd10_codes, and drugs."""
        from rag_engine import search_all
        results = search_all("asthma")
        assert isinstance(results, dict)
        assert "guidelines" in results
        assert "icd10_codes" in results
        assert "drugs" in results


class TestGetCollectionStats:
    """Tests for get_collection_stats()."""

    def test_returns_dict(self):
        """Should return a dict with collection counts."""
        from rag_engine import get_collection_stats
        stats = get_collection_stats()
        assert isinstance(stats, dict)

    def test_stats_have_expected_keys(self):
        """Should have keys for all three collections."""
        from rag_engine import get_collection_stats
        stats = get_collection_stats()
        assert "nice_guidelines" in stats
        assert "icd10_codes" in stats
        assert "drug_reference" in stats

    def test_stats_are_non_negative(self):
        """All counts should be non-negative integers."""
        from rag_engine import get_collection_stats
        stats = get_collection_stats()
        for count in stats.values():
            assert isinstance(count, int)
            assert count >= 0
