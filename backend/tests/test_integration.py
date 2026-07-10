"""
MediMate — Integration Tests
==============================
End-to-end test: transcript → SOAP note → ICD-10 → safety check.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


class TestEndToEndPipeline:
    """Integration test: full pipeline from transcript to output."""

    def test_full_pipeline_normal_case(self):
        """
        End-to-end test: a normal transcript produces a SOAP note
        with ICD-10 suggestions and no safety flags.
        """
        from llm_core import generate_soap_note
        from tools import suggest_icd10, suggest_tests

        transcript = (
            "Patient is a 45-year-old female presenting with persistent dry cough "
            "for 2 weeks. No fever, no weight loss. Non-smoker. "
            "Currently on Lisinopril 10mg for hypertension."
        )

        # Step 1: Generate SOAP note
        result = generate_soap_note(transcript)
        assert isinstance(result, dict)
        assert "soap_note" in result
        assert len(result["soap_note"]) > 50  # Should be a meaningful note

        # Step 2: Safety should NOT be flagged
        assert result["safety"]["is_emergency"] is False

        # Step 3: ICD-10 suggestions
        icd10 = suggest_icd10(transcript, top_k=3)
        assert isinstance(icd10, list)

        # Step 4: Test suggestions
        tests = suggest_tests(transcript, top_k=3)
        assert isinstance(tests, list)

    def test_full_pipeline_emergency_case(self):
        """
        End-to-end test: an emergency transcript triggers safety flags
        but still produces a SOAP note.
        """
        from llm_core import generate_soap_note

        transcript = (
            "Patient brought to ER with crushing chest pain radiating to left arm. "
            "Sweating profusely. History of cardiac arrest in family. "
            "Patient appears unresponsive at times."
        )

        result = generate_soap_note(transcript)

        # Should still produce a note
        assert "soap_note" in result
        assert len(result["soap_note"]) > 0

        # Safety SHOULD be flagged
        assert result["safety"]["is_emergency"] is True
        assert len(result["safety"]["flags"]) >= 1
        assert "EMERGENCY" in result["safety"]["warning"]

    def test_disclaimer_always_present(self):
        """The AI disclaimer should always be present in the output."""
        from llm_core import generate_soap_note

        result = generate_soap_note("Routine checkup. Patient is healthy.")
        assert "AI-GENERATED" in result["soap_note"]
        assert "NOT A MEDICAL DIAGNOSIS" in result["soap_note"]
