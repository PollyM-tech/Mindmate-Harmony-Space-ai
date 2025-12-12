import litellm;
import from dotenv { load_dotenv }
import os;
import requests;
import base64;
import from byllm.lib { Model}


glob llm: Model = Model(model_name = "gemini/gemini-2.5-flash", api_key = os.getenv("GEMINI_API_KEY"));

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
        for patient_data in self.patients {
            patient = Patient(
                patient_id=patient_data.get("patient_id", ""),
                name=patient_data.get("name", ""),
                email=patient_data.get("email", ""),
                age=patient_data.get("age", 0),
                medical_history=patient_data.get("medical_history", "")
            );

            session = TherapySession(
                assessment_context=self.assessment_context,
                patient=patient,
                is_active=True,
                assessment_started=False
            );

            therapy_sessions[patient.patient_id] = session;
        }

        report {
            "status": "registered",
            "patient_count": len(self.patients),
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

