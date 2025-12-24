import streamlit as st
import requests
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# ============================================================
# Config
# ============================================================
API_BASE_URL = "http://localhost:8000"

st.set_page_config(
    page_title="BetterHealthAi",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# ✅ STYLES (YOUR THEME — unchanged colors)
# ============================================================
st.markdown(
    """
<style>
/* =========================
   ✅ GLOBAL APP LOOK
   ========================= */
body, .stApp {
    background: linear-gradient(135deg,#f6fbff 0%,#eef7f4 100%);
    color: #0f1724;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}
.block-container {
    padding-top: 1.25rem;
    padding-bottom: 1.25rem;
    padding-left: 2rem;
    padding-right: 2rem;
}

/* =========================
   ✅ SIDEBAR LOOK (keeps blue/white)
   ========================= */
[data-testid="stSidebar"]{
    background: linear-gradient(180deg,#f0f8ff 0%,#e6f2ff 100%) !important;
    color: #07263b !important;
    padding: 1rem !important;
    border-right: 1px solid rgba(7,38,59,0.06) !important;
    box-shadow: 0 2px 8px rgba(3,27,45,0.03) !important;
}

/* reduce extra padding inside sidebar content */
[data-testid="stSidebar"] .block-container{
    padding: 0.25rem 0.5rem 0.5rem 0.5rem !important;
}

/* =========================
   ✅ EXPANDER (fix dark/black issue)
   ========================= */
section[data-testid="stSidebar"] details {
    background: transparent !important;
    border: 0 !important;
}

section[data-testid="stSidebar"] details > summary{
    background: rgba(7,38,59,0.06) !important;
    padding: 8px 10px !important;
    border-radius: 10px !important;
    border: 1px solid rgba(7,38,59,0.10) !important;
}

/* expander title text + arrow visible */
section[data-testid="stSidebar"] details > summary p,
section[data-testid="stSidebar"] details > summary div,
section[data-testid="stSidebar"] details > summary span{
    color: #07263b !important;
    font-weight: 700 !important;
}
section[data-testid="stSidebar"] details > summary svg path{
    fill: #07263b !important;
}
section[data-testid="stSidebar"] details > summary:hover{
    background: rgba(7,38,59,0.10) !important;
}

/* expander content background (prevents black block) */
section[data-testid="stSidebar"] details > div {
    background: transparent !important;
    border: 0 !important;
    padding-top: 8px !important;
}

/* =========================
   ✅ COMPACT UNIFORM BUTTONS (same blue)
   ========================= */
:root{
  --btn-bg: #2563eb;
  --btn-bg-hover:#1d4ed8;
  --btn-bg-active:#1e40af;

  --btn-radius: 10px;
  --btn-pad-y: 6px;
  --btn-pad-x: 12px;
  --btn-font: 600;

  --btn-min-height: 36px;
  --btn-shadow: 0 2px 6px rgba(37,99,235,.15);
  --btn-shadow-hover: 0 4px 10px rgba(37,99,235,.20);
}

/* IMPORTANT: sidebar buttons + app buttons */
div.stButton > button,
div.stFormSubmitButton > button,
div.stDownloadButton > button,
[data-testid="stSidebar"] .stButton > button {
    width: 100% !important;
    min-height: var(--btn-min-height) !important;

    display: flex !important;
    align-items: center !important;
    justify-content: flex-start !important;

    background: var(--btn-bg) !important;
    color: #ffffff !important;

    border: none !important;
    border-radius: var(--btn-radius) !important;

    padding: var(--btn-pad-y) var(--btn-pad-x) !important;
    font-size: 14px !important;
    font-weight: var(--btn-font) !important;

    box-shadow: var(--btn-shadow) !important;
    margin-bottom: 6px !important;
    text-align: left !important;

    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;

    transition: all 0.12s ease !important;
}

div.stButton > button:hover,
div.stFormSubmitButton > button:hover,
div.stDownloadButton > button:hover,
[data-testid="stSidebar"] .stButton > button:hover {
    background: var(--btn-bg-hover) !important;
    box-shadow: var(--btn-shadow-hover) !important;
}

div.stButton > button:active,
div.stFormSubmitButton > button:active,
div.stDownloadButton > button:active,
[data-testid="stSidebar"] .stButton > button:active {
    background: var(--btn-bg-active) !important;
    transform: translateY(1px) !important;
}

div.stButton > button:focus,
div.stFormSubmitButton > button:focus,
div.stDownloadButton > button:focus,
[data-testid="stSidebar"] .stButton > button:focus {
    outline: 2px solid rgba(37,99,235,0.35) !important;
    outline-offset: 2px !important;
}

/* =========================
   ✅ INPUTS READABLE
   ========================= */
textarea,
input,
select,
.stTextInput input,
.stTextArea textarea {
    background-color: #ffffff !important;
    color: #000000 !important;
    border: 1px solid #e5e7eb !important;
    border-radius: 10px !important;
}
textarea::placeholder,
input::placeholder {
    color: #6b7280 !important;
    opacity: 1 !important;
}
label,
.stTextInput label,
.stTextArea label {
    color: #000000 !important;
    font-weight: 500;
}

/* =========================
   ✅ HEADERS
   ========================= */
h1, h2, h3 {
    color: #0b3b2e;
    font-weight: 600;
}

/* =========================
   ✅ ALERTS
   ========================= */
[data-testid="stAlert"] {
    background-color: #ffffff !important;
    color: #000000 !important;
    border: 1px solid #e5e7eb !important;
    border-radius: 12px !important;
}
[data-testid="stAlert"] * {
    color: #000000 !important;
}

/* =========================
   ✅ METRICS
   ========================= */
[data-testid="stMetric"] {
    background-color: #ffffff !important;
    padding: 12px !important;
    border-radius: 12px !important;
    border: 1px solid #e5e7eb !important;
}
[data-testid="stMetricValue"] { color: #000000 !important; }
[data-testid="stMetricLabel"] { color: #111827 !important; }

/* =========================
   ✅ CODE / PRE FORMATTING
   ========================= */
pre, code {
    background-color: #ffffff !important;
    color: #000000 !important;
    border-radius: 10px !important;
    border: 1px solid #e5e7eb !important;
}

/* =========================
   ✅ LANDING ANIMATION
   ========================= */
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(16px); }
    to   { opacity: 1; transform: translateY(0); }
}
.landing-wrap{
    animation: fadeUp 0.8s ease-out;
    max-width: 760px;
    margin: 54px auto 0 auto;
    text-align: center;
}
.landing-title{
    font-size: 42px;
    font-weight: 800;
    color: #0b3b2e;
    margin: 6px 0 2px 0;
}
.landing-subtitle{
    font-size: 15px;
    color: #6b7280;
    margin: 0 0 22px 0;
}
.landing-badge{
    font-size: 34px;
    width: 74px;
    height: 74px;
    border-radius: 999px;
    background: #ffffff;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 14px auto;
    box-shadow: 0 6px 18px rgba(15,23,36,0.08);
    border: 1px solid rgba(229,231,235,0.9);
}
.landing-card{
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 16px;
    padding: 16px 18px;
    text-align: left;
    box-shadow: 0 2px 10px rgba(15,23,36,0.06);
    margin-top: 12px;
}
.landing-text{
    font-size: 15px;
    line-height: 1.75;
    color: #111827;
    margin: 0;
}
.landing-tip{
    font-size: 14px;
    color: #374151;
    font-style: italic;
    margin-top: 14px;
}
</style>
""",
    unsafe_allow_html=True,
)

# ============================================================
# ✅ Jac HTTP Client
# ============================================================
def safe_json(resp: requests.Response) -> Any:
    try:
        return resp.json()
    except Exception:
        return {"error": "non_json_response", "details": resp.text}


def call_walker(walker: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{API_BASE_URL}/walker/{walker}"
    try:
        r = requests.post(url, json=payload, timeout=30)
        data = safe_json(r)

        if r.status_code == 404:
            return {"error": f"Walker not found: {walker}"}
        if not r.ok:
            return {"error": f"HTTP {r.status_code}", "details": data}

        return data if isinstance(data, dict) else {"reports": data}

    except requests.exceptions.ConnectionError:
        return {"error": f"Cannot reach server at {API_BASE_URL}. Please start backend (python run.py)."}
    except requests.exceptions.Timeout:
        return {"error": f"Server timed out calling {walker}."}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


def first_report(resp: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    reports = resp.get("reports")
    if isinstance(reports, list) and reports and isinstance(reports[0], dict):
        return reports[0]
    return None


# ============================================================
# ✅ Mood emoji mapping
# ============================================================
def mood_feedback(score: int):
    if score >= 8:
        return "😄", "Feeling good", "#16a34a"
    if score >= 5:
        return "🙂", "Okay / managing", "#f59e0b"
    if score >= 3:
        return "😕", "Not great", "#f97316"
    return "😢", "Struggling", "#dc2626"


# ============================================================
# ✅ Small UI helpers
# ============================================================
def card(title: str, body: str, tone: str = "info"):
    if tone == "success":
        st.success(body)
    elif tone == "warn":
        st.warning(body)
    elif tone == "error":
        st.error(body)
    else:
        st.info(body)


def show_error(resp: Dict[str, Any]):
    msg = resp.get("error", "Something went wrong.")
    details = resp.get("details")
    st.error(msg)
    if details:
        st.caption(str(details))


# ============================================================
# ✅ App header
# ============================================================
st.title("BetterHealthAi")
st.caption("Mental Health Assessment Platform.")

# ---------- Sidebar Navigation (collapsible that actually hides items) ----------
if "active_action" not in st.session_state:
    st.session_state["active_action"] = "Home"

if "menu_open" not in st.session_state:
    st.session_state["menu_open"] = True

st.sidebar.markdown(
    "<h3 style='margin:0;padding:0'>BetterHealthAi</h3>"
    "<p style='font-size:12px;margin-top:2px;color:gray'>Mental Health Assessment Platform.</p>",
    unsafe_allow_html=True,
)

# Home (always visible)
if st.sidebar.button("Home", key="nav_home", use_container_width=True):
    st.session_state["active_action"] = "Home"
    st.session_state["menu_open"] = False
    st.rerun()

# Toggle button (this is the REAL collapse control)
toggle_label = "Menu ▼" if st.session_state["menu_open"] else "Menu ▶"
if st.sidebar.button(toggle_label, key="nav_menu_toggle", use_container_width=True):
    st.session_state["menu_open"] = not st.session_state["menu_open"]
    st.rerun()

# Only render menu items when open (this makes it truly collapse)
if st.session_state["menu_open"]:
    for opt in [
        "Register Patient",
        "Start Assessment",
        "Submit Assessment Answer",
        "Submit Journal Entry",
        "Generate Recommendations",
        "Session Summary",
        "Patient Visit Stats",
    ]:
        if st.sidebar.button(opt, key=f"nav_{opt}", use_container_width=True):
            st.session_state["active_action"] = opt
            st.session_state["menu_open"] = False
            st.rerun()

    if st.sidebar.button("Reset", key="nav_reset", use_container_width=True):
        st.session_state["active_action"] = "Home"
        st.session_state["menu_open"] = False
        st.rerun()

choice = st.session_state["active_action"]


# ---------------------------
# Home / Landing
# ---------------------------
if choice == "Home":
    st.balloons()

    st.markdown(
        """
<div class="landing-wrap">
  <div class="landing-badge">💙</div>
  <div class="landing-title">Welcome to BetterHealthAi</div>
  <div class="landing-subtitle">A calm space to check in, reflect, and get supportive guidance.</div>

  <div class="landing-card">
    <p class="landing-text">
      BetterAI is a Jac-based prototype for mental-health tooling.
      It helps people share how they feel through simple questions and journaling.
      It can also generate supportive suggestions and structured summaries for follow-ups.
    </p>
  </div>

  <div class="landing-card">
    <p class="landing-text">
      If you are a student or young person, you can use it as a friendly check-in.
      If you are a medical professional, you can use it to capture a clear session summary.
    </p>
    <p class="landing-tip">Start small. One honest sentence is enough to begin.</p>
  </div>

  <div class="landing-card">
    <p class="landing-text">
      To begin, open the menu on the left and click <b>Register Patient</b>.
      After that, you can start an assessment, submit answers, write a journal entry,
      and generate recommendations.
    </p>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

# ---------------------------
# Register Patient
# ---------------------------
elif choice == "Register Patient":
    st.header("Register Patient")

    with st.form("register_form"):
        patient_id = st.text_input("Patient ID", value="patient_001")
        name = st.text_input("Name", value="John Doe")
        email = st.text_input("Email", value="john@example.com")
        age = st.number_input("Age", min_value=0, max_value=120, value=28)
        assessment_type = st.selectbox("Assessment Type", ["initial", "follow-up", "crisis"])
        num_questions = st.number_input("Number of Questions", min_value=1, max_value=50, value=10)
        medical_history = st.text_area("Medical history (optional)", value="", height=100)
        submitted = st.form_submit_button("Register")

    if submitted:
        payload = {
            "assessment_context": {
                "assessment_type": assessment_type,
                "number_of_questions": int(num_questions),
            },
            "patients": [
                {
                    "patient_id": patient_id,
                    "name": name,
                    "email": email,
                    "age": int(age),
                    "medical_history": medical_history,
                }
            ],
        }

        resp = call_walker("RegisterPatientWalker", payload)
        if "error" in resp:
            show_error(resp)
            st.stop()

        rep = first_report(resp) or {}
        if rep.get("already_registered_count", 0) > 0:
            st.warning("This patient ID is already registered.")
        else:
            st.success("Patient registration completed successfully.")

# ---------------------------
# Start Assessment
# ---------------------------
elif choice == "Start Assessment":
    st.header("Start Assessment")

    with st.form("start_form"):
        start_patient_id = st.text_input("Patient ID", value="patient_001")
        start_assessment_type = st.selectbox("Assessment Type", ["initial", "follow-up", "crisis"])
        focus_areas = st.text_input("Focus areas (comma separated)", value="anxiety, sleep")
        start_sub = st.form_submit_button("Start Assessment")

    if start_sub:
        payload = {
            "patient_id": start_patient_id,
            "assessment_type": start_assessment_type,
            "focus_areas": [s.strip() for s in focus_areas.split(",") if s.strip()],
        }

        resp = call_walker("StartAssessmentWalker", payload)
        if "error" in resp:
            show_error(resp)
            st.stop()

        st.success("Assessment started. You can now submit answers and journal entries.")

# ---------------------------
# Submit Assessment Answer
# ---------------------------
elif choice == "Submit Assessment Answer":
    st.header("Submit Assessment Answer")

    with st.form("answer_form"):
        ans_patient_id = st.text_input("Patient ID", value="patient_001")
        question = st.text_area("Question", value="How have you been feeling lately?", height=90)
        answer = st.text_area("Answer", value="", height=120)
        ans_sub = st.form_submit_button("Submit Answer")

    if ans_sub:
        payload = {"patient_id": ans_patient_id, "question": question, "answer": answer}
        resp = call_walker("SubmitAssessmentAnswerWalker", payload)

        if "error" in resp:
            show_error(resp)
            st.stop()

        rep = first_report(resp) or {}
        st.success("Your answer has been saved.")

        analysis = rep.get("analysis", "")
        if isinstance(analysis, str) and analysis.strip():
            st.subheader("Supportive feedback")
            st.write(analysis)

# ---------------------------
# Submit Journal Entry
# ---------------------------
elif choice == "Submit Journal Entry":
    st.header("Submit Journal Entry")

    with st.form("journal_form"):
        j_patient_id = st.text_input("Patient ID", value="patient_001")
        journal_content = st.text_area("Journal content", value="Today was hard...", height=140)

        mood_score = st.slider("Mood score (0 = worst, 10 = best)", 0, 10, 5)
        emoji, label, color = mood_feedback(int(mood_score))
        st.write(f"{emoji} {label}")

        created_at = st.text_input("Created at (ISO)", value=datetime.now(timezone.utc).isoformat())
        j_sub = st.form_submit_button("Submit Journal Entry")

    if j_sub:
        payload = {
            "patient_id": j_patient_id,
            "journal_content": journal_content,
            "created_at": created_at,
            "mood_score": int(mood_score),
        }
        resp = call_walker("SubmitJournalEntryWalker", payload)

        if "error" in resp:
            show_error(resp)
            st.stop()

        rep = first_report(resp) or {}
        st.success("Your journal entry has been saved.")

        suggestions = rep.get("suggestions", "")
        if isinstance(suggestions, str) and suggestions.strip():
            st.subheader("Supportive suggestions")
            st.write(suggestions)

# ---------------------------
# Generate Recommendations
# ---------------------------
elif choice == "Generate Recommendations":
    st.header("Generate Recommendations")

    with st.form("gen_form"):
        g_patient_id = st.text_input("Patient ID", value="patient_001")
        g_created_at = st.text_input("Created at (ISO)", value=datetime.now(timezone.utc).isoformat())
        g_sub = st.form_submit_button("Generate")

    if g_sub:
        payload = {"patient_id": g_patient_id, "created_at": g_created_at}
        resp = call_walker("GenerateRecommendationsWalker", payload)

        if "error" in resp:
            show_error(resp)
            st.stop()

        rep = first_report(resp) or {}
        rec = rep.get("recommendations", "")

        st.success("Recommendations generated.")
        if isinstance(rec, str) and rec.strip():
            st.write(rec)

# ---------------------------
# Session Summary
# ---------------------------
elif choice == "Session Summary":
    st.header("Session Summary")

    with st.form("summary_form"):
        s_patient_id = st.text_input("Patient ID", value="patient_001")
        s_sub = st.form_submit_button("Get Summary")

    if s_sub:
        resp = call_walker("GetSessionSummaryWalker", {"patient_id": s_patient_id})
        if "error" in resp:
            show_error(resp)
            st.stop()

        rep = first_report(resp) or {}

        name = rep.get("patient_name", "the patient")
        answers = int(rep.get("qa_count", 0) or 0)
        journals = int(rep.get("journal_entries", 0) or 0)
        recs = int(rep.get("recommendation_count", 0) or 0)
        focus = rep.get("focus_areas", [])

        st.write(f"This summary is for **{name}**.")
        st.write(f"So far there are **{answers}** assessment answers and **{journals}** journal entries.")
        st.write(f"**{recs}** recommendation sets have been generated.")

        if isinstance(focus, list) and focus:
            st.write("Focus areas: " + ", ".join([str(x) for x in focus]))

# ---------------------------
# Patient Visit Stats
# ---------------------------
elif choice == "Patient Visit Stats":
    st.header("Patient Visit Stats")

    resp = call_walker("PatientVisitStatsWalker", {})
    if "error" in resp:
        show_error(resp)
        st.stop()

    rep = first_report(resp) or {}
    reg = int(rep.get("registered_count", 0) or 0)
    visited = int(rep.get("visited_count", 0) or 0)
    started = int(rep.get("started_count", 0) or 0)
    assessed = int(rep.get("patients_assessed_count", 0) or 0)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Registered", reg)
    with c2:
        st.metric("Visited", visited)
    with c3:
        st.metric("Started", started)
    with c4:
        st.metric("Assessed", assessed)

    genders = rep.get("gender_counts", {})
    if isinstance(genders, dict) and genders:
        st.subheader("Gender counts")
        for k, v in genders.items():
            st.write(f"{k}: {v}")

# ============================================================
# Footer
# ============================================================
st.markdown("---")
st.markdown(
    "<p style='font-size:12px;color:gray;text-align:center;'>BetterHealthAi — Simple check-ins. Supportive guidance. Small steps count 💙</p>",
    unsafe_allow_html=True,
)