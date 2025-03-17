
import streamlit as st
import pandas as pd
import datetime
import smtplib
from email.mime.text import MIMEText
import os

st.set_page_config(page_title="Request Voter Access Code", layout="centered")
st.title("📬 Request Your One-Time Voting Code")

EMAIL_ADDRESS = st.secrets["EMAIL"]["address"]
EMAIL_PASSWORD = st.secrets["EMAIL"]["password"]

codes_file = "valid_codes.csv"
log_file = "usage_log.csv"

def send_email(to_email, code):
    subject = "Your Guyana Voter Access Code"
    body = f"""Thank you for requesting your voting code.

Your one-time access code is: {code}

Please visit the voting platform and enter this code to cast your vote.

Guyana Voter Pulse Team
"""
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)

def log_event(event, email, code, source="request_code"):
    log = pd.read_csv(log_file) if os.path.exists(log_file) else pd.DataFrame(columns=["timestamp", "event", "email", "code", "source"])
    new_entry = pd.DataFrame([{
        "timestamp": datetime.datetime.now(),
        "event": event,
        "email": email,
        "code": code,
        "source": source
    }])
    log = pd.concat([log, new_entry], ignore_index=True)
    log.to_csv(log_file, index=False)

st.markdown("Enter your email to receive a one-time access code.")

email = st.text_input("Email address")

if st.button("Request Code"):
    if not email or "@" not in email:
        st.error("Please enter a valid email address.")
    else:
        codes = pd.read_csv(codes_file)
        issued = codes[codes["issued"] == True]
        already_issued = pd.read_csv(log_file) if os.path.exists(log_file) else pd.DataFrame()

        if email in already_issued["email"].values:
            code = already_issued[already_issued["email"] == email]["code"].values[0]
            st.info(f"A code has already been issued to this email: {code}")
        else:
            unused = codes[codes["issued"] == False]
            if unused.empty:
                st.error("No codes left to issue.")
            else:
                code = unused.iloc[0]["code"]
                codes.loc[codes["code"] == code, "issued"] = True
                codes.to_csv(codes_file, index=False)
                log_event("code_issued", email, code)
                try:
                    send_email(email, code)
                    st.success(f"Code sent to {email}")
                except Exception as e:
                    st.error(f"Error sending email: {e}")
