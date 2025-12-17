import streamlit as st
import requests
import subprocess
import json
import pandas as pd
from datetime import datetime, timezone
from typing import Any, Dict

API_BASE_URL = "http://localhost:8000"  # optional Jac HTTP bridge; fallback to CLI if unavailable
JAC_MODULE_PATH = "/home/hmungania/code/mindharmony2.jac"  # updated to match mindharmony2.jac

st.set_page_config(page_title="MindHarmony UI", layout="wide", initial_sidebar_state="expanded")

# Add app-wide styling: fonts, background, sidebar, buttons, and form fields
st.markdown(
    """
    <style>
    /* Page background and base font */
    body, .stApp {
        background: linear-gradient(135deg,#f6fbff 0%,#eef7f4 100%);
        color: #0f1724;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }
    /* Container padding */
    .block-container {
        padding-top: 1.25rem;
        padding-bottom: 1.25rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }
    /* Sidebar / menu styling (changed colors) */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg,#f0f8ff 0%,#e6f2ff 100%);
        color: #07263b;
        padding: 1rem 1rem;
        border-right: 1px solid rgba(7,38,59,0.06);
        box-shadow: 0 2px 8px rgba(3,27,45,0.03);
    }
    /* Sidebar menu button appearance */
    [data-testid="stSidebar"] .stButton>button {
        background: linear-gradient(180deg,#2563eb,#1d4ed8) !important; /* blue gradient */
        color: #ffffff !important;
        border: none;
        padding: 8px 12px;
        border-radius: 8px;
        width: 100%;
        text-align: left;
        box-shadow: none;
        margin-bottom: 6px;
    }
    [data-testid="stSidebar"] .stButton>button:hover {
        filter: brightness(0.95);
    }
    /* Make primary action buttons in main area use an accent that complements the sidebar */
    .stButton>button {
        background-color: #0b7360 !important;
        color: #fff !important;
        border: none;
        padding: 8px 12px;
        border-radius: 8px;
    }
    .stButton>button:hover { filter: brightness(0.95); }

    /* Inputs / textareas */
    input, textarea, select, .public-DraftStyleDefault-block {
        background: #ffffff;
        border: 1px solid #e6eef3;
        border-radius: 6px;
        padding: 8px;
    }
    /* Headings */
    h1, h2, h3 { color: #0b3b2e; font-weight:600; }
    /* Cards / result area */
    .stMarkdown, .stExpander, .stContainer {
        background: transparent;
    }
    /* Small helper text */
    .css-1v3fvcr { color: #6b7280; } /* best-effort minimal helper color */
    </style>
    """,
    unsafe_allow_html=True,
)

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

def extract_byllm_content(resp):
    try:
        # direct string
        if isinstance(resp, str):
            s = resp.strip()
            return s if s else None

        # common top-level keys
        if isinstance(resp, dict):
            for k in ("analysis", "suggestions", "recommendations", "content", "message", "result", "text"):
                v = resp.get(k)
                if isinstance(v, str) and v.strip():
                    return v.strip()

            # try CLI stdout if present
            if "stdout" in resp and isinstance(resp["stdout"], str) and resp["stdout"].strip():
                try:
                    parsed = json.loads(resp["stdout"])
                    return extract_byllm_content(parsed)
                except Exception:
                    s = resp["stdout"].strip()
                    if s:
                        return s

            # recursive search for first non-empty string in nested structures
            def recurse(obj):
                if isinstance(obj, str):
                    s = obj.strip()
                    return s if s else None
                if isinstance(obj, dict):
                    for _, v in obj.items():
                        r = recurse(v)
                        if r:
                            return r
                if isinstance(obj, list):
                    for item in obj:
                        r = recurse(item)
                        if r:
                            return r
                return None

            return recurse(resp)
    except Exception:
        pass
    return None

def find_key_recursive(obj, key):
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for v in obj.values():
            found = find_key_recursive(v, key)
            if found is not None:
                return found
    if isinstance(obj, list):
        for item in obj:
            found = find_key_recursive(item, key)
            if found is not None:
                return found
    return None

