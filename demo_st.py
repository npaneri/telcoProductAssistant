# streamlit_app.py
import streamlit as st
from telecom_product_crew import run_telecom_product_crew  # We'll create this helper from your existing code

st.set_page_config(page_title="Telecom Product Designer", layout="centered")
st.title("Telecom Product Design Assistant")
st.markdown("""
Hello, I am Telecom Product Manager Assistant. I can help you in your day to day tasks like product market research,product ideas, competition analysis etc.
            Enter your **telecom product prompt** below. I shall do my best to give you expected output. Make sure you include needed information. 
            Few examples are as below

Examples:
- "List all competition plan priced at 3 Euro in UK with operator name, plan details."
- "Suggest a new prepaid product in India for students at 199 INR."
- "Give a new product idea to offer data packs to customers in Germany at 2 Euros."
""")

user_input = st.text_area("Enter Prompt:", height=150)

if st.button("Submit"):
    if not user_input.strip():
        st.warning("Please enter a valid prompt before submitting.")
    else:
        with st.spinner("Analyzing your request, researching market, and preparing a response..."):
            result = run_telecom_product_crew(user_input)

        if result.startswith("RESPONSE_"):
            st.error(result)
        else:
            st.success("Done")
            st.markdown("**Generated Recommendation:**")
            st.markdown(f"```text\n{result}\n```)")
