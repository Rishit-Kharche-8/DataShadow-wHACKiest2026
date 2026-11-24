import streamlit as st
from analyzer import (
    load_health_export,
    audit_inferences,
    compute_compound_insights,
    minimise_and_reaudit,
)
from ai_voice import (
    build_zero_pii_digest,
    sync_digest_to_aws_s3,
    generate_elevenlabs_brief,
)

st.set_page_config(
    page_title="DataShadow — Local-First Privacy & Habit Auditor",
    page_icon="🛡️",
    layout="wide",
)

st.title("🛡️ DataShadow — Local-First Privacy & Habit Auditor")
st.caption(
    "Track 03: Know Thyself | Raw exports stay strictly in local laptop RAM; "
    "only zero-PII digests reach ElevenLabs & encrypted AWS S3."
)

# STEP 1: LOCAL UPLOAD
st.sidebar.header("1. Local CSV / JSON Input")
uploaded_file = st.sidebar.file_uploader(
    "Upload Apple Health / Google Fit / Digital Wellbeing export",
    type=["csv", "json"],
)

if uploaded_file is not None:
    raw_df = load_health_export(uploaded_file)
    source_label = uploaded_file.name
else:
    raw_df = load_health_export("sample_health_logs.csv")
    source_label = "sample_health_logs.csv (Riya Campus Persona)"

st.sidebar.success(f"Loaded in Local RAM: `{source_label}` ({len(raw_df)} rows)")

# STEP 2: AUDIT LEAKS & COMPOUND HABITS
before_audit = audit_inferences(raw_df)
compound = compute_compound_insights(raw_df)
clean_df, after_audit, disclosure_card = minimise_and_reaudit(raw_df)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Before Re-ID Risk", f"{before_audit['reid_risk_pct']}%", delta="High Exposure", delta_color="inverse")
col2.metric(
    "After Scrub Re-ID Risk",
    f"{after_audit['reid_risk_pct']}%",
    delta=f"-{before_audit['reid_risk_pct'] - after_audit['reid_risk_pct']}% Risk",
)
col3.metric("Compound Trigger Days", f"{compound['trigger_days']} days")
col4.metric("Focus Crash Lift", f"{compound['lift']}x" if compound["status"] == "verified" else "Thin Data")

st.divider()

left_col, right_col = st.columns(2)

with left_col:
    st.subheader("2. Inference Mirror (What Outsiders Infer)")
    st.table(before_audit["inferences"])

    st.subheader("3. Compound Insight Meter")
    if compound["status"] == "verified":
        st.warning(compound["message"])
        if compound["cited_dates"]:
            st.caption(f"Cited Trigger Dates: {', '.join(compound['cited_dates'])}")
    else:
        st.info(compound["message"])

with right_col:
    st.subheader("4. Before vs. After PII Firewall")
    tab_before, tab_after = st.tabs(["Raw Export (Exposed)", "Minimised Export (Safe)"])
    with tab_before:
        st.dataframe(raw_df.head(6), use_container_width=True)
    with tab_after:
        st.dataframe(clean_df.head(6), use_container_width=True)

    st.subheader("5. Safe Export, ElevenLabs Brief & AWS S3 Vault")
    dl1, dl2 = st.columns(2)
    dl1.download_button(
        "⬇️ Download Clean CSV",
        data=clean_df.to_csv(index=False).encode("utf-8"),
        file_name="datashadow_minimised.csv",
        mime="text/csv",
        use_container_width=True,
    )
    dl2.download_button(
        "📄 Download Disclosure Card",
        data=disclosure_card.encode("utf-8"),
        file_name="datashadow_disclosure_card.md",
        mime="text/markdown",
        use_container_width=True,
    )

    if st.button("🔊 Generate 30s ElevenLabs Audio Brief & Sync Zero-PII Digest to AWS S3", use_container_width=True):
        digest = build_zero_pii_digest(before_audit, after_audit, compound, clean_df)
        _, s3_status = sync_digest_to_aws_s3(digest)
        script, audio_bytes, voice_status = generate_elevenlabs_brief(digest)

        st.success(voice_status)
        st.audio(audio_bytes)
        st.info(f"**Spoken Audit Transcript:** {script}")
        st.caption(s3_status)
        with st.expander("Inspect Zero-PII JSON Payload Sent to Cloud"):
            st.json(digest)
