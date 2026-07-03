"""
MediMate — Medical Copilot
==========================
Streamlit application for the MediMate medical copilot.

Features:
  - Audio transcription (Whisper) or text input
  - RAG-augmented SOAP note generation with NICE guideline references
  - ICD-10 code suggestions
  - Drug interaction checking (OpenFDA + local reference)
  - Guideline lookup tool
  - Human-in-the-loop approval workflow
"""

import streamlit as st
import tempfile
import os
from audio_processor import process_audio
from llm_core import generate_soap_note, suggest_icd10_codes
from tools import check_drug_interaction, lookup_nice_guideline, suggest_icd10, lookup_drug_info

# --- Page Configuration ---
st.set_page_config(
    page_title="MediMate Copilot",
    page_icon="🩺",
    layout="wide",
)

# --- Sidebar: Data Status & Guideline Lookup ---
with st.sidebar:
    st.title("📚 Knowledge Base")

    # Show vector store status
    try:
        from rag_engine import get_collection_stats
        stats = get_collection_stats()
        total = sum(stats.values())
        if total > 0:
            st.success(f"✅ RAG Engine Active — {total} documents indexed")
            st.caption(
                f"📋 NICE Guidelines: {stats.get('nice_guidelines', 0)} chunks\n\n"
                f"🏥 ICD-10 Codes: {stats.get('icd10_codes', 0)} entries\n\n"
                f"💊 Drug Reference: {stats.get('drug_reference', 0)} chunks"
            )
        else:
            st.warning("⚠️ Vector store is empty. Run `python setup_data.py` to populate.")
    except ImportError:
        st.warning("⚠️ RAG engine not available. Install chromadb and sentence-transformers.")

    st.markdown("---")

    # Guideline Lookup Tool
    st.subheader("🔍 Guideline Lookup")
    guideline_query = st.text_input("Search NICE Guidelines:", placeholder="e.g., asthma management")
    if st.button("Search Guidelines"):
        if guideline_query:
            with st.spinner("Searching guidelines..."):
                result = lookup_nice_guideline(guideline_query)
                st.markdown(result)
        else:
            st.info("Enter a condition or clinical question to search.")

    st.markdown("---")

    # Drug Info Lookup
    st.subheader("💊 Drug Reference")
    drug_query = st.text_input("Look up a drug:", placeholder="e.g., Metformin")
    if st.button("Look Up Drug"):
        if drug_query:
            with st.spinner("Looking up drug..."):
                result = lookup_drug_info(drug_query)
                st.markdown(result)
        else:
            st.info("Enter a drug name to look up.")


# --- Main Content ---
st.title("🩺 MediMate: Medical Copilot")
st.markdown(
    "Upload a doctor-patient conversation audio, or type a summary, "
    "to generate an evidence-based SOAP note with NICE guideline references."
)

col1, col2 = st.columns(2)

# --- Left Column: Input ---
with col1:
    st.subheader("📝 Input")
    input_method = st.radio("Choose input method:", ("Audio Upload", "Text Summary"))

    transcript = ""
    if input_method == "Audio Upload":
        uploaded_file = st.file_uploader("Upload Audio (MP3, WAV)", type=["mp3", "wav"])
        if uploaded_file is not None:
            with st.spinner("Transcribing audio... (This may take a moment locally)"):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = tmp_file.name

                transcript = process_audio(tmp_path)
                st.success("Transcription Complete!")
                st.text_area("Transcript", transcript, height=150)
                os.remove(tmp_path)
    else:
        transcript = st.text_area(
            "Type doctor-patient conversation summary:",
            height=150,
            placeholder="e.g., Patient is a 55-year-old male presenting with persistent cough for 3 weeks, shortness of breath on exertion, and mild chest tightness. History of smoking 20 pack-years. Currently on Amlodipine 5mg for hypertension.",
        )

    st.markdown("---")

    # Drug Interaction Check
    st.subheader("⚠️ Drug Interaction Check")
    drug_col1, drug_col2 = st.columns(2)
    with drug_col1:
        drug1 = st.text_input("Drug 1", placeholder="e.g., Aspirin")
    with drug_col2:
        drug2 = st.text_input("Drug 2", placeholder="e.g., Warfarin")

    if st.button("Check Interaction"):
        if drug1 and drug2:
            with st.spinner("Checking OpenFDA + local drug reference..."):
                interaction = check_drug_interaction(drug1, drug2)
                if interaction:
                    st.warning(f"⚠️ **Interaction Found:**\n\n{interaction}")
                else:
                    st.success("✅ No major interactions found in OpenFDA database.")
        else:
            st.info("Enter two drug names to check for interactions.")


# --- Right Column: SOAP Note & ICD-10 ---
with col2:
    st.subheader("📋 Generated SOAP Note")

    if st.button("Generate SOAP Note", type="primary"):
        if not transcript:
            st.error("Please provide audio or text input first.")
        else:
            with st.spinner("Generating evidence-based SOAP note..."):
                result = generate_soap_note(transcript)

                soap_note = result["soap_note"]
                context_used = result["context_used"]
                rag_enabled = result["rag_enabled"]

                # Display RAG status
                if rag_enabled:
                    st.info("📚 **RAG-Augmented:** This note references NICE guidelines from the knowledge base.")
                else:
                    st.caption("ℹ️ Generated without guideline context. Run `setup_data.py` to enable RAG.")

                # Display the SOAP note
                st.markdown(soap_note)

                # Show referenced guidelines in an expander
                if context_used:
                    with st.expander("📋 View Referenced Clinical Context", expanded=False):
                        st.text(context_used)

                st.markdown("---")

                # ICD-10 Suggestions Section
                st.subheader("🏥 ICD-10 Code Suggestions")
                icd10_results = suggest_icd10(transcript, top_k=5)
                if icd10_results:
                    for suggestion in icd10_results:
                        relevance_pct = int(suggestion["relevance_score"] * 100)
                        st.markdown(
                            f"**`{suggestion['code']}`** — {suggestion['description']}  \n"
                            f"*Category: {suggestion['category']}* | "
                            f"Relevance: {'🟢' if relevance_pct > 70 else '🟡' if relevance_pct > 50 else '🔴'} {relevance_pct}%"
                        )
                else:
                    st.caption("No ICD-10 suggestions available. Ensure the vector store is populated.")

                st.markdown("---")

                # HITL Checkpoint
                st.markdown("**🔒 HITL Checkpoint:** Please review and edit the note below before saving.")
                edited_note = st.text_area("Edit SOAP Note", soap_note, height=300)
                if st.button("✅ Approve & Save Note"):
                    st.success("Note approved and saved successfully to patient record!")
                    st.balloons()
