import streamlit as st
import requests
from datetime import datetime, timezone
from typing import Any, Dict, Optional

API_BASE_URL = "http://localhost:8000"

st.set_page_config(
    page_title="BetterHealthAi",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------------------------------------------------------
# ✅ STYLES (FULL)
# -------------------------------------------------------------------
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
   ✅ SIDEBAR LOOK + MENU LABEL VISIBLE
   ========================= */
[data-testid="stSidebar"]{
    background: linear-gradient(180deg,#f0f8ff 0%,#e6f2ff 100%);
    color: #07263b;
    padding: 1rem;
    border-right: 1px solid rgba(7,38,59,0.06);
    box-shadow: 0 2px 8px rgba(3,27,45,0.03);
}

/* reduce extra padding inside sidebar content */
[data-testid="stSidebar"] .block-container{
    padding: 0.25rem 0.5rem 0.5rem 0.5rem !important;
}

/* expander header stays subtle (theme-safe) */
section[data-testid="stSidebar"] details > summary{
    background: rgba(7,38,59,0.06) !important;
    padding: 8px 10px !important;
    border-radius: 10px !important;
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

/* =========================
   ✅ COMPACT UNIFORM BUTTONS
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
   ✅ LANDING ANIMATION + CENTERED HERO
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

# -------------------------------------------------------------------
# ✅ Jac HTTP Client
# -------------------------------------------------------------------
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


# -------------------------------------------------------------------
# ✅ Mood emoji mapping
# -------------------------------------------------------------------
def mood_feedback(score: int):
    if score >= 8:
        return "😄", "Feeling good", "#16a34a"
    if score >= 5:
        return "🙂", "Okay / managing", "#f59e0b"
    if score >= 3:
        return "😕", "Not great", "#f97316"
    return "😢", "Struggling", "#dc2626"


# -------------------------------------------------------------------
# ✅ Friendly UI building blocks
# -------------------------------------------------------------------
def card(title: str, body_html: str, tone: str = "info"):
    border = {"info": "#3b82f6", "success": "#10b981", "warn": "#f59e0b", "error": "#ef4444"}.get(tone, "#3b82f6")
    st.markdown(
        f"""
<div style="
    background:#ffffff;
    border:1px solid #e5e7eb;
    border-left:6px solid {border};
    border-radius:14px;
    padding:14px;
    box-shadow:0 2px 10px rgba(15,23,36,0.06);
    margin-top:10px;
">
  <div style="font-size:16px;font-weight:700;color:#111827;margin-bottom:8px;">
    {title}
  </div>
  <div style="color:#111827;font-size:14px;line-height:1.65;">
    {body_html}
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def long_text(text: str):
    safe = (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
    st.markdown(
        f"""
<div style="
    background:#ffffff;
    border:1px solid #e5e7eb;
    border-radius:14px;
    padding:14px;
    margin-top:10px;
    color:#111827;
    line-height:1.7;
">{safe}</div>
""",
        unsafe_allow_html=True,
    )


def show_error(resp: Dict[str, Any]):
    msg = resp.get("error", "Something went wrong.")
    card("Something went wrong", f"<div>{msg}</div>", tone="error")


# -------------------------------------------------------------------
# ✅ App header
# -------------------------------------------------------------------
st.title("BetterHealthAi")
st.markdown(
    "<p style='font-size:14px;margin-top:-6px;color:gray'>Mental Health Assessment Platform.</p>",
    unsafe_allow_html=True,
)

# -------------------------------------------------------------------
# ✅ Sidebar menu (simple dropdown / collapsible)
# -------------------------------------------------------------------
menu_options = [
    "Home",
    "Register Patient",
    "Start Assessment",
    "Submit Assessment Answer",
    "Submit Journal Entry",
    "Generate Recommendations",
    "Session Summary",
    "Patient Visit Stats",
]

if "active_action" not in st.session_state:
    st.session_state["active_action"] = "Home"

st.sidebar.markdown(
    "<h3 style='margin:0;padding:0'>BetterHealthAi</h3>"
    "<p style='font-size:12px;margin-top:2px;color:gray'>Mental Health Assessment Platform.</p>",
    unsafe_allow_html=True,
)

with st.sidebar.expander("Menu", expanded=True):
    for opt in menu_options:
        if st.button(opt, key=f"btn_{opt}"):
            st.session_state["active_action"] = opt

    if st.button("Clear selection", key="btn_clear"):
        st.session_state["active_action"] = "Home"

choice = st.session_state["active_action"]

# -------------------------------------------------------------------
# ✅ Landing page (NO forms here)
# -------------------------------------------------------------------
if choice == "Home":
    st.balloons()
    st.subheader("Welcome")

    st.write(
        "This is a calm and supportive space where someone can check in, share how they feel, "
        "and receive helpful guidance. It is designed for students, demos, and mental-health awareness."
    )

    st.write(
        "To get started, click **Register Patient** from the menu. After registering, you can start an assessment, "
        "submit answers, write a journal entry, and generate recommendations."
    )

    st.write("Small steps matter. Even one short sentence can be enough to begin.")


# -------------------------------------------------------------------
# ✅ Pages
# -------------------------------------------------------------------
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
            "assessment_context": {"assessment_type": assessment_type, "number_of_questions": int(num_questions)},
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
        else:
            rep = first_report(resp) or {}
            if rep.get("already_registered_count", 0) > 0:
                already = rep.get("already_registered", [])
                card("Already registered", f"<div>This patient ID already exists: <b>{', '.join(already)}</b></div>", tone="warn")
            else:
                card("Registered", "<div>Patient registration completed successfully.</div>", tone="success")

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
            "focus_areas": [s.strip() for s in focus_areas.split(",") if s.strip()],
        }

        resp = call_walker("StartAssessmentWalker", payload)
        if "error" in resp:
            show_error(resp)
        else:
            rep = first_report(resp) or {}
            card("🟢 Assessment started", "<div>You're good to go. You can now submit answers and journal entries.</div>", tone="success")
            fa = rep.get("focus_areas", [])
            if isinstance(fa, list) and fa:
                card("Focus Areas", "<div>" + "<br>".join([f"• {x}" for x in fa]) + "</div>", tone="info")

elif choice == "Submit Assessment Answer":
    st.header("Submit Assessment Answer")

    with st.form("answer_form"):
        ans_patient_id = st.text_input("Patient ID", value="patient_001", key="ans_pid")
        question = st.text_area("Question", value="How have you been feeling lately?", key="q", height=90)
        answer = st.text_area("Answer", value="", key="a", height=120)
        ans_sub = st.form_submit_button("Submit Answer")

    if ans_sub:
        payload = {"patient_id": ans_patient_id, "question": question, "answer": answer}
        resp = call_walker("SubmitAssessmentAnswerWalker", payload)

        if "error" in resp:
            show_error(resp)
        else:
            rep = first_report(resp) or {}
            card("💬 Saved", "<div>Your answer has been recorded. Here’s feedback based on what you shared:</div>", tone="success")
            analysis = rep.get("analysis")
            if isinstance(analysis, str) and analysis.strip():
                long_text(analysis)

elif choice == "Submit Journal Entry":
    st.header("Submit Journal Entry")

    with st.form("journal_form"):
        j_patient_id = st.text_input("Patient ID", value="patient_001", key="j_pid")
        journal_content = st.text_area("Journal content", value="Today was hard...", key="jc", height=140)
        mood_score = st.slider("Mood score (0 = worst, 10 = best)", 0, 10, 5)

        emoji, label, color = mood_feedback(int(mood_score))

        st.markdown(
            f"""
<div style="
    background:#ffffff;
    border:1px solid #e5e7eb;
    border-left:6px solid {color};
    border-radius:14px;
    padding:12px;
    margin-top:8px;
    margin-bottom:10px;
    font-size:16px;
    font-weight:700;
    color:#111827;
">
  {emoji} Mood check: <span style="color:{color}">{label}</span>
</div>
""",
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
<div style="
    height:12px;
    width:100%;
    background:#e5e7eb;
    border-radius:999px;
    overflow:hidden;
    margin-bottom:14px;
">
  <div style="
      height:100%;
      width:{int(mood_score) * 10}%;
      background:{color};
      border-radius:999px;
  "></div>
</div>
""",
            unsafe_allow_html=True,
        )

        created_at = st.text_input("Created at (ISO)", value=datetime.now(timezone.utc).isoformat(), key="ja")
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
        else:
            rep = first_report(resp) or {}
            card("Journal saved", "<div>Thanks for sharing. Here are some supportive suggestions:</div>", tone="success")
            suggestions = rep.get("suggestions")
            if isinstance(suggestions, str) and suggestions.strip():
                long_text(suggestions)

elif choice == "Generate Recommendations":
    st.header("Generate Recommendations")

    with st.form("gen_form"):
        g_patient_id = st.text_input("Patient ID", value="patient_001", key="g_pid")
        g_created_at = st.text_input("Created at (ISO)", value=datetime.now(timezone.utc).isoformat(), key="g_time")
        g_sub = st.form_submit_button("Generate")

    if g_sub:
        payload = {"patient_id": g_patient_id, "created_at": g_created_at}
        resp = call_walker("GenerateRecommendationsWalker", payload)

        if "error" in resp:
            show_error(resp)
        else:
            rep = first_report(resp) or {}
            card("Recommendations", "<div>Here are your personalized recommendations:</div>", tone="info")
            rec = rep.get("recommendations")
            if isinstance(rec, str) and rec.strip():
                long_text(rec)

elif choice == "Session Summary":
    st.header("Session Summary")

    with st.form("summary_form"):
        s_patient_id = st.text_input("Patient ID", value="patient_001", key="s_pid")
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

        summary_text = f"""
This session summary is for **{name}**.
The assessment session is currently active.

So far, the patient has shared **{answers} assessment response{'s' if answers != 1 else ''}**
and written **{journals} journal entr{'ies' if journals != 1 else 'y'}**.

Based on the information shared,
**{recs} set{'s' if recs != 1 else ''} of personalized recommendations**
have been generated to help support the patient’s mental and emotional well-being.
"""
        st.markdown(summary_text.strip())

        if isinstance(focus, list) and focus:
            focus_text = ", ".join(focus)
            st.markdown(f"The main areas being worked on during this session include: **{focus_text}.**")

        if answers == 0 and journals == 0:
            st.markdown(
                " *Tip:* You can begin by answering one assessment question or writing a short journal entry "
                "to receive more personalized support."
            )

elif choice == "Patient Visit Stats":
    st.header("Patient Visit Stats")

    resp = call_walker("PatientVisitStatsWalker", {})
    if "error" in resp:
        show_error(resp)
    else:
        rep = first_report(resp) or {}
        reg = int(rep.get("registered_count", 0) or 0)
        visited = int(rep.get("visited_count", 0) or 0)
        started = int(rep.get("started_count", 0) or 0)
        assessed = int(rep.get("patients_assessed_count", 0) or 0)

        card("Overview", "<div>Here is what’s happening in the platform right now.</div>", tone="info")

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
            card("Gender counts", "<div>" + "<br>".join([f"• {k}: {v}" for k, v in genders.items()]) + "</div>", tone="success")

else:
    card("Welcome", "<div>Select an action from the left menu to begin.</div>", tone="info")

st.markdown("---")
st.markdown(
    "<p style='font-size:12px;color:gray;text-align:center;'>"
    "BetterHealthAi — Mental Health Assessment Platform 💙"
    "</p>",
    unsafe_allow_html=True,
)