def display_response(walker_name: str, resp: Dict[str, Any]):
    # registration: concise success or explicit already-registered message
    if walker_name == "RegisterPatientWalker":
        if isinstance(resp, dict):
            if resp.get("already_registered_count", 0) > 0:
                st.error("ALREADY REGISTERED!!")
                already = resp.get("already_registered", [])
                if already:
                    st.write("Already registered IDs:", ", ".join(already))
                return
            if resp.get("status") == "registered":
                st.success(f"Patient registered successfully ({resp.get('new_registered_count', resp.get('patient_count', 1))} added).")
                return

    # explicit handling for GenerateRecommendationsWalker: search recursively for 'recommendations'
    if walker_name == "GenerateRecommendationsWalker":
        # try direct or nested key
        if isinstance(resp, dict):
            rec = find_key_recursive(resp, "recommendations")
            if isinstance(rec, str) and rec.strip():
                st.markdown(rec.strip())
                return
            # if recommendations is nested as dict/list with 'content'
            if isinstance(rec, dict):
                cont = find_key_recursive(rec, "content")
                if isinstance(cont, str) and cont.strip():
                    st.markdown(cont.strip())
                    return
        # CLI stdout wrapper case
        if isinstance(resp, dict) and "stdout" in resp and isinstance(resp["stdout"], str) and resp["stdout"].strip():
            try:
                parsed = json.loads(resp["stdout"])
                rec2 = find_key_recursive(parsed, "recommendations")
                if isinstance(rec2, str) and rec2.strip():
                    st.markdown(rec2.strip())
                    return
                if isinstance(rec2, dict):
                    cont2 = find_key_recursive(rec2, "content")
                    if isinstance(cont2, str) and cont2.strip():
                        st.markdown(cont2.strip())
                        return
            except Exception:
                pass

    # explicit errors
    if isinstance(resp, dict) and "error" in resp:
        err = resp.get("error")
        st.error(err if isinstance(err, str) else json.dumps(resp))
        return

    # prefer LLM/byllm content only
    content = extract_byllm_content(resp)
    if content:
        st.markdown(content)
        return

    # fallback to a minimal status/info if available
    if isinstance(resp, dict) and "status" in resp:
        st.info(str(resp.get("status")))
        return

    # last-resort: write small fallback instead of dumping full JSON
    try:
        st.write(resp if isinstance(resp, str) else json.dumps(resp))
    except Exception:
        st.write(str(resp))

st.title("BetterHealthAi")
st.markdown("<p style='font-size:14px;margin-top:-6px;color:gray'>Mental Health Assessment Platform.</p>", unsafe_allow_html=True)

# Sidebar menu to choose which form to display
menu_options = [
    "Register Patient",
    "Start Assessment",
    "Submit Assessment Answer",
    "Submit Journal Entry",
    "Generate Recommendations",
    "Session Summary",
    "Patient Visit Stats",
]

# Initialize session state for active action
if "active_action" not in st.session_state:
    st.session_state["active_action"] = None

st.sidebar.markdown(
    "<h3 style='margin:0;padding:0'>BetterHealthAi</h3>"
    "<p style='font-size:12px;margin-top:2px;color:gray'>Mental Health Assessment Platform.</p>",
    unsafe_allow_html=True,
)
for opt in menu_options:
    if st.sidebar.button(opt, key=f"btn_{opt}"):
        st.session_state["active_action"] = opt

# Allow clearing selection to hide forms
if st.sidebar.button("Clear selection", key="btn_clear"):
    st.session_state["active_action"] = None

choice = st.session_state["active_action"]

st.markdown("---")

if choice == "Register Patient":
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
            display_response("RegisterPatientWalker", resp)

elif choice == "Start Assessment":
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
            display_response("StartAssessmentWalker", resp)

elif choice == "Submit Assessment Answer":
    st.header("Submit Assessment Answer")
    with st.form("answer_form"):
        ans_patient_id = st.text_input("Patient ID", value="patient_001", key="ans_pid")
        question = st.text_area("Question", value="How have you been feeling lately?", key="q")
        answer = st.text_area("Answer", value="", key="a")
        ans_sub = st.form_submit_button("Submit Answer")
        if ans_sub:
            payload = {"patient_id": ans_patient_id, "question": question, "answer": answer}
            resp = call_walker("SubmitAssessmentAnswerWalker", payload)
            display_response("SubmitAssessmentAnswerWalker", resp)

