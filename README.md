# DataShadow — Local-First Privacy & Habit Auditor
**Hackathon:** wHACKiest 2026 (Ramaiah Institute of Technology, Bengaluru)  
**Track:** Track 03 — *Know Thyself*

## Overview
**DataShadow** is a local-first privacy and habit auditor that exposes what raw health/activity exports reveal about a user's routine, strips PII and coarsens timestamps on-device, re-audits the file to prove re-identification risk dropped, and delivers a screen-free **ElevenLabs** audio brief plus encrypted zero-PII JSON digests on **AWS S3**.

## Architecture (Input → Processing → Output)
1. **Input (`app.py`):** Local Streamlit CSV/JSON uploader (raw files stay in local RAM only).
2. **Inference Mirror (`analyzer.py`):** Detects exposed PII columns & timestamp fingerprints, cites exact supporting rows, and computes baseline re-identification risk.
3. **Compound Insight Meter (`analyzer.py`):** Deterministic lift math detecting multi-habit chains (`<6h` sleep + `>90m` late screen → low focus), returning `"insufficient evidence"` on thin data.
4. **PII Firewall & Re-Audit (`analyzer.py`):** Drops `name`, `email`, `gps_city`, rounds exact timestamps into coarse windows, re-runs the exact same rules to verify risk reduction (`94% → 3%`), and exports a Clean CSV + Disclosure Card.
5. **Voice & Vault Layer (`ai_voice.py`):** Synthesizes a 30-sec spoken audit via **ElevenLabs** and syncs strictly zero-PII summary JSON digests to an encrypted **AWS S3** vault.

## 4-Member Modular Ownership
- **Member 1:** `sample_health_logs.csv` & GitHub Repository Management
- **Member 2:** `analyzer.py` (Inference Mirror, Deterministic Lift Rules & PII Firewall)
- **Member 3:** `app.py` (Streamlit Local-First Dashboard & Export UI)
- **Member 4:** `ai_voice.py` (ElevenLabs Audio Brief & AWS S3 Zero-PII Digest Sync)

## Quickstart (Run Locally)
```bash
pip install -r requirements.txt
streamlit run app.py
