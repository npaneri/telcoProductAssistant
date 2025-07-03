# demo_st.py
import streamlit as st
import pandas as pd
from telecom_product_crew import run_telecom_product_crew

st.set_page_config(page_title="📡 Telecom Product Designer", layout="wide")

# --- Load Share List and Track Sessions ---
SHARE_FILE = "share.csv"
if "query_count" not in st.session_state:
    st.session_state.query_count = 0

# --- Sidebar Branding and Instructions ---
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/Telecom-icon.svg/1200px-Telecom-icon.svg.png", width=100)
st.sidebar.markdown("## 📞 Telecom Design Assistant")
st.sidebar.markdown("Use this app to validate telecom ideas, analyze the market, and get GenAI-driven product suggestions.")

# --- User Authentication State Check ---
user_verified = st.session_state.get("user_verified", False)
max_queries = st.session_state.get("max_queries", 0)

if not user_verified:
    st.title("📡 Telecom Product Design Assistant")
    with st.form(key="auth_form"):
        name = st.text_input("👤 Your Name")
        email = st.text_input("📧 Your Email")
        submitted = st.form_submit_button("🔓 Submit")

    if submitted:
        try:
            share_df = pd.read_csv(SHARE_FILE)
            match = share_df[share_df['email'].str.lower() == email.strip().lower()]
            if not match.empty:
                st.session_state.user_verified = True
                st.session_state.user_name = name
                st.session_state.user_email = email
                st.session_state.max_queries = int(match.iloc[0]['max queries'])
                st.success(f"Welcome {name}! This demo permits you with {st.session_state.max_queries} queries.")
                st.experimental_rerun()
            else:
                st.error("❌ You are not authorized to access this demo. Please contact the demo provider.")
        except Exception as e:
            st.error(f"Error loading access list: {e}")

# --- Prompt UI only if verified ---
if st.session_state.get("user_verified", False):
    max_queries = st.session_state.get("max_queries", 0)
    user_name = st.session_state.get("user_name", "")
    st.title(f"📡 Welcome {user_name}!")
    st.markdown(f"You have used {st.session_state.query_count} out of {max_queries} allowed queries.")

    st.markdown("""
    Enter your **telecom product prompt** below. The system will validate it, analyze market data, and propose a concise product recommendation.

    ### 🔍 Example Prompts
    - "List all competition plan priced at 3 Euro in UK with operator name, plan details."
    - "Suggest a new prepaid product in India for students at 199 INR."
    """)

    user_input = st.text_area("✍️ Enter your telecom prompt:", height=150)

    with st.expander("💡 Prompt Examples"):
        st.markdown("""
        - Suggest 5G postpaid product in Germany under 20 Euro
        - What’s the right price for unlimited data in Italy for youth?
        - List all competition in France for 5 euro prepaid plans
        """)

    if st.button("🚀 Submit"):
        if st.session_state.query_count >= max_queries:
            st.error("🚫 You have reached your query limit. Please contact us to increase access.")
        elif not user_input.strip():
            st.warning("⚠️ Please enter a valid prompt before submitting.")
        else:
            with st.spinner("Analyzing your request, researching market, and synthesizing a strategy..."):
                result = run_telecom_product_crew(user_input)

            st.session_state.query_count += 1

            if result.startswith("RESPONSE_"):
                st.error(result)
            else:
                st.success("✅ AI Recommendation Ready!")
                st.markdown("### 📌 Generated Recommendation:")
                st.markdown(f"""```text\n{result}\n```""")

                st.download_button(
                    label="💾 Download Output as TXT",
                    data=result,
                    file_name="telecom_recommendation.txt",
                    mime="text/plain"
                )

    st.markdown("---")
    st.markdown("### 📝 Feedback")
    feedback = st.text_area("Have thoughts or suggestions for improvement? Leave them here:")
    if st.button("📨 Submit Feedback"):
        if feedback.strip():
            st.success("🙏 Thanks for your feedback! (Note: You can wire this to send to email/DB)")
        else:
            st.warning("⚠️ Feedback cannot be empty.")
