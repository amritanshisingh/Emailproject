# Streamlit Dashboard for Finance Follow-Up Agent
# Run this with: streamlit run dashboard.py

import json
import os
import pandas as pd
import streamlit as st
from agent import run_agent

st.set_page_config(page_title="Finance Follow-Up Agent", page_icon="💰")

st.title(" Finance Credit Follow-Up Email Agent")
st.write("This tool automatically generates payment follow-up emails based on how overdue an invoice is.")

st.divider()

# show the tone escalation table so user understands the stages
st.subheader("How the Tone Escalation Works")
st.table({
    "Stage": ["1", "2", "3", "4", "5 (Flag)"],
    "Days Overdue": ["1-7", "8-14", "15-21", "22-30", "30+"],
    "Tone": ["Warm & Friendly", "Polite but Firm", "Formal & Serious", "Stern & Urgent", "Legal Team"],
})

st.divider()

# button to run the agent
st.subheader("Run the Agent")
st.info("Currently running in DRY RUN mode - no real emails will be sent.")

if st.button("▶ Generate Follow-Up Emails", type="primary"):
    with st.spinner("Calling Gemini API and generating emails... please wait"):
        results = run_agent()
        st.session_state["results"] = results
    st.success("Done! Emails generated successfully.")

# show results only after running
if "results" not in st.session_state:
    st.stop()

results = st.session_state["results"]

st.divider()

# quick summary numbers
st.subheader("Summary")
col1, col2, col3 = st.columns(3)
col1.metric("Total Invoices Processed", len(results))
col2.metric("Emails Generated", sum(1 for r in results if r["status"] == "DRY_RUN"))
col3.metric("Legal Flags", sum(1 for r in results if "LEGAL" in str(r["stage"])))

st.divider()

# show results table
st.subheader("Results Table")
table_data = []
for r in results:
    table_data.append({
        "Invoice": r["invoice"],
        "Client": r["client"],
        "Days Overdue": r["days_overdue"],
        "Stage": str(r["stage"]),
        "Status": r["status"]
    })
st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)

st.divider()

# show individual emails
st.subheader("Generated Emails Preview")

email_results = [r for r in results if r["status"] == "DRY_RUN"]

if len(email_results) == 0:
    st.warning("No emails were generated.")
else:
    for r in email_results:
        with st.expander(f"📧 {r['invoice']} — {r['client']} ({r['days_overdue']} days overdue)"):
            st.write(f"**Stage:** {r['stage']}")
            st.write(f"**Subject:** {r['subject']}")
            st.write("**Email Body:**")
            st.text(r["body"])

st.divider()

# show audit log if it exists
st.subheader("Audit Log")
if os.path.exists("logs/audit_log.json"):
    with open("logs/audit_log.json") as f:
        audit = json.load(f)
    if len(audit) > 0:
        st.dataframe(pd.DataFrame(audit), use_container_width=True, hide_index=True)
    else:
        st.write("Audit log is empty.")
else:
    st.write("No audit log found. Run the agent first.")