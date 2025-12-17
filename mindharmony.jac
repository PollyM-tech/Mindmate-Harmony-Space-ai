import litellm;
import from dotenv { load_dotenv }
import os;
import requests;
import base64;
import from byllm.lib { Model}


glob llm: Model = Model(model_name = "gemini/gemini-2.5-flash",api_key = os.getenv("GEMINI_API_KEY"));


node AssessmentContext {
    has assessment_type: str;           # "initial", "follow-up", "crisis"
    has number_of_questions: int;
    has focus_areas: list = [];          # ["anxiety", "depression", "sleep"]
    has clinical_guidelines: str = "";
    has therapist_notes: str = "";
}

obj Patient {
    has patient_id: str;
    has name: str;
    has email: str;
    has age: int = 0;
    has medical_history: str = "";
    has gender: str = "unknown";    # added gender field
}

obj Chat { has role: str; has content: str; }
obj AssessmentQA { has question: str; has answer: str; has confidence: float = 1.0; }

node TherapySession {
    has assessment_context: AssessmentContext;
    has patient: Patient;
    has assessment_qa: list[AssessmentQA] = [];
    has chat_history: list[Chat] = [];
    has is_active: bool = False;
    has assessment_started: bool = False;
    has journal_entries: list = [];
    has recommendations: list = [];
}

glob therapy_sessions: dict[str, TherapySession] = {};
glob assessment_stats: dict = {
    "registered_count": 0,
    "started_count": 0,
    "answers_total": 0,
    "patients_assessed": [],
    "registered_list": [],
    "focus_counts": {},
    "gender_counts": {}    # added gender_counts
};


def generate_assessment_question(
    assessment_type: str,
    focus_areas: str,
    patient_history: str,
    previous_answers: str,
    clinical_guidelines: str
) -> str by llm();

sem generate_assessment_question = "Generate thoughtful therapeutic assessment questions that help evaluate the patient's mental health, emotional state, and wellbeing based on the provided context and clinical guidelines.";
sem generate_assessment_question.assessment_type = "The type of assessment (initial, follow-up, or crisis evaluation).";
sem generate_assessment_question.focus_areas = "The specific mental health areas to focus on (e.g., anxiety, depression, sleep quality).";
sem generate_assessment_question.patient_history = "The patient's medical and mental health history.";
sem generate_assessment_question.previous_answers = "Previous assessment answers to build context and continuity.";
sem generate_assessment_question.clinical_guidelines = "Clinical best practices and assessment guidelines.";


def analyze_patient_response(
    patient_answer: str,
    question: str,
    medical_history: str
) -> str by llm();

sem analyze_patient_response = "Analyze the patient's response to assess emotional state, risk factors, and therapeutic needs.";
sem analyze_patient_response.patient_answer = "The patient's response to the assessment question.";
sem analyze_patient_response.question = "The original question asked.";
sem analyze_patient_response.medical_history = "The patient's relevant medical and psychiatric history.";


def generate_therapy_recommendations(
    assessment_summary: str,
    focus_areas: str,
    patient_preferences: str
) -> str by llm();

sem generate_therapy_recommendations = "Generate personalized therapeutic recommendations and coping strategies based on the assessment findings.";
sem generate_therapy_recommendations.assessment_summary = "Summary of the assessment findings and identified issues.";
sem generate_therapy_recommendations.focus_areas = "The main areas of concern identified during assessment.";
sem generate_therapy_recommendations.patient_preferences = "The patient's preferences for therapeutic approaches.";


