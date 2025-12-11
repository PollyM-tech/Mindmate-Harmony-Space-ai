import streamlit as st
import requests
import subprocess
import json
from datetime import datetime, timezone
from typing import Any, Dict

API_BASE_URL = "http://localhost:8000"  # optional Jac HTTP bridge; fallback to CLI if unavailable
JAC_MODULE_PATH = "/home/hmungania/code/mindharmony.jac"  # path to your Jac backend file

st.set_page_config(page_title="MindHarmony UI", layout="wide")

def call_walker_http(walker: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        url = f"{API_BASE_URL}/walker/{walker}"
        r = requests.post(url, json=payload, timeout=10)
        # If the bridge returns 404 for missing walker, capture it and return specific error
        if r.status_code == 404:
            return {"error": f"http_404: walker not found ({walker}) at {url}"}
        r.raise_for_status()
        return r.json()
    except requests.exceptions.HTTPError as e:
        # If response present, inspect status code
        status = None
        if e.response is not None:
            status = e.response.status_code
        if status == 404:
            return {"error": f"http_404: walker not found ({walker}) at {url}"}
        return {"error": f"http_error: {str(e)}"}
    except Exception as e:
        return {"error": f"http_error: {str(e)}"}

def call_walker_cli(walker: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    # Build jac CLI arguments: jac run <module> --run Walker key=json_value ...
    cmd = ["jac", "run", JAC_MODULE_PATH, "--run", walker]
    for k, v in payload.items():
        # ensure value serialized as JSON for safe CLI parsing
        cmd.append(f"{k}={json.dumps(v)}")
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except Exception as e:
        return {"error": f"cli_exec_error: {str(e)}"}
    if proc.returncode != 0:
        return {"error": "jac_error", "stderr": proc.stderr, "stdout": proc.stdout}
    # try parse stdout as json
    try:
        return json.loads(proc.stdout)
    except Exception:
        # fallback: return raw stdout/stderr
        return {"stdout": proc.stdout, "stderr": proc.stderr}

def call_walker(walker: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    # Try HTTP first
    res = call_walker_http(walker, payload)
    # If HTTP bridge indicates a missing route (404) or other http error, fallback to CLI
    if isinstance(res, dict) and "error" in res and (res["error"].startswith("http_error") or res["error"].startswith("http_404")):
        st.warning(f"HTTP bridge unavailable or walker not found for '{walker}'. Falling back to jac CLI.")
        return call_walker_cli(walker, payload)
    return res

st.title("BetterHealthAi")
st.markdown("BetterHealthAi Mental Health Assesment Platform.")

col1, col2 = st.columns(2)

with col1:
    st.header("Register Patient")
    with st.form("register_form"):
        patient_id = st.text_input("Patient ID", value="patient_001")
        name = st.text_input("Name", value="John Doe")
        email = st.text_input("Email", value="john@example.com")
        age = st.number_input("Age", min_value=0, max_value=120, value=28)
        assessment_type = st.selectbox("Assessment Type", ["initial", "follow-up", "crisis"])
        num_questions = st.number_input("Number of Questions", min_value=1, max_value=50, value=10)
        medical_history = st.text_area("Medical history (optional)", value="")
        submitted = st.form_submit_button("Register")
        if submitted:
            payload = {
                "assessment_context": {
                    "assessment_type": assessment_type,
                    "number_of_questions": int(num_questions)
                },
                "patients": [
                    {
                        "patient_id": patient_id,
                        "name": name,
                        "email": email,
                        "age": int(age),
                        "medical_history": medical_history
                    }
                ]
            }
            resp = call_walker("RegisterPatientWalker", payload)
            st.json(resp)

with col2:
    st.header("Start Assessment")
    with st.form("start_form"):
        start_patient_id = st.text_input("Patient ID", value="patient_001")
        start_assessment_type = st.selectbox("Assessment Type (start)", ["initial", "follow-up", "crisis"])
        focus_areas = st.text_input("Focus areas (comma separated)", value="anxiety, sleep")
        start_sub = st.form_submit_button("Start Assessment")
        if start_sub:
            payload = {
                "patient_id": start_patient_id,
                "assessment_type": start_assessment_type,
                "focus_areas": [s.strip() for s in focus_areas.split(",") if s.strip()]
            }
            resp = call_walker("StartAssessmentWalker", payload)
            st.json(resp)

st.markdown("---")

col3, col4 = st.columns(2)

with col3:
    st.header("Submit Assessment Answer")
    with st.form("answer_form"):
        ans_patient_id = st.text_input("Patient ID", value="patient_001", key="ans_pid")
        question = st.text_area("Question", value="How have you been feeling lately?", key="q")
        answer = st.text_area("Answer", value="", key="a")
        ans_sub = st.form_submit_button("Submit Answer")
        if ans_sub:
            payload = {"patient_id": ans_patient_id, "question": question, "answer": answer}
            resp = call_walker("SubmitAssessmentAnswerWalker", payload)
            st.json(resp)

with col4:
    st.header("Submit Journal Entry")
    with st.form("journal_form"):
        j_patient_id = st.text_input("Patient ID", value="patient_001", key="j_pid")
        journal_content = st.text_area("Journal content", value="Today was hard...", key="jc")
        mood_score = st.slider("Mood score", 0, 10, 5)
        created_at = st.text_input("Created at (ISO)", value=datetime.now(timezone.utc).isoformat(), key="ja")
        j_sub = st.form_submit_button("Submit Journal")
        if j_sub:
            payload = {
                "patient_id": j_patient_id,
                "journal_content": journal_content,
                "created_at": created_at,
                "mood_score": int(mood_score)
            }
            resp = call_walker("SubmitJournalEntryWalker", payload)
            st.json(resp)

st.markdown("---")

col5, col6 = st.columns(2)

with col5:
    st.header("Generate Recommendations")
    with st.form("gen_form"):
        g_patient_id = st.text_input("Patient ID", value="patient_001", key="g_pid")
        g_created_at = st.text_input("Created at (ISO)", value=datetime.now(timezone.utc).isoformat(), key="g_time")
        g_sub = st.form_submit_button("Generate")
        if g_sub:
            payload = {"patient_id": g_patient_id, "created_at": g_created_at}
            resp = call_walker("GenerateRecommendationsWalker", payload)
            st.json(resp)

with col6:
    st.header("Session Summary")
    with st.form("summary_form"):
        s_patient_id = st.text_input("Patient ID", value="patient_001", key="s_pid")
        s_sub = st.form_submit_button("Get Summary")
        if s_sub:
            payload = {"patient_id": s_patient_id}
            resp = call_walker("GetSessionSummaryWalker", payload)
            st.json(resp)

st.markdown("---")
st.caption("If HTTP bridge is available at http://localhost:8000, the app will use it; otherwise it runs the jac CLI as a fallback. Ensure jac is on PATH and mindharmony.jac is the correct module path.")
