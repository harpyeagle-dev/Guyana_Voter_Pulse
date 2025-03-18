
import streamlit as st
import pandas as pd
import datetime
import smtplib
from email.mime.text import MIMEText
import plotly.express as px
import os

st.set_page_config(page_title="Guyana Voter Pulse", layout="wide")
st.title("🇬🇾 Guyana Voter Pulse – Request & Vote")

EMAIL_ADDRESS = st.secrets["EMAIL"]["address"]
EMAIL_PASSWORD = st.secrets["EMAIL"]["password"]

CODES_FILE = "valid_codes.csv"
LOG_FILE = "usage_log.csv"
VOTES_FILE = "votes.csv"

# Initialize session state
if "step" not in st.session_state:
    st.session_state.step = 1
if "email" not in st.session_state:
    st.session_state.email = ""
if "code" not in st.session_state:
    st.session_state.code = ""

# Email sender
def send_email(to_email, code):
    subject = "Your Guyana Voter Access Code"
    body = f"""Your one-time access code is: {code}

Use this code to cast your vote.

Guyana Voter Pulse Team
"""
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)

def log_event(event, email, code, source="app"):
    log = pd.read_csv(LOG_FILE) if os.path.exists(LOG_FILE) else pd.DataFrame(columns=["timestamp", "event", "email", "code", "source"])
    new_entry = pd.DataFrame([{
        "timestamp": datetime.datetime.now(),
        "event": event,
        "email": email,
        "code": code,
        "source": source
    }])
    log = pd.concat([log, new_entry], ignore_index=True)
    log.to_csv(LOG_FILE, index=False)

# STEP 1 — Request code
if st.session_state.step == 1:
    with st.form("request_form"):
        st.subheader("📬 Step 1: Request Access Code")
        email = st.text_input("Enter your email address")
        send = st.form_submit_button("Send Code")
    if send:
        if "@" not in email:
            st.error("Enter a valid email.")
        else:
            st.session_state.email = email
            codes = pd.read_csv(CODES_FILE)
            log_df = pd.read_csv(LOG_FILE) if os.path.exists(LOG_FILE) else pd.DataFrame()
            existing = log_df[log_df["email"] == email]
            if not existing.empty:
                code = existing["code"].values[0]
            else:
                unused = codes[codes["issued"] == False]
                if unused.empty:
                    st.error("No codes available.")
                    st.stop()
                code = unused.iloc[0]["code"]
                codes.loc[codes["code"] == code, "issued"] = True
                codes.to_csv(CODES_FILE, index=False)
                log_event("code_issued", email, code)
                send_email(email, code)
            st.success(f"Access code sent to {email}")
            st.session_state.step = 2
            st.experimental_rerun()

# STEP 2 — Enter code
elif st.session_state.step == 2:
    st.subheader("🗳️ Step 2: Enter Access Code")
    st.info(f"Code sent to: {st.session_state.email}")
    with st.form("code_form"):
        code_input = st.text_input("Enter the code")
        verify = st.form_submit_button("Verify Code")
    if verify:
        codes = pd.read_csv(CODES_FILE)
        row = codes[codes["code"] == code_input]
        if row.empty:
            st.error("Invalid code.")
        elif row.iloc[0]["used"]:
            st.warning("This code has already been used.")
        else:
            st.session_state.code = code_input
            st.session_state.step = 3
            st.experimental_rerun()

# STEP 3 — Voting
elif st.session_state.step == 3:
    st.success("✅ Code accepted. Please vote below.")
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
        vote = st.form_submit_button("Submit Vote")
    if vote:
        if len(issues) > 3:
            st.error("Please select no more than 3 issues.")
        else:
            vote_df = pd.DataFrame([{
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
            }])
            existing_votes = pd.read_csv(VOTES_FILE) if os.path.exists(VOTES_FILE) and os.path.getsize(VOTES_FILE) > 0 else pd.DataFrame(columns=vote_df.columns)
            all_votes = pd.concat([existing_votes, vote_df], ignore_index=True)
            all_votes.to_csv(VOTES_FILE, index=False)
            codes = pd.read_csv(CODES_FILE)
            codes.loc[codes["code"] == st.session_state.code, "used"] = True
            codes.to_csv(CODES_FILE, index=False)
            log_event("vote_cast", st.session_state.email, st.session_state.code)
            st.session_state.step = 4
            st.experimental_rerun()

# STEP 4 — Results
elif st.session_state.step == 4:
    st.subheader("📊 Voting Summary")
    try:
        data = pd.read_csv(VOTES_FILE)
    except pd.errors.EmptyDataError:
        data = pd.DataFrame(columns=[
            "Timestamp", "Code", "Region", "Party", "Preferred Candidate", "Candidate Reason",
            "Age", "Gender", "Diaspora", "Top Issues", "Fairness", "GECOM Trust"
        ])
    if not data.empty:
        st.write("### Votes by Party")
        st.plotly_chart(px.bar(data["Party"].value_counts().reset_index(), x="index", y="Party", labels={"index": "Party", "Party": "Votes"}), use_container_width=True)
        st.write("### Votes by Region")
        st.plotly_chart(px.pie(data, names="Region", title="Votes by Region"), use_container_width=True)
        st.write("### Age and Gender Breakdown")
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(px.pie(data, names="Age", title="Age"), use_container_width=True)
        with col2:
            st.plotly_chart(px.pie(data, names="Gender", title="Gender"), use_container_width=True)
        st.write("### Perceptions")
        col3, col4 = st.columns(2)
        with col3:
            st.plotly_chart(px.pie(data, names="Fairness", title="Fairness"), use_container_width=True)
        with col4:
            st.plotly_chart(px.pie(data, names="GECOM Trust", title="GECOM Trust"), use_container_width=True)
