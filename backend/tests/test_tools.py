"""
MediMate — Unit Tests for tools.py
===================================
Tests the tool functions: drug interaction check, ICD-10 suggestion,
guideline lookup, drug info lookup, and test suggestion.
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


class TestCheckDrugInteraction:
    """Tests for check_drug_interaction()."""

    @patch("tools.requests.get")
    def test_interaction_found(self, mock_get):
        """Should return a message when FDA reports adverse events for both drugs."""
        from tools import check_drug_interaction

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "meta": {"results": {"total": 42}},
            "results": [{
                "patient": {
                    "reaction": [
                        {"reactionmeddrapt": "Nausea"},
                        {"reactionmeddrapt": "Dizziness"},
                    ]
                }
            }]
        }
        mock_get.return_value = mock_response

        result = check_drug_interaction("Aspirin", "Warfarin")
        assert "42" in result
        assert "Aspirin" in result
        assert "Warfarin" in result

    @patch("tools.requests.get")
    def test_no_interaction_found(self, mock_get):
        """Should return empty string when no results from FDA."""
        from tools import check_drug_interaction

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": []}
        mock_get.return_value = mock_response

        result = check_drug_interaction("DrugA", "DrugB")
        assert result == ""

    @patch("tools.requests.get")
    def test_fda_404(self, mock_get):
        """Should return empty string on 404."""
        from tools import check_drug_interaction

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        result = check_drug_interaction("DrugX", "DrugY")
        assert result == ""

    @patch("tools.requests.get")
    def test_connection_error(self, mock_get):
        """Should return error message on connection failure."""
        from tools import check_drug_interaction
        import requests

        mock_get.side_effect = requests.exceptions.ConnectionError("Network unreachable")
        result = check_drug_interaction("Aspirin", "Ibuprofen")
        assert "Error" in result


class TestSuggestIcd10:
    """Tests for suggest_icd10()."""

    def test_returns_list(self):
        """Should return a list (possibly empty if RAG is unavailable)."""
        from tools import suggest_icd10
        result = suggest_icd10("type 2 diabetes")
        assert isinstance(result, list)

    def test_suggestion_structure(self):
        """Each suggestion should have required keys."""
        from tools import suggest_icd10
        results = suggest_icd10("headache and fever", top_k=2)
        for item in results:
            assert "code" in item
            assert "description" in item
            assert "category" in item
            assert "relevance_score" in item


class TestSuggestTests:
    """Tests for suggest_tests()."""

    def test_returns_list(self):
        """Should return a list (possibly empty)."""
        from tools import suggest_tests
        result = suggest_tests("patient with persistent cough and shortness of breath")
        assert isinstance(result, list)

    def test_suggestion_structure(self):
        """Each test suggestion should have required keys."""
        from tools import suggest_tests
        results = suggest_tests("hypertension and diabetes", top_k=3)
        for item in results:
            assert "test" in item
            assert "rationale" in item
            assert "source" in item
            assert "relevance_score" in item

    def test_max_results(self):
        """Should return at most 8 results."""
        from tools import suggest_tests
        results = suggest_tests("general health checkup with multiple complaints", top_k=10)
        assert len(results) <= 8


class TestLookupDrugInfo:
    """Tests for lookup_drug_info()."""

    def test_returns_string(self):
        """Should always return a string."""
        from tools import lookup_drug_info
        result = lookup_drug_info("Metformin")
        assert isinstance(result, str)


class TestLookupNiceGuideline:
    """Tests for lookup_nice_guideline()."""

    def test_returns_string(self):
        """Should always return a string."""
        from tools import lookup_nice_guideline
        result = lookup_nice_guideline("asthma")
        assert isinstance(result, str)