walker RegisterPatientWalker {
    has assessment_context: AssessmentContext;
    has patients: list[dict];

    obj __specs__ { static has auth: bool = False; }

    can execute with `root entry {
        # track newly registered vs already registered
        new_count = 0;
        already_registered_ids = [];

        for patient_data in self.patients {
            pid = patient_data.get("patient_id", "");

            # if session already exists, mark as already registered and skip creating a new session
            if pid in therapy_sessions {
                already_registered_ids.append(pid);
                continue;
            }

            patient = Patient(
                patient_id=pid,
                name=patient_data.get("name", ""),
                email=patient_data.get("email", ""),
                age=patient_data.get("age", 0),
                medical_history=patient_data.get("medical_history", ""),
                gender=patient_data.get("gender", "unknown")    # capture gender on registration
            );

            session = TherapySession(
                assessment_context=self.assessment_context,
                patient=patient,
                is_active=True,
                assessment_started=False
            );

            therapy_sessions[patient.patient_id] = session;

            # Update assessment stats for registration
            if "registered_list" not in assessment_stats {
                assessment_stats["registered_list"] = [];
            }
            if patient.patient_id not in assessment_stats["registered_list"] {
                assessment_stats["registered_list"].append(patient.patient_id);
                assessment_stats["registered_count"] += 1;

                # update gender_counts
                g = patient.gender;
                if g == "" { g = "unknown"; }
                if g not in assessment_stats["gender_counts"] {
                    assessment_stats["gender_counts"][g] = 0;
                }
                assessment_stats["gender_counts"][g] += 1;
            }
            new_count += 1;
        }

        report {
            "status": "registered",
            "patient_count": len(self.patients),
            "new_registered_count": new_count,
            "already_registered_count": len(already_registered_ids),
            "already_registered": already_registered_ids,
            "assessment_type": self.assessment_context.assessment_type
        };
    }
}

walker StartAssessmentWalker {
    has patient_id: str;
    has assessment_type: str = "initial";
    has focus_areas: list = [];

    obj __specs__ { static has auth: bool = False; }

    can execute with `root entry {
        if self.patient_id not in therapy_sessions {
            report {"error": "Patient not found", "patient_id": self.patient_id};
            return;
        }

        session = therapy_sessions[self.patient_id];
        session.is_active = True;
        session.assessment_started = True;
        session.assessment_context.assessment_type = self.assessment_type;
        session.assessment_context.focus_areas = self.focus_areas;

        # Update stats for started assessments
        assessment_stats["started_count"] += 1;
        for fa in self.focus_areas {
            if fa not in assessment_stats["focus_counts"] {
                assessment_stats["focus_counts"][fa] = 0;
            }
            assessment_stats["focus_counts"][fa] += 1;
        }

        session.chat_history.append(Chat(
            role="therapist",
            content="Hello! I'm here to support your mental health journey. Let's begin our assessment to better understand how you're doing."
        ));

        report {
            "status": "assessment_started",
            "patient_id": self.patient_id,
            "assessment_type": self.assessment_type,
            "focus_areas": self.focus_areas
        };
    }
}

walker SubmitAssessmentAnswerWalker {
    has patient_id: str;
    has answer: str;
    has question: str = "";

    obj __specs__ { static has auth: bool = False; }

    can execute with `root entry {
        if self.patient_id not in therapy_sessions {
            report {"error": "Patient not found", "patient_id": self.patient_id};
            return;
        }

        session = therapy_sessions[self.patient_id];

        # Analyze the patient's response
        response_analysis = analyze_patient_response(
            self.answer,
            self.question,
            session.patient.medical_history
        );

        qa_pair = AssessmentQA(
            question=self.question,
            answer=self.answer,
            confidence=1.0
        );

        session.assessment_qa.append(qa_pair);

        # Update assessment statistics
        assessment_stats["answers_total"] += 1;
        if self.patient_id not in assessment_stats["patients_assessed"] {
            assessment_stats["patients_assessed"].append(self.patient_id);
        }

        session.chat_history.append(Chat(
            role="patient",
            content=self.answer
        ));

        session.chat_history.append(Chat(
            role="therapist",
            content=response_analysis
        ));

        report {
            "status": "answer_recorded",
            "patient_id": self.patient_id,
            "question_count": len(session.assessment_qa),
            "analysis": response_analysis
        };
    }
}

walker SubmitJournalEntryWalker {
    has patient_id: str;
    has journal_content: str;
    has created_at: str;
    has mood_score: int = 0;

    obj __specs__ { static has auth: bool = False; }

    can execute with `root entry {
        if self.patient_id not in therapy_sessions {
            report {"error": "Patient not found", "patient_id": self.patient_id};
            return;
        }

        session = therapy_sessions[self.patient_id];

        journal_entry = {
            "content": self.journal_content,
            "mood_score": self.mood_score,
            "created_at": self.created_at
        };

        session.journal_entries.append(journal_entry);

        # Generate supportive suggestions based on journal
        suggestions = generate_therapy_recommendations(
            self.journal_content,
            " ".join(session.assessment_context.focus_areas),
            ""
        );

        session.chat_history.append(Chat(
            role="therapist",
            content=suggestions
        ));

        report {
            "status": "journal_logged",
            "patient_id": self.patient_id,
            "mood_score": self.mood_score,
            "suggestions": suggestions,
            "created_at": self.created_at
        };
    }
}

