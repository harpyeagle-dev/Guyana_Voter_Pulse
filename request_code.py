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

# --- Session state init ---
if "step" not in st.session_state:
    st.session_state.step = 1
if "email" not in st.session_state:
    st.session_state.email = ""
if "code" not in st.session_state:
    st.session_state.code = ""
if "pending_vote" not in st.session_state:
    st.session_state.pending_vote = None

# --- Email sender ---
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

# --- Step 1: Request Access Code ---
if st.session_state.step == 1:
    with st.form("request_form"):
        st.subheader("📬 Step 1: Request Access Code")
        email = st.text_input("Enter your email")
        submit = st.form_submit_button("Send Code")

    if submit:
        if "@" not in email or "." not in email:
            st.error("Please enter a valid email address.")
        else:
            try:
                codes = pd.read_csv(CODES_FILE)

                # Select an unused code
                unused = codes[codes["issued"] == False]
                if unused.empty:
                    st.error("No more codes available.")
                    st.stop()

                code = unused.iloc[0]["code"]

                # Mark code as issued
                codes.loc[codes["code"] == code, "issued"] = True
                codes.to_csv(CODES_FILE, index=False)

                # Send code via email
                send_email(email, code)

                # Log the code issue
                log = pd.read_csv(LOG_FILE) if os.path.exists(LOG_FILE) else pd.DataFrame(columns=["timestamp", "event", "email", "code", "source"])
                log = pd.concat([log, pd.DataFrame([{
                    "timestamp": datetime.datetime.now(),
                    "event": "code_issued",
                    "email": email,
                    "code": code,
                    "source": "app"
                }])], ignore_index=True)
                log.to_csv(LOG_FILE, index=False)

                # Store session and move to step 2
                st.session_state.email = email
                st.session_state.step = 2
                st.rerun()

            except Exception as e:
                st.error(f"Something went wrong: {str(e)}")

# --- Step 2: Verify Access Code ---
elif st.session_state.step == 2:
    st.subheader("🗳️ Step 2: Enter Access Code")

    with st.form("verify_form"):
        code_input = st.text_input("Enter the code sent to your email")
        check = st.form_submit_button("Verify Code")

    if check:
        codes = pd.read_csv(CODES_FILE)

        # DEBUG: Show entered code and available codes
        st.write("🔍 You entered:", code_input)
        st.write("📄 Codes in file:", codes["code"].tolist())

        # Clean up input for comparison
        entered = code_input.strip()

        if entered in codes["code"].values:
            match = codes[codes["code"] == entered].iloc[0]

            if match["used"]:
                st.warning("This code has already been used.")
            else:
                st.session_state.code = entered
                st.success("✅ Code verified.")
                st.session_state.step = 3
                st.rerun()
        else:
            st.error("❌ Invalid code. Please check and try again.")

# --- Step 3: Vote Form ---
elif st.session_state.step == 3:
    st.subheader("✅ Step 3: Cast Your Vote")
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
            existing = pd.read_csv(VOTES_FILE) if os.path.exists(VOTES_FILE) and os.path.getsize(VOTES_FILE) > 0 else pd.DataFrame(columns=vote_df.columns)
            pd.concat([existing, vote_df], ignore_index=True).to_csv(VOTES_FILE, index=False)
            codes = pd.read_csv(CODES_FILE)
            codes.loc[codes["code"] == st.session_state.code, "used"] = True
            codes.to_csv(CODES_FILE, index=False)
            st.session_state.step = 4
            st.rerun()

# --- Step 4: Results ---
elif st.session_state.step == 4:
    st.subheader("📊 Voting Summary")
    try:
        data = pd.read_csv(VOTES_FILE)
        if not data.empty:
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(px.bar(data["Party"].value_counts().reset_index(), x="index", y="Party", title="Party Preferences"), use_container_width=True)
            with col2:
                st.plotly_chart(px.pie(data, names="Region", title="Votes by Region"), use_container_width=True)

            col3, col4 = st.columns(2)
            with col3:
                st.plotly_chart(px.pie(data, names="Age", title="Age Breakdown"), use_container_width=True)
            with col4:
                st.plotly_chart(px.pie(data, names="Gender", title="Gender Breakdown"), use_container_width=True)
                        
            col5, col6 = st.columns(2)
            with col5:
                st.plotly_chart(px.pie(data, names="Fairness", title="Perceived Fairness"), use_container_width=True)
            with col6:
                st.plotly_chart(px.pie(data, names="GECOM Trust", title="Trust in GECOM"), use_container_width=True)
    except:
        st.error("No vote data available yet.")
