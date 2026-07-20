# ADR-001: Choosing Local Whisper over Cloud Speech APIs

## Context
MediMate needs to transcribe live doctor-patient conversations into text to generate SOAP notes. Audio data in a clinical setting contains highly sensitive Protected Health Information (PHI). We needed to decide between using a managed cloud service (e.g., Google Cloud Speech-to-Text, OpenAI Whisper API) or running an open-source model locally.

## Decision
We chose to run **HuggingFace's Whisper model locally on the CPU**.

## Consequences
**Positive:**
- **Absolute Privacy:** Raw audio bytes never leave the host machine, eliminating major HIPAA/GDPR compliance risks associated with transmitting voice data.
- **Zero Cost:** No per-minute transcription fees, keeping the operational cost at $0.
- **Offline Capability:** The transcription step works entirely offline.

**Negative:**
- **Compute Bound:** Running inference on a CPU is slower than cloud GPUs. For longer encounters, there is a slight processing delay before the text is ready.
- **Package Size:** The Whisper model weights (base/small) require local disk space and RAM.

## Alternatives considered
- **OpenAI Whisper API:** Rejected due to cost ($0.006/min) and the requirement to send PHI to a third-party server.
- **AWS Transcribe Medical:** Rejected due to high enterprise costs and complex IAM setup not suitable for a zero-cost local copilot.
