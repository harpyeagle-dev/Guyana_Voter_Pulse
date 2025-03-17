
import streamlit as st
import pandas as pd
import datetime
import smtplib
from email.mime.text import MIMEText
import os

st.set_page_config(page_title="Request Voter Access Code", layout="centered")
st.title("📬 Request Your One-Time Voting Code")

# Load email credentials securely
EMAIL_ADDRESS = st.secrets["EMAIL"]["address"]
EMAIL_PASSWORD = st.secrets["EMAIL"]["password"]

CODES_FILE = "valid_codes.csv"
ISSUED_FILE = "issued_codes.csv"

def load_codes():
    if os.path.exists(CODES_FILE):
        return pd.read_csv(CODES_FILE)
    else:
        return pd.DataFrame(columns=["code", "used"])

def load_issued():
    if os.path.exists(ISSUED_FILE):
        return pd.read_csv(ISSUED_FILE)
    else:
        return pd.DataFrame(columns=["email", "code", "timestamp"])

def save_issued(df):
    df.to_csv(ISSUED_FILE, index=False)

def send_email(to_email, code):
    subject = "Your Guyana Voter Access Code"
    body = f"""Thank you for requesting your voting code.

Your one-time access code is: {code}

Please visit the voting platform and enter this code to cast your vote. This code can only be used once.

Guyana Voter Pulse Team
"""
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)

# App logic
st.markdown("Enter your email address to receive your one-time access code for the Guyana Voter Pulse platform.")

user_email = st.text_input("Your Email Address")

if st.button("Request Access Code"):
    if not user_email or "@" not in user_email:
        st.error("Please enter a valid email address.")
    else:
        codes_df = load_codes()
        issued_df = load_issued()

        # Check if already issued
        if user_email in issued_df["email"].values:
            code_row = issued_df[issued_df["email"] == user_email]
            existing_code = code_row["code"].values[0]
            st.info(f"A code was already sent to this email: {existing_code}")
        else:
            available_codes = codes_df[codes_df["used"] == False]
            if available_codes.empty:
                st.error("No available codes at the moment. Please try again later.")
            else:
                new_code = available_codes.iloc[0]["code"]
                codes_df.loc[codes_df["code"] == new_code, "used"] = True
                codes_df.to_csv(CODES_FILE, index=False)

                issued_df = issued_df.append({
                    "email": user_email,
                    "code": new_code,
                    "timestamp": datetime.datetime.now()
                }, ignore_index=True)
                save_issued(issued_df)

                try:
                    send_email(user_email, new_code)
                    st.success(f"Access code sent to {user_email}. Check your inbox!")
                except Exception as e:
                    st.error(f"Failed to send email: {e}")
