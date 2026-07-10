"""
MediMate — Unit Tests for llm_core.py
=======================================
Tests SOAP note generation (mock mode), safety flagging,
and ICD-10 code suggestion.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from llm_core import generate_soap_note, suggest_icd10_codes, flag_out_of_scope, SAFETY_DISCLAIMER


class TestFlagOutOfScope:
    """Tests for the safety/emergency flagging system."""

    def test_no_flags_for_normal_transcript(self):
        """A routine transcript should not trigger any safety flags."""
        transcript = "Patient presents with mild headache for 2 days. No other symptoms."
        result = flag_out_of_scope(transcript)
        assert result["is_emergency"] is False
        assert result["flags"] == []
        assert result["warning"] == ""

    def test_flags_suicidal_ideation(self):
        """Should flag transcripts mentioning suicidal ideation."""
        transcript = "Patient reports feeling hopeless and having suicidal thoughts."
        result = flag_out_of_scope(transcript)
        assert result["is_emergency"] is True
        assert "suicidal" in result["flags"]
        assert "EMERGENCY" in result["warning"]

    def test_flags_chest_pain(self):
        """Should flag transcripts mentioning radiating chest pain."""
        transcript = "Patient has chest pain radiating to the left arm."
        result = flag_out_of_scope(transcript)
        assert result["is_emergency"] is True
        assert "chest pain radiating" in result["flags"]

    def test_flags_anaphylaxis(self):
        """Should flag anaphylactic reactions."""
        transcript = "Patient experiencing anaphylaxis after bee sting."
        result = flag_out_of_scope(transcript)
        assert result["is_emergency"] is True
        assert "anaphylaxis" in result["flags"]

    def test_flags_multiple_keywords(self):
        """Should capture all matching keywords."""
        transcript = "Patient is unresponsive with severe bleeding from wound."
        result = flag_out_of_scope(transcript)
        assert result["is_emergency"] is True
        assert len(result["flags"]) >= 2

    def test_case_insensitive(self):
        """Should match keywords regardless of case."""
        transcript = "Patient reports SUICIDAL thoughts and SELF-HARM tendencies."
        result = flag_out_of_scope(transcript)
        assert result["is_emergency"] is True


class TestGenerateSoapNote:
    """Tests for generate_soap_note() in mock mode (no API key)."""

    def test_mock_mode_returns_dict(self):
        """Should return a dict with the expected keys."""
        result = generate_soap_note("Patient has fever and cough for 3 days.")
        assert isinstance(result, dict)
        assert "soap_note" in result
        assert "context_used" in result
        assert "rag_enabled" in result
        assert "safety" in result

    def test_mock_mode_includes_disclaimer(self):
        """Mock mode should include the safety disclaimer."""
        result = generate_soap_note("Patient has a mild headache.")
        assert "AI-GENERATED" in result["soap_note"]
        assert "NOT A MEDICAL DIAGNOSIS" in result["soap_note"]

    def test_mock_mode_soap_sections(self):
        """Mock response should contain SOAP sections."""
        result = generate_soap_note("Patient has a sore throat.")
        note = result["soap_note"]
        assert "Subjective" in note
        assert "Objective" in note
        assert "Assessment" in note
        assert "Plan" in note

    def test_safety_flag_passed_through(self):
        """Safety flags should be passed through in the result."""
        result = generate_soap_note("Patient is having a seizure and is unresponsive.")
        assert result["safety"]["is_emergency"] is True
        assert len(result["safety"]["flags"]) > 0

    def test_normal_transcript_no_safety_flag(self):
        """Normal transcript should have no safety flags."""
        result = generate_soap_note("Routine checkup. All vitals normal.")
        assert result["safety"]["is_emergency"] is False


class TestSuggestIcd10Codes:
    """Tests for suggest_icd10_codes()."""

    def test_returns_list(self):
        """Should return a list."""
        result = suggest_icd10_codes("type 2 diabetes with complications")
        assert isinstance(result, list)

    def test_suggestion_structure(self):
        """Each suggestion should have the required keys."""
        results = suggest_icd10_codes("asthma")
        for item in results:
            assert "code" in item
            assert "description" in item
            assert "category" in item
            assert "relevance_score" in item
