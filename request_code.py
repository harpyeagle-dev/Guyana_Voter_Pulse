import streamlit as st
import pandas as pd
import datetime
import smtplib
from email.mime.text import MIMEText
import plotly.express as px
import os

# Setup
st.set_page_config(page_title="Guyana Voter Pulse", layout="wide")
st.title("🇬🇾 Guyana Voter Pulse")

EMAIL_ADDRESS = st.secrets["EMAIL"]["address"]
EMAIL_PASSWORD = st.secrets["EMAIL"]["password"]

CODES_FILE = "valid_codes.csv"
LOG_FILE = "usage_log.csv"
VOTES_FILE = "votes.csv"

# Session state
if "step" not in st.session_state:
    st.session_state.step = 1
if "email" not in st.session_state:
    st.session_state.email = ""
if "code" not in st.session_state:
    st.session_state.code = ""
if "pending_action" not in st.session_state:
    st.session_state.pending_action = None
if "pending_vote" not in st.session_state:
    st.session_state.pending_vote = None

# Helpers
def send_email(to_email, code):
    subject = "Your Guyana Voter Access Code"
    body = f\"""Your one-time access code is: {code}

Use this code to cast your vote.

Guyana Voter Pulse Team
\"""
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)

# Handle pending actions from last rerun
if st.session_state.pending_action == "save_code":
    email = st.session_state.email
    codes = pd.read_csv(CODES_FILE)
    log = pd.read_csv(LOG_FILE) if os.path.exists(LOG_FILE) else pd.DataFrame(columns=["timestamp", "event", "email", "code", "source"])
    if not log[log["email"] == email].empty:
        code = log[log["email"] == email]["code"].values[0]
    else:
        unused = codes[codes["issued"] == False]
        if unused.empty:
            st.error("No more codes available.")
            st.stop()
        code = unused.iloc[0]["code"]
        codes.loc[codes["code"] == code, "issued"] = True
        codes.to_csv(CODES_FILE, index=False)
        log = pd.concat([log, pd.DataFrame([{
            "timestamp": datetime.datetime.now(),
            "event": "code_issued",
            "email": email,
            "code": code,
            "source": "app"
        }])], ignore_index=True)
        log.to_csv(LOG_FILE, index=False)
        send_email(email, code)
    st.session_state.pending_action = None
    st.session_state.step = 2
    st.experimental_rerun()

if st.session_state.pending_action == "save_vote":
    vote_data = st.session_state.pending_vote
    vote_df = pd.DataFrame([vote_data])
    if os.path.exists(VOTES_FILE) and os.path.getsize(VOTES_FILE) > 0:
        existing = pd.read_csv(VOTES_FILE)
    else:
        existing = pd.DataFrame(columns=vote_df.columns)
    pd.concat([existing, vote_df], ignore_index=True).to_csv(VOTES_FILE, index=False)
    codes = pd.read_csv(CODES_FILE)
    codes.loc[codes["code"] == vote_data["Code"], "used"] = True
    codes.to_csv(CODES_FILE, index=False)
    st.session_state.pending_vote = None
    st.session_state.pending_action = None
    st.session_state.step = 4
    st.experimental_rerun()

# Step 1: Request Code
if st.session_state.step == 1:
    with st.form("request_code_form"):
        st.subheader("📬 Step 1: Request Access Code")
        email = st.text_input("Enter your email")
        send = st.form_submit_button("Send Code")
    if send:
        st.session_state.email = email
        st.session_state.pending_action = "save_code"
        st.experimental_rerun()

# Step 2: Enter Code
elif st.session_state.step == 2:
    st.subheader("🗳️ Step 2: Enter Code Sent to Your Email")
    with st.form("verify_code"):
        code_input = st.text_input("Enter your code")
        validate = st.form_submit_button("Verify Code")
    if validate:
        codes = pd.read_csv(CODES_FILE)
        match = codes[codes["code"] == code_input]
        if match.empty:
            st.error("Invalid code.")
        elif match.iloc[0]["used"]:
            st.warning("Code already used.")
        else:
            st.session_state.code = code_input
            st.session_state.step = 3
            st.experimental_rerun()

# Step 3: Vote
elif st.session_state.step == 3:
    st.success("✅ Code verified. Please cast your vote below.")
    with st.form("vote_form"):
        region = st.selectbox("Region", [f"Region {i}" for i in range(1, 11)])
        party = st.selectbox("Party", ["PPP", "APNU", "AFC", "LJP", "URP", "TNM", "ANUG", "ALP", "GAP", "Other"])
        candidate = st.text_input("Preferred presidential candidate")
        reason = st.text_area("Why this candidate? (optional)")
        age = st.selectbox("Age", ["18–24", "25–34", "35–44", "45–54", "55+"])
        gender = st.radio("Gender", ["Male", "Female", "Other"])
        diaspora = st.radio("Where do you live?", ["In Guyana", "Diaspora"])
        issues = st.multiselect("Top 3 issues", ["Jobs", "Education", "Healthcare", "Cost of living", "Crime", "Corruption", "Infrastructure"])
        fair = st.radio("Do you believe the election will be fair?", ["Yes", "No", "Not sure"])
        gecom = st.radio("Do you trust GECOM?", ["Yes", "No", "Not sure"])
        submit_vote = st.form_submit_button("Submit Vote")
    if submit_vote:
        if len(issues) > 3:
            st.error("Please select no more than 3 issues.")
        else:
            st.session_state.pending_vote = {
                "Timestamp": datetime.datetime.now(),
                "Code": st.session_state.code,
                "Region": region,
                "Party": party,
                "Preferred Candidate": candidate,
                "Candidate Reason": reason,
                "Age": age,
                "Gender": gender,
                "Diaspora": diaspora,
                "Top Issues": ", ".join(issues),
                "Fairness": fair,
                "GECOM Trust": gecom
            }
            st.session_state.pending_action = "save_vote"
            st.experimental_rerun()

# Step 4: Results
elif st.session_state.step == 4:
    st.subheader("📊 Voting Summary")
    try:
        df = pd.read_csv(VOTES_FILE)
    except:
        df = pd.DataFrame()
    if not df.empty:
        st.write("### Party Preferences")
        st.plotly_chart(px.bar(df["Party"].value_counts().reset_index(), x="index", y="Party", title="Votes by Party"), use_container_width=True)
        st.write("### Votes by Region")
        st.plotly_chart(px.pie(df, names="Region", title="Region Breakdown"), use_container_width=True)
        st.write("### Age & Gender")
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(px.pie(df, names="Age", title="Age Breakdown"), use_container_width=True)
        with col2:
            st.plotly_chart(px.pie(df, names="Gender", title="Gender Breakdown"), use_container_width=True)
        st.write("### Trust & Fairness")
        col3, col4 = st.columns(2)
        with col3:
            st.plotly_chart(px.pie(df, names="Fairness", title="Fairness Perception"), use_container_width=True)
        with col4:
            st.plotly_chart(px.pie(df, names="GECOM Trust", title="Trust in GECOM"), use_container_width=True)
