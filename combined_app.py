
import streamlit as st
import pandas as pd
import datetime
import smtplib
from email.mime.text import MIMEText
import os
import plotly.express as px

st.set_page_config(page_title="Guyana Voter Pulse", layout="wide")
st.title("🇬🇾 Guyana Voter Pulse – Request & Vote")

EMAIL_ADDRESS = st.secrets["EMAIL"]["address"]
EMAIL_PASSWORD = st.secrets["EMAIL"]["password"]

CODES_FILE = "valid_codes.csv"
LOG_FILE = "usage_log.csv"
VOTES_FILE = "votes.csv"

# Initialize session state
for key in ["step", "user_email", "code"]:
    if key not in st.session_state:
        st.session_state[key] = None

# Function to send email
def send_email(to_email, code):
    subject = "Your Guyana Voter Access Code"
    body = f"""Thank you for requesting your voting code.

Your one-time access code is: {code}

Please return to the app and enter this code to cast your vote.

Guyana Voter Pulse Team
"""
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)

def log_event(event, email, code, source="combined_app"):
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

# Step 1: Request access code
if st.session_state.step is None or st.session_state.step == 1:
    with st.form("email_form"):
        st.subheader("📬 Step 1: Request Access Code")
        email = st.text_input("Enter your email address")
        submit_email = st.form_submit_button("Send Code")

    if submit_email:
        if "@" not in email:
            st.error("Enter a valid email address.")
        else:
            codes = pd.read_csv(CODES_FILE)
            issued_log = pd.read_csv(LOG_FILE) if os.path.exists(LOG_FILE) else pd.DataFrame()
            existing = issued_log[issued_log["email"] == email]
            if not existing.empty:
                code = existing["code"].values[0]
            else:
                unused = codes[codes["issued"] == False]
                if unused.empty:
                    st.error("No more codes available.")
                    st.stop()
                code = unused.iloc[0]["code"]
                codes.loc[codes["code"] == code, "issued"] = True
                codes.to_csv(CODES_FILE, index=False)
                log_event("code_issued", email, code)
                send_email(email, code)
            st.session_state.user_email = email
            st.session_state.step = 2
            st.experimental_rerun()

# Step 2: Enter code
elif st.session_state.step == 2:
    with st.form("code_form"):
        st.subheader("🗳️ Step 2: Enter Your Access Code")
        entered_code = st.text_input("Enter the code sent to your email")
        submit_code = st.form_submit_button("Validate Code")

    if submit_code:
        codes = pd.read_csv(CODES_FILE)
        row = codes[codes["code"] == entered_code]
        if row.empty:
            st.error("Invalid code.")
        elif row.iloc[0]["used"]:
            st.warning("Code has already been used.")
        else:
            st.session_state.code = entered_code
            st.session_state.step = 3
            st.experimental_rerun()

# Step 3: Voting form
elif st.session_state.step == 3:
    st.success("Code verified. Please cast your vote.")
    with st.form("vote_form"):
        region = st.selectbox("Region", [f"Region {i}" for i in range(1, 11)])
        party = st.selectbox("Party", ["-- Select a Party --", "PPP", "APNU", "AFC", "LJP", "URP", "TNM", "ANUG", "ALP", "GAP", "Other"], index=0)
        candidate = st.text_input("Who is your preferred presidential candidate?")
        candidate_reason = st.text_area("Why this candidate? (optional)")
        age = st.selectbox("Age", ["18–24", "25–34", "35–44", "45–54", "55+"])
        gender = st.radio("Gender", ["Male", "Female", "Other"])
        diaspora = st.radio("Where do you live?", ["In Guyana", "Diaspora"])
        issues = st.multiselect("Top 3 issues influencing your vote", ["Jobs", "Education", "Healthcare", "Cost of living", "Crime", "Corruption", "Infrastructure"])
        fair = st.radio("Do you believe the election will be fair?", ["Yes", "No", "Not sure"])
        gecom = st.radio("Trust in GECOM?", ["Yes", "No", "Not sure"])
        submit_vote = st.form_submit_button("Submit Vote")

    if submit_vote:
        if len(issues) > 3:
            st.error("Select up to 3 issues.")
        else:
            vote = pd.DataFrame([{
                "Timestamp": datetime.datetime.now(),
                "Code": st.session_state.code,
                "Region": region,
                "Party": party,
                "Preferred Candidate": candidate,
                "Candidate Reason": candidate_reason,
                "Age": age,
                "Gender": gender,
                "Diaspora": diaspora,
                "Top Issues": ", ".join(issues),
                "Fairness": fair,
                "GECOM Trust": gecom
            }])
            votes = pd.read_csv(VOTES_FILE) if os.path.exists(VOTES_FILE) else pd.DataFrame()
            votes = pd.concat([votes, vote], ignore_index=True)
            votes.to_csv(VOTES_FILE, index=False)
            codes = pd.read_csv(CODES_FILE)
            codes.loc[codes["code"] == st.session_state.code, "used"] = True
            codes.to_csv(CODES_FILE, index=False)
            log_event("vote_cast", "", st.session_state.code)
            st.session_state.step = 4
            st.experimental_rerun()

# Step 4: Show results
elif st.session_state.step == 4:
    st.subheader("📊 Live Voting Results")
    if os.path.exists(VOTES_FILE):
        data = pd.read_csv(VOTES_FILE)

        col1, col2 = st.columns(2)
        with col1:
            fig1 = px.bar(data["Party"].value_counts().reset_index(), x="index", y="Party", title="Party Preferences", labels={"index": "Party", "Party": "Votes"})
            st.plotly_chart(fig1, use_container_width=True)
        with col2:
            fig2 = px.pie(data, names="Region", title="Votes by Region")
            st.plotly_chart(fig2, use_container_width=True)

        col3, col4 = st.columns(2)
        with col3:
            fig3 = px.pie(data, names="Age", title="Age Distribution")
            st.plotly_chart(fig3, use_container_width=True)
        with col4:
            fig4 = px.pie(data, names="Gender", title="Gender Breakdown")
            st.plotly_chart(fig4, use_container_width=True)

        st.subheader("🧠 Perceptions")
        col5, col6 = st.columns(2)
        with col5:
            st.plotly_chart(px.pie(data, names="Fairness", title="Perceived Fairness"), use_container_width=True)
        with col6:
            st.plotly_chart(px.pie(data, names="GECOM Trust", title="Trust in GECOM"), use_container_width=True)
