import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import os

st.set_page_config(page_title="Guyana Voter Pulse", layout="wide")
st.title("🇬🇾 Guyana Voter Pulse")

codes_file = "valid_codes.csv"
log_file = "usage_log.csv"
votes_file = "votes.csv"

def log_event(event, email, code, source="voter_app"):
    log = pd.read_csv(log_file) if os.path.exists(log_file) else pd.DataFrame(columns=["timestamp", "event", "email", "code", "source"])
    log = log.append({
        "timestamp": datetime.datetime.now(),
        "event": event,
        "email": email,
        "code": code,
        "source": source
    }, ignore_index=True)
    log.to_csv(log_file, index=False)

code = st.text_input("Enter your access code")

if code:
    codes = pd.read_csv(codes_file)
    code_row = codes[codes["code"] == code]

    if code_row.empty:
        st.error("Invalid code.")
        st.stop()
    elif code_row.iloc[0]["used"]:
        st.warning("This code has already been used.")
        st.stop()
    else:
        st.success("✅ Code accepted. Please cast your vote.")

        with st.form("vote_form"):
            region = st.selectbox("Region", [f"Region {i}" for i in range(1, 11)])
            party = st.selectbox("Party", ["-- Select a Party --", "PPP", "APNU", "AFC", "LJP", "URP", "TNM", "ANUG", "ALP", "Other"], index=0)
            age = st.selectbox("Age", ["18–24", "25–34", "35–44", "45–54", "55+"])
            gender = st.radio("Gender", ["Male", "Female", "Other"])
            diaspora = st.radio("Where do you live?", ["In Guyana", "Diaspora"])
            issues = st.multiselect("Top Issues", ["Jobs", "Education", "Healthcare", "Cost of living", "Crime", "Corruption", "Infrastructure"])
            fair = st.radio("Do you believe the election will be fair?", ["Yes", "No", "Not sure"])
            gecom = st.radio("Trust in GECOM?", ["Yes", "No", "Not sure"])
            submit = st.form_submit_button("Submit Vote")

        if submit:
            vote = pd.DataFrame([{
                "Timestamp": datetime.datetime.now(),
                "Code": code,
                "Region": region,
                "Party": party,
                "Age": age,
                "Gender": gender,
                "Diaspora": diaspora,
                "Top Issues": ", ".join(issues),
                "Fairness": fair,
                "GECOM Trust": gecom
            }])
            if os.path.exists(votes_file):
                votes = pd.read_csv(votes_file)
                votes = votes.append(vote, ignore_index=True)
            else:
                votes = vote
            votes.to_csv(votes_file, index=False)
            codes.loc[codes["code"] == code, "used"] = True
            codes.to_csv(codes_file, index=False)
            log_event("vote_cast", "", code)
            st.success("✅ Your vote has been recorded.")

# Show visualizations
if os.path.exists(votes_file):
    data = pd.read_csv(votes_file)
    st.subheader("📊 Voting Trends")

    col1, col2 = st.columns(2)
    with col1:
        fig1 = px.bar(data["Party"].value_counts().reset_index(), x="index", y="Party", labels={"index": "Party", "Party": "Votes"}, title="Party Preferences")
        st.plotly_chart(fig1, use_container_width=True)
    with col2:
        fig2 = px.pie(data, names="Region", title="Votes by Region")
        st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        fig3 = px.pie(data, names="Age", title="Voter Age Groups")
        st.plotly_chart(fig3, use_container_width=True)
    with col4:
        fig4 = px.pie(data, names="Gender", title="Gender Distribution")
        st.plotly_chart(fig4, use_container_width=True)

    st.subheader("🧠 Perceptions")
    col5, col6 = st.columns(2)
    with col5:
        st.plotly_chart(px.pie(data, names="Fairness", title="Perceived Election Fairness"), use_container_width=True)
    with col6:
        st.plotly_chart(px.pie(data, names="GECOM Trust", title="Trust in GECOM"), use_container_width=True)