elif choice == "Submit Journal Entry":
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

            # extract only by-LLM suggestion/summary text
            def extract_suggestion(obj):
                if isinstance(obj, dict):
                    for key in ("suggestions", "recommendations", "analysis", "content", "result", "text", "message"):
                        v = obj.get(key)
                        if isinstance(v, str) and v.strip():
                            return v.strip()
                        if isinstance(v, (dict, list)):
                            r = extract_suggestion(v)
                            if r:
                                return r
                    for v in obj.values():
                        r = extract_suggestion(v)
                        if r:
                            return r
                if isinstance(obj, list):
                    for item in obj:
                        r = extract_suggestion(item)
                        if r:
                            return r
                if isinstance(obj, str):
                    s = obj.strip()
                    return s if s else None
                return None

            suggestion = extract_suggestion(resp)

            # CLI stdout wrapper case
            if not suggestion and isinstance(resp, dict) and "stdout" in resp and isinstance(resp["stdout"], str) and resp["stdout"].strip():
                try:
                    parsed = json.loads(resp["stdout"])
                    suggestion = extract_suggestion(parsed)
                except Exception:
                    suggestion = None

            # final fallback to generic extraction
            if not suggestion:
                suggestion = extract_byllm_content(resp)

            if suggestion:
                st.markdown(suggestion)
            else:
                st.warning("No by-LLM suggestion found.")

elif choice == "Generate Recommendations":
    st.header("Generate Recommendations")
    with st.form("gen_form"):
        g_patient_id = st.text_input("Patient ID", value="patient_001", key="g_pid")
        g_created_at = st.text_input("Created at (ISO)", value=datetime.now(timezone.utc).isoformat(), key="g_time")
        g_sub = st.form_submit_button("Generate")
        if g_sub:
            payload = {"patient_id": g_patient_id, "created_at": g_created_at}
            resp = call_walker("GenerateRecommendationsWalker", payload)

            # prefer explicit 'recommendations' field (search recursively)
            def extract_recommendations(obj):
                if isinstance(obj, dict):
                    if "recommendations" in obj:
                        return obj["recommendations"]
                    for v in obj.values():
                        r = extract_recommendations(v)
                        if r is not None:
                            return r
                if isinstance(obj, list):
                    for item in obj:
                        r = extract_recommendations(item)
                        if r is not None:
                            return r
                return None

            r = extract_recommendations(resp)

            # CLI stdout wrapper case
            if r is None and isinstance(resp, dict) and "stdout" in resp and isinstance(resp["stdout"], str) and resp["stdout"].strip():
                try:
                    parsed = json.loads(resp["stdout"])
                    r = extract_recommendations(parsed)
                except Exception:
                    r = None

            # normalize into a plain string
            rec = None
            if isinstance(r, list):
                rec = "\n\n".join([str(i).strip() for i in r if str(i).strip()])
            elif isinstance(r, dict):
                cont = find_key_recursive(r, "content")
                if isinstance(cont, str) and cont.strip():
                    rec = cont.strip()
                else:
                    rec = extract_byllm_content(r)
            elif isinstance(r, str):
                rec = r.strip()

            # final attempt: generic LLM content extraction (text only)
            if not rec:
                rec = extract_byllm_content(resp)

            if rec:
                st.markdown(rec)
            else:
                st.warning("No by-LLM recommendations found.")

