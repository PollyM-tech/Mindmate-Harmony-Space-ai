# ==============================
# ========== NODES ============
# ==============================

node User {
    has user_id: str;
    has display_name: str;
    has timezone: str = "UTC";
    has preferences: dict = {};
}

node Emotion {
    has user_id: str;
    has created_at: str;
    has label: str;
    has category: str = "";
    has intensity: int = 0;
    has valence: str = "neutral";
    has context: str = "";
}

node Trigger {
    has user_id: str;
    has created_at: str;
    has name: str;
    has category: str = "";
    has description: str = "";
    has risk_level: str = "low";
}

node Activity {
    has user_id: str;
    has created_at: str;
    has name: str;
    has type: str = "";
    has energy_level: int = 0;
    has helpfulness_tag: str = "unknown";
    has description: str = "";
}

node Suggestion {
    has user_id: str;
    has created_at: str;
    has title: str;
    has content: str;
    has category: str = "";
    has duration_minutes: int = 5;
    has source: str = "llm";
    has tags: list = [];
}

node PatientMedicalHistory {
    has user_id: str;
    has created_at: str;
    has conditions: list = [];
    has medications: list = [];
    has therapy_status: str = "";
    has risk_notes: str = "";
    has allergies: list = [];
}

node JournalEntry {
    has user_id: str;
    has created_at: str;
    has content: str;
    has mood_score: int = 0;
    has notes: str = "";
    has emotion_labels: list = [];
    has trigger_labels: list = [];
    has risk_level: str = "mild";
}

node MoodEntry {
    has user_id: str;
    has created_at: str;
    has emoji: str;
    has primary_emotion: str;
    has mood_score: int = 0;
    has notes: str = "";
    has context_text: str = "";
    has time_of_day: str = "";
}

# ==============================
# ========== EDGES ============
# ==============================

edge UserAll {
    has relation_type: str;
    has created_at: str;
}

edge EmotionTrigger {
    has count: int = 0;
    has last_seen_at: str = "";
    has strength: float = 0.0;
}

edge TriggerActivity {
    has usage_count: int = 0;
    has helpfulness_score: float = 0.0;
    has last_used_at: str = "";
}

edge ActivityEmotion {
    has before_mood: int = 0;
    has after_mood: int = 0;
    has delta: int = 0;
    has recorded_at: str = "";
}

edge LoggedEmotion {
    has confidence: float = 1.0;
    has source: str = "llm";
}

edge LoggedTrigger {
    has confidence: float = 1.0;
    has source: str = "llm";
}

edge SuggestionLink {
    has relation_type: str;
    has created_at: str;
    has usage_count: int = 0;
    has avg_effect: float = 0.0;
}

# ==============================
# ========== BYLLM AI ==========
# ==============================

can analyze_journal_entry(text: str) -> dict {
    prompt = """
    You are a mental health assistant.
    From the journal below:
    - Extract emotions
    - Extract triggers
    - Assess risk level (mild, moderate, severe, critical)
    - Generate 2 supportive suggestions
    Reply strictly in JSON format.

    Journal:
    {text}
    """;

    result = byllm.generate(
        prompt=prompt,
        temperature=0.4,
        max_tokens=400
    );

    return json.loads(result);
}

# ==============================
# ===== GET OR CREATE USER =====
# ==============================

walker get_or_create_user {
    has user_id: str;
    has display_name: str = "";
    has timezone: str = "UTC";

    can entrypoint with `root entry {
        users = [root -->(`?User)](?user_id == self.user_id);

        if users {
            user = users[0];
        } else {
            user = User(
                user_id=self.user_id,
                display_name=self.display_name if self.display_name else self.user_id,
                timezone=self.timezone
            );
            root ++> user;
        }

        report {
            "user_id": user.user_id,
            "display_name": user.display_name,
            "timezone": user.timezone
        };
    }
}

# ==============================
# ===== LOG MOOD ENTRY =========
# ==============================

walker log_mood_entry {
    has user_id: str;
    has created_at: str;
    has mood_score: int;
    has emoji: str;
    has primary_emotion: str;
    has notes: str = "";
    has context_text: str = "";
    has time_of_day: str = "";

    can entrypoint with `root entry {
        users = [root -->(`?User)](?user_id == self.user_id);
        if users { user = users[0]; }
        else {
            user = User(user_id=self.user_id, display_name=self.user_id);
            root ++> user;
        }

        mood = MoodEntry(
            user_id=self.user_id,
            created_at=self.created_at,
            mood_score=self.mood_score,
            notes=self.notes,
            emoji=self.emoji,
            primary_emotion=self.primary_emotion,
            context_text=self.context_text,
            time_of_day=self.time_of_day
        );

        user +>:UserAll(relation_type="mood_entry", created_at=self.created_at):+> mood;

        report {
            "status": "logged",
            "primary_emotion": self.primary_emotion,
            "mood_score": self.mood_score
        };
    }
}

# ==============================
# ===== LOG JOURNAL + BYLLM ====
# ==============================

walker log_journal_entry {
    has user_id: str;
    has created_at: str;
    has content: str;
    has mood_score: int = 0;
    has notes: str = "";

    can entrypoint with `root entry {

        users = [root-->(`?User)](?user_id == self.user_id);
        if users { user = users[0]; }
        else {
            user = User(user_id=self.user_id, display_name=self.user_id);
            root ++> user;
        }

        analysis = analyze_journal_entry(self.content);

        emotion_labels = analysis.get("emotions", []);
        trigger_labels = analysis.get("triggers", []);
        risk_level = analysis.get("risk_level", "mild");
        suggestions_data = analysis.get("suggestions", []);

        journal = JournalEntry(
            user_id=self.user_id,
            created_at=self.created_at,
            content=self.content,
            mood_score=self.mood_score,
            notes=self.notes,
            emotion_labels=emotion_labels,
            trigger_labels=trigger_labels,
            risk_level=risk_level
        );

        user +>:UserAll(relation_type="journal_entry", created_at=self.created_at):+> journal;

        for label in emotion_labels {
            e = Emotion(user_id=self.user_id, created_at=self.created_at, label=label);
            journal +>:LoggedEmotion(confidence=1.0, source="llm"):+> e;
        }

        for t_label in trigger_labels {
            t = Trigger(user_id=self.user_id, created_at=self.created_at, name=t_label);
            journal +>:LoggedTrigger(confidence=1.0, source="llm"):+> t;
        }

        created_titles = [];

        for s in suggestions_data {
            sug = Suggestion(
                user_id=self.user_id,
                created_at=self.created_at,
                title=s.get("title", "Support Tip"),
                content=s.get("content", ""),
                category="journal_auto",
                duration_minutes=5,
                source="llm",
                tags=[risk_level]
            );

            user +>:UserAll(relation_type="suggestion", created_at=self.created_at):+> sug;

            journal +>:SuggestionLink(
                relation_type="auto_generated",
                created_at=self.created_at
            ):+> sug;

            created_titles.append(sug.title);
        }

        report {
            "status": "logged",
            "risk_level": risk_level,
            "emotion_labels": emotion_labels,
            "trigger_labels": trigger_labels,
            "suggestions_created": created_titles
        };
    }
}
