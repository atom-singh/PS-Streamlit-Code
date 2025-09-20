import os
from dotenv import load_dotenv

import streamlit as st
import json
from openai import OpenAI

# Load environment variables from .env file
#load_dotenv()
#openai_api_key = os.getenv('OPENAI_API_KEY')
#serper_api_key = os.environ.get("SERPER_API_KEY")

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])  # Store your key in .streamlit/secrets.toml
#client = OpenAI(api_key=openai_api_key)

# ---------------- Functions ---------------- #
# Step 1: Extract Pros and Cons
def extract_pros_cons(product_reviews):
    pros_cons_prompt = f"""
    You are a professional customer review analyst.

    Your task is to extract key **pros and cons** from each review. 
    Provide the output as a **list of dictionaries**, where each dictionary contains:
    - "pros": a list of positive points
    - "cons": a list of negative points

    Only include factual or sentiment-backed observations (not vague statements).

    Here are the reviews:
    {product_reviews}
    """
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role":"user", "content":pros_cons_prompt}]
    )
    return response.choices[0].message.content

# Step 2: Group common feedback
def group_feedback(step_1_output):
    group_feedback_prompt = f"""
    You are an AI assistant helping to synthesize customer feedback.

    From the extracted pros and cons below, identify **common themes** by grouping 
    similar or semantically equivalent feedback into categories.

    Return a JSON object with:
    - "common_pros": List of grouped positive themes
    - "common_cons": List of grouped negative themes

    Avoid repeating similar items.

    Extracted feedback:
    {step_1_output}
    """
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role":"user", "content":group_feedback_prompt}]
    )
    return response.choices[0].message.content

# Step 3: Generate Summary
def generate_summary(step_2_output):
    generate_prompt = f"""
    You are an AI product analyst.

    Using the grouped customer feedback below, write a professional summary 
    highlighting the main strengths and weaknesses of the product.

    Structure:
    **Strengths**
    - Bullet point 1
    - Bullet point 2
    - ...

    **Weaknesses**
    - Bullet point 1
    - Bullet point 2
    - ...

    Limit each section to 3–4 concise points.

    Grouped Feedback:
    {step_2_output}
    """
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role":"user", "content":generate_prompt}]
    )
    return response.choices[0].message.content

# ---------------- Streamlit UI ---------------- #
st.set_page_config(page_title="Customer Review Analyzer", layout="wide")

st.title("📊 Customer Review Analyzer")
st.markdown("Upload a JSON file with product reviews and get structured insights.")

uploaded_file = st.file_uploader("Upload your reviews (JSON format)", type=["json"])

if uploaded_file:
    try:
        product_reviews = json.load(uploaded_file)
        st.success("✅ File uploaded successfully!")

        if st.button("Run Feedback Analysis"):
            with st.spinner("🔍 Extracting pros and cons..."):
                step1_output = extract_pros_cons(product_reviews)
            with st.expander("Step 1: Pros & Cons Extraction", expanded=True):
                st.json(step1_output)

            with st.spinner("📊 Grouping feedback..."):
                step2_output = group_feedback(step1_output)
            with st.expander("Step 2: Grouped Feedback", expanded=False):
                st.json(step2_output)

            with st.spinner("📝 Generating summary..."):
                final_summary = generate_summary(step2_output)
            with st.expander("Step 3: Final Summary", expanded=True):
                st.markdown(final_summary)

    except Exception as e:
        st.error(f"Error reading file: {e}")

else:
    st.info("Please upload a JSON file with reviews to begin.")