walker GenerateRecommendationsWalker {
    has patient_id: str;
    has created_at: str;

    obj __specs__ { static has auth: bool = False; }

    can execute with `root entry {
        if self.patient_id not in therapy_sessions {
            report {"error": "Patient not found", "patient_id": self.patient_id};
            return;
        }

        session = therapy_sessions[self.patient_id];

        assessment_summary = "";
        for qa in session.assessment_qa {
            assessment_summary += f"Q: {qa.question}\nA: {qa.answer}\n";
        }

        recommendations = generate_therapy_recommendations(
            assessment_summary,
            " ".join(session.assessment_context.focus_areas),
            session.patient.name
        );

        session.recommendations.append({
            "created_at": self.created_at,
            "content": recommendations
        });

        report {
            "status": "recommendations_generated",
            "patient_id": self.patient_id,
            "recommendations": recommendations,
            "created_at": self.created_at
        };
    }
}

walker GetSessionSummaryWalker {
    has patient_id: str;

    obj __specs__ { static has auth: bool = False; }

    can execute with `root entry {
        if self.patient_id not in therapy_sessions {
            report {"error": "Patient not found", "patient_id": self.patient_id};
            return;
        }

        session = therapy_sessions[self.patient_id];

        report {
            "patient_id": self.patient_id,
            "patient_name": session.patient.name,
            "assessment_started": session.assessment_started,
            "is_active": session.is_active,
            "qa_count": len(session.assessment_qa),
            "journal_entries": len(session.journal_entries),
            "focus_areas": session.assessment_context.focus_areas,
            "recommendation_count": len(session.recommendations)
        };
    }
}

walker PatientVisitStatsWalker {
    has patient_id: str = "";

    obj __specs__ { static has auth: bool = False; }

    can execute with `root entry {
        registered = assessment_stats.get("registered_count", 0);
        started = assessment_stats.get("started_count", 0);
        registered_list = assessment_stats.get("registered_list", []);
        gender_counts = assessment_stats.get("gender_counts", {});
        patients_assessed_list = assessment_stats.get("patients_assessed", []);

        visited_list = [];
        # collect patient_ids whose sessions have assessment_started = True
        for pid in therapy_sessions {
            sess = therapy_sessions[pid];
            if sess.assessment_started {
                visited_list.append(pid);
            }
        }

        # optional per-patient query
        if self.patient_id != "" {
            is_registered = self.patient_id in registered_list;
            is_visited = self.patient_id in visited_list;
            report {
                "patient_id": self.patient_id,
                "is_registered": is_registered,
                "is_visited": is_visited
            };
            return;
        }

        report {
            "registered_count": registered,
            "visited_count": len(visited_list),
            "started_count": started,
            "registered_list": registered_list,
            "visited_list": visited_list,
            "gender_counts": gender_counts,    # include gender_counts in the report
            "patients_assessed_count": len(patients_assessed_list)   # new: number of patients who answered assessments
        };
    }
}

