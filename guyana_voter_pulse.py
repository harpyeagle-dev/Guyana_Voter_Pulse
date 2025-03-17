
import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import os

st.set_page_config(page_title="Guyana Voter Pulse", layout="centered")

st.title("🇬🇾 Guyana Voter Pulse")
st.markdown("#### Indicate your voting preference anonymously")

st.info("🔒 This is **not an official vote**. This platform is for civic engagement and research only. All entries are strictly confidential.")

# Form
with st.form("vote_form"):
    region = st.selectbox("Select your Region", [f"Region {i}" for i in range(1, 11)])
    parties = [
        "People's Progressive Party (PPP)",
        "A Partnership for National Unity (APNU)",
        "Alliance For Change (AFC)",
        "The United Republican Party (URP)",
        "The Liberty and Justice Party (LJP)",
        "The New Movement (TNM)",
        "A New and United Guyana (ANUG)",
        "Federal United Party (FEDUP)",
        "United Party for National Growth and Development (UPNGD)",
        "Other / Independent"
    ]
    party_choice = st.radio("If elections were held today, which party would you vote for?", parties)
    custom_party_candidate = ""
    if party_choice == "Other / Independent":
        custom_party_candidate = st.text_input("Name of the independent candidate or other party representative:")

    age = st.selectbox("Age range (optional)", ["Prefer not to say", "18–24", "25–34", "35–44", "45–54", "55+"])
    gender = st.selectbox("Gender (optional)", ["Prefer not to say", "Male", "Female", "Other"])
    comment = st.text_area("Why are you voting this way? (optional)")

    not_voting_for = st.multiselect("Are there any parties you would NOT vote for?", parties)
    not_vote_reason = st.text_area("Why would you not vote for the selected party/parties? (optional)")

    preferred_candidate = st.text_input("Who is your preferred candidate (for President or Prime Minister)?")
    candidate_reason = st.text_area("Why this candidate? (optional)")

    diaspora = st.radio("Are you currently living in Guyana or abroad?", ["In Guyana", "Diaspora (abroad)"])

    issues = st.multiselect(
        "What are the top issues influencing your vote? (Choose up to 3)",
        ["Jobs", "Education", "Healthcare", "Cost of living", "Crime", "Corruption", "Infrastructure", "Environmental issues", "Freedom of speech"]
    )

    ethnicity = st.selectbox("What is your ethnicity?", [
        "Prefer not to say", "African-Guyanese", "Indo-Guyanese", "Amerindian", "Mixed", "Other"
    ])

    community = st.selectbox("Which community or group do you most identify with? (optional)", [
        "Prefer not to say", "African-Guyanese", "Indo-Guyanese", "Amerindian", "Mixed heritage", "Portuguese", "Chinese", "Other"
    ])

    voted_last = st.radio("Did you vote in the last national election?", ["Yes", "No", "Can't remember", "Prefer not to say"])

    perception = st.radio("Do you believe the upcoming election will be fair and transparent?", ["Yes", "No", "Not sure"])
    gecom_trust = st.radio("Do you agree that the Guyana Elections Commission will deliver an electoral process of international standards?", ["Yes", "No", "Not sure"])

    submitted = st.form_submit_button("Submit Vote")

    if submitted:
        new_vote = {
            "Timestamp": datetime.datetime.now(),
            "Region": region,
            "Party": party_choice,
            "Independent Candidate (if any)": custom_party_candidate,
            "Age": age,
            "Gender": gender,
            "Comment": comment,
            "Not Voting For": ", ".join(not_voting_for),
            "Reason for Not Voting": not_vote_reason,
            "Preferred Candidate": preferred_candidate,
            "Candidate Reason": candidate_reason,
            "Diaspora": diaspora,
            "Top Issues": ", ".join(issues),
            "Ethnicity": ethnicity,
            "Community": community,
            "Voted Last Election": voted_last,
            "Perception of Fairness": perception,
            "Trust in GECOM (International Standards)": gecom_trust
        }

        if os.path.exists("votes.csv"):
            df = pd.read_csv("votes.csv")
            df = df.append(new_vote, ignore_index=True)
        else:
            df = pd.DataFrame([new_vote])

        df.to_csv("votes.csv", index=False)
        st.success("✅ Your vote has been recorded anonymously!")

# Show results
st.markdown("## 📊 Live Results (based on submitted votes)")
if os.path.exists("votes.csv"):
    data = pd.read_csv("votes.csv")
    count_by_party = data["Party"].value_counts().reset_index()
    count_by_party.columns = ["Party", "Votes"]
    fig = px.bar(count_by_party, x="Party", y="Votes", color="Party", title="Voting Preferences")
    st.plotly_chart(fig, use_container_width=True)

    if st.checkbox("Show region-wise breakdown"):
        region_filter = st.selectbox("Choose a Region", sorted(data["Region"].unique()))
        filtered = data[data["Region"] == region_filter]
        party_counts = filtered["Party"].value_counts().reset_index()
        party_counts.columns = ["Party", "Votes"]
        fig2 = px.pie(party_counts, names="Party", values="Votes", title=f"Votes in {region_filter}")
        st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("No votes recorded yet. Be the first to participate!")