elif choice == "Session Summary":
    st.header("Session Summary")
    with st.form("summary_form"):
        s_patient_id = st.text_input("Patient ID", value="patient_001", key="s_pid")
        s_sub = st.form_submit_button("Get Summary")
        if s_sub:
            payload = {"patient_id": s_patient_id}
            resp = call_walker("GetSessionSummaryWalker", payload)

            # Display patient id and conditions (focus_areas) if available
            if isinstance(resp, dict):
                pid = resp.get("patient_id", s_patient_id)
                st.markdown(f"**Patient ID:** {pid}")

                focus = resp.get("focus_areas")
                if isinstance(focus, list):
                    fa_text = ", ".join([str(x) for x in focus]) if focus else "None listed"
                    st.markdown(f"**Conditions / Focus areas:** {fa_text}")
                elif focus:
                    st.markdown(f"**Conditions / Focus areas:** {str(focus)}")
                # also show patient name if present
                name = resp.get("patient_name")
                if name:
                    st.markdown(f"**Patient name:** {name}")

            # prefer explicit 'summary' or 'suggestions', then generic by-LLM content
            def extract_summary(obj):
                if isinstance(obj, dict):
                    for key in ("summary", "suggestions", "recommendations", "content", "analysis", "result", "text"):
                        v = obj.get(key)
                        if isinstance(v, str) and v.strip():
                            return v.strip()
                        if isinstance(v, dict) or isinstance(v, list):
                            r = extract_summary(v)
                            if r:
                                return r
                    for v in obj.values():
                        r = extract_summary(v)
                        if r:
                            return r
                if isinstance(obj, list):
                    for item in obj:
                        r = extract_summary(item)
                        if r:
                            return r
                if isinstance(obj, str):
                    s = obj.strip()
                    return s if s else None
                return None

            summary_text = extract_summary(resp)

            # CLI stdout wrapper case
            if not summary_text and isinstance(resp, dict) and "stdout" in resp and isinstance(resp["stdout"], str) and resp["stdout"].strip():
                try:
                    parsed = json.loads(resp["stdout"])
                    summary_text = extract_summary(parsed)
                except Exception:
                    summary_text = None

            # final generic fallback
            if not summary_text:
                summary_text = extract_byllm_content(resp)

            if summary_text:
                st.markdown("**Summary / Suggestions:**")
                st.markdown(summary_text)
            else:
                st.warning("No by-LLM summary/suggestion found.")

elif choice == "Patient Visit Stats":
    st.header("Patient Visit Stats")

    # helper: try many possible locations/structures for the assessed count
    def extract_assessed_count(resp_obj):
        def try_parse_stdout(obj):
            if isinstance(obj, dict) and "stdout" in obj and isinstance(obj["stdout"], str) and obj["stdout"].strip():
                try:
                    return json.loads(obj["stdout"])
                except Exception:
                    return None
            return None

        def normalize(obj):
            # if string that contains JSON, try parse
            if isinstance(obj, str):
                try:
                    return json.loads(obj)
                except Exception:
                    return obj
            return obj

        obj = normalize(resp_obj)

        # if wrapped CLI stdout, precedence to parsed stdout
        if isinstance(obj, dict):
            parsed = try_parse_stdout(obj)
            if parsed is not None:
                obj = parsed

        # look for explicit numeric/count keys or lists to derive count
        if isinstance(obj, dict):
            # direct numeric keys
            for key in ("patients_assessed_count", "assessed_count", "visited_count", "started_count", "registered_count"):
                val = obj.get(key)
                if isinstance(val, int):
                    return val
                if isinstance(val, str) and val.isdigit():
                    return int(val)
            # list keys that imply count
            for list_key in ("patients_assessed", "patients_assessed_list", "visited_list", "registered_list"):
                val = obj.get(list_key)
                if isinstance(val, list):
                    return len(val)
            # nested search (first match)
            for k, v in obj.items():
                if isinstance(v, (dict, list)):
                    nested = extract_assessed_count(v)
                    if nested is not None:
                        return nested
        if isinstance(obj, list):
            # if top-level is list, use its length
            return len(obj) if obj else None

        return None

    # call walker and display
    payload = {}
    resp = call_walker("PatientVisitStatsWalker", payload)

    assessed_count = extract_assessed_count(resp)
    if assessed_count is not None:
        st.metric("Patients assessed", assessed_count)
    else:
        st.info("No assessment count available.")

st.markdown("---")
st.caption("If HTTP bridge is available at http://localhost:8000, the app will use it; otherwise it runs the jac CLI as a fallback. Ensure jac is on PATH and mindharmony.jac is the correct module path.")
