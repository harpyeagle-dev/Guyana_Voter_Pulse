
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
    party_choice = st.radio("Which party do you currently support?", parties)
    age = st.selectbox("Age range (optional)", ["Prefer not to say", "18–24", "25–34", "35–44", "45–54", "55+"])
    gender = st.selectbox("Gender (optional)", ["Prefer not to say", "Male", "Female", "Other"])
    comment = st.text_area("Why are you voting this way? (optional)")

    submitted = st.form_submit_button("Submit Vote")

    if submitted:
        new_vote = {
            "Timestamp": datetime.datetime.now(),
            "Region": region,
            "Party": party_choice,
            "Age": age,
            "Gender": gender,
            "Comment": comment
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
