# streamlit_app.py
import streamlit as st
import json
from openai import OpenAI

# ----------------------------
# Initialize OpenAI client
# ----------------------------
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])  # Store your key in .streamlit/secrets.toml


def askAI(prompt):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content


# ----------------------------
# Agent 1: Planning Agent
# ----------------------------
def get_diagnostic_plan(patient_input):
    prompt = f"""         
You are a medical planning agent. Based solely on the information provided below — 
without the patient being physically present — break down the case into a clear, medically sound diagnostic plan.

Return the output as a JSON array of objects.

Each object must contain:
- "step_number": the step number
- "instruction": an actionable diagnostic or evaluation step.

Patient Data:
{patient_input}
"""
    ai_response = askAI(prompt)
    return json.loads(ai_response)


# ----------------------------
# Agent 2: Worker Agent
# ----------------------------
def perform_diagnostic_step(step, accumulated_context):
    prompt = f"""
You are a medical assistant AI. Execute the following diagnostic instruction:

Instruction: {step['instruction']}

Patient context so far:
{accumulated_context}

Respond with the output of this step in clearly formatted text or JSON.
"""
    step_output = askAI(prompt)
    return step_output


def run_full_diagnostic_plan(diagnostic_steps, patient_input):
    accumulated_context = {"patient_input": patient_input}
    step_results = []
    for step in diagnostic_steps:
        result = perform_diagnostic_step(step, accumulated_context)
        step_results.append({"step": step, "result": result})
        accumulated_context[f"Step{step['step_number']}"] = result
    return step_results


# ----------------------------
# Agent 3: Orchestrator Agent
# ----------------------------
def create_diagnostic_summary(diagnostic_outputs, patient_input):
    prompt = f"""
You are a medical orchestrator AI. The user has input: {patient_input}
You received the following results from medical worker agents:

{diagnostic_outputs}

Synthesize a final diagnostic summary that:
- Interprets all findings
- Lists suspected diseases
- Suggests tests
- Advises next medical steps

Respond in clear bullet points.
"""
    return askAI(prompt)


# ----------------------------
# Streamlit UI
# ----------------------------
st.set_page_config(page_title="AI Medical Diagnostics System", layout="wide")

st.title("🧑‍⚕️ AI-Powered Multi-Agent Medical Diagnostics")
st.markdown("This system uses **three AI agents** to plan, execute, and summarize medical diagnostics.")

# Sidebar Navigation
page = st.sidebar.radio("🔍 Navigate", ["Patient Input", "Planning Agent", "Worker Agent", "Orchestrator Agent"])

# Patient Input Section
if page == "Patient Input":
    st.subheader("📝 Enter Patient Symptoms")
    patient_input = st.text_area("Patient Case", 
        "I’ve been experiencing chest pain, especially when I breathe deeply, fatigue, and shortness of breath after climbing stairs.\nI have a history of mild asthma but no recent attacks.")
    
    if st.button("Run Diagnostics"):
        st.session_state["patient_input"] = patient_input
        st.session_state["diagnostic_steps"] = get_diagnostic_plan(patient_input)
        st.session_state["diagnostic_outputs"] = run_full_diagnostic_plan(st.session_state["diagnostic_steps"], patient_input)
        st.session_state["final_summary"] = create_diagnostic_summary(st.session_state["diagnostic_outputs"], patient_input)
        st.success("Diagnostics Completed ✅")

# Planning Agent
elif page == "Planning Agent":
    st.subheader("🧩 Diagnostic Plan")
    if "diagnostic_steps" in st.session_state:
        for step in st.session_state["diagnostic_steps"]:
            with st.expander(f"Step {step['step_number']}"):
                st.write(step["instruction"])
    else:
        st.warning("Please run diagnostics first.")

# Worker Agent
elif page == "Worker Agent":
    st.subheader("⚙️ Worker Agent Results")
    if "diagnostic_outputs" in st.session_state:
        for output in st.session_state["diagnostic_outputs"]:
            with st.container():
                st.markdown(f"### Step {output['step']['step_number']}: {output['step']['instruction']}")
                st.write(output["result"])
                st.divider()
    else:
        st.warning("Please run diagnostics first.")

# Orchestrator Agent
elif page == "Orchestrator Agent":
    st.subheader("📋 Final Diagnostic Summary")
    if "final_summary" in st.session_state:
        st.info(st.session_state["final_summary"])
    else:
        st.warning("Please run diagnostics first.")
