#Import BYLLM
import from byllm.lib { Model }

glob llm = Model(verbose=True, model_name="gpt-4o-mini");

node User {
    has user_id: str;
    has display_name: str;
    has timezone: str = "UTC";
    has preferences: dict = {};     # e.g., {"tone": "gentle", "panic_mode": true}
}

# Core Node Types

node Emotion {
    has user_id: str;
    has created_at: str;
    has label: str;                 # "sad", "anxious", "calm"
    has category: str = "";
    has intensity: int = 0;         # 1–10
    has valence: str = "neutral";   # "negative", "neutral", "positive"
    has context: str = "";
}

node Trigger {
    has user_id: str;
    has created_at: str;
    has name: str;                  # "exam", "conflict", "social media"
    has category: str = "";
    has description: str = "";
    has risk_level: str = "low";
}

node Activity {
    has user_id: str;
    has created_at: str;
    has name: str;
    has type: str = "";             # "self-care", "work"
    has energy_level: int = 0;      #1-5
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
    has source: str = "llm";       ## "llm", "clinician", "template"
    has tags: list = [];           # e.g., ["anxiety", "sleep"] 
}

node PatientMedicalHistory {
    has user_id: str;
    has created_at: str;
    has conditions: list = [];      # ["anxiety", "bipolar"]
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
    has risk_level: str = "mild";  # "mild", "moderate", "severe", "critical"
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


edge UserAll {
    has relation_type: str;         
    has created_at: str;             
}

edge EmotionTrigger {
    has count: int = 0;              # times this pair co-occurred
    has last_seen_at: str = "";      # last time we saw this combo
    has strength: float = 0.0;       # normalized correlation score (0.0–1.0)
}

edge TriggerActivity {
    has usage_count: int = 0;        # how many times user tried this activity
    has helpfulness_score: float = 0.0;  # avg effect on mood (e.g., -5..+5)
    has last_used_at: str = "";
}
# 

edge ActivityEmotion {
    has before_mood: int = 0;        # mood_score before activity
    has after_mood: int = 0;         # mood_score after activity
    has delta: int = 0;              # after_mood - before_mood
    has recorded_at: str = "";       # timestamp
}

edge LoggedEmotion {
    has confidence: float = 1.0;     # LLM confidence in this label (0.0–1.0)
    has source: str = "llm";         # "llm", "user", "rule"
}

edge LoggedTrigger {
    has confidence: float = 1.0;
    has source: str = "llm";         # label origin
}

edge SuggestionLink {
    has relation_type: str;          # "for_emotion", "for_trigger"
    has created_at: str;             
    has usage_count: int = 0;        # how many times suggested to user
    has avg_effect: float = 0.0;     # avg mood delta when used
}
#GET OR CREATE USER
walker get_or_create_user {
    has user_id: str;
    has display_name: str = "";
    has timezone: str = "UTC";

    obj __specs__ {
        static has auth: bool = False;
    }

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

# LOG MOOD ENTRY
walker log_mood_entry {
    has user_id: str;
    has created_at: str;
    has mood_score: int;
    has emoji: str;
    has primary_emotion: str;
    has notes: str = "";
    has context_text: str = "";
    has time_of_day: str = "";

    obj __specs__ {
        static has auth: bool = False;
    }

    can entrypoint with `root entry {
        # Get or create user
        users = [root -->(`?User)](?user_id == self.user_id);
        if users {
            user = users[0];
        } else {
            user = User(
                user_id=self.user_id,
                display_name=self.user_id
            );
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

        user +>:UserAll(
            relation_type="mood_entry",
            created_at=self.created_at
        ):+> mood;

        report {
            "status": "logged",
            "user_id": self.user_id,
            "mood_score": self.mood_score,
            "primary_emotion": self.primary_emotion,
            "created_at": self.created_at
        };
    }
}

# LOG JOURNAL ENTRY + ANALYSIS
walker log_journal_entry {
    has user_id: str;
    has created_at: str;
    has content: str;
    has mood_score: int = 0;
    has notes: str = "";

    obj __specs__ {
        static has auth: bool = False;
    }

    can entrypoint with `root entry {
        # 1. Get or create user
        users = [root-->(`?User)](?user_id == self.user_id);

        if users {
            user = users[0];
        } else {
            user = User(
                user_id=self.user_id,
                display_name=self.user_id
            );
            root ++> user;
        }

        # 2. Call LLM to analyze the journal content
        analysis = analyze_journal_entry(self.content);

        emotion_labels = analysis.get("emotion_labels", []);
        trigger_labels = analysis.get("trigger_labels", []);
        risk_level = analysis.get("risk_level", "mild");

        # 3. Create the JournalEntry node
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

        # Attach journal to user
        user +>:UserAll(
            relation_type="journal_entry",
            created_at=self.created_at
        ):+> journal;

        # 4. Link to Emotion nodes
        for label in emotion_labels {
            emotions = [user-->(`?Emotion)](?label == label);

            if emotions {
                e = emotions[0];
            } else {
                e = Emotion(
                    user_id=self.user_id,
                    created_at=self.created_at,
                    label=label
                );
                user +>:UserAll(
                    relation_type="emotion",
                    created_at=self.created_at
                ):+> e;
            }

            journal +>:LoggedEmotion(
                confidence=1.0,
                source="llm"
            ):+> e;
        }

        # 5. Link to Trigger nodes
        for t_label in trigger_labels {
            triggers = [user-->(`?Trigger)](?name == t_label);

            if triggers {
                t = triggers[0];
            } else {
                t = Trigger(
                    user_id=self.user_id,
                    created_at=self.created_at,
                    name=t_label
                );
                user +>:UserAll(
                    relation_type="trigger",
                    created_at=self_created_at
                ):+> t;
            }

            journal +>:LoggedTrigger(
                confidence=1.0,
                source="llm"
            ):+> t;
        }

        # 6. Final API response
        report {
            "status": "logged",
            "user_id": self.user_id,
            "risk_level": risk_level,
            "emotion_labels": emotion_labels,
            "trigger_labels": trigger_labels,
            "created_at": self.created_at
        };
    }
}

#LIST RECENT MOODS

walker list_recent_moods {
    has user_id: str;
    has limit: int = 20;

    obj __specs__ {
        static has auth: bool = False;
    }

    can entrypoint with `root entry {
        users = [root -->(`?User)](?user_id == self.user_id);
        if not users {
            report {"user_id": self.user_id, "moods": [], "count": 0};
            return;
        }

        user = users[0];

        moods = [user --> (`?MoodEntry)];
        # For MVP we won't sort; frontend can sort by created_at.

        result = [];
        count = 0;

        for m in moods {
            if count >= self.limit {
                break;
            }
            result.append({
                "created_at": m.created_at,
                "mood_score": m.mood_score,
                "emoji": m.emoji,
                "primary_emotion": m.primary_emotion,
                "notes": m.notes,
                "time_of_day": m.time_of_day
            });
            count += 1;
        }

        report {
            "user_id": self.user_id,
            "moods": result,
            "count": count
        };
    }
}
# LIST RECENT JOURNALS
walker list_recent_journals {
    has user_id: str;
    has limit: int = 20;

    obj __specs__ {
        static has auth: bool = False;
    }

    can entrypoint with `root entry {
        users = [root -->(`?User)](?user_id == self.user_id);
        if not users {
            report {"user_id": self.user_id, "journals": [], "count": 0};
            return;
        }

        user = users[0];

        journals = [user --> (`?JournalEntry)];
        result = [];
        count = 0;

        for j in journals {
            if count >= self.limit {
                break;
            }
            result.append({
                "created_at": j.created_at,
                "mood_score": j.mood_score,
                "content": j.content,
                "notes": j.notes,
                "emotion_labels": j.emotion_labels,
                "trigger_labels": j.trigger_labels,
                "risk_level": j.risk_level
            });
            count += 1;
        }

        report {
            "user_id": self.user_id,
            "journals": result,
            "count": count
        };
    }
}
# GENERATE SUPPORT SUGGESTIONS
walker generate_suggestions {
    has user_id: str;
    has created_at: str;
    has mood_limit: int = 10;
    has journal_limit: int = 5;

    obj __specs__ {
        static has auth: bool = False;
    }

    can entrypoint with `root entry {
        users = [root -->(`?User)](?user_id == self.user_id);
        if not users {
            report {"error": "User not found", "user_id": self.user_id};
            return;
        }

        user = users[0];

        moods = [user --> (`?MoodEntry)];
        journals = [user --> (`?JournalEntry)];
        histories = [user --> (`?PatientMedicalHistory)];

        recent_moods = [];
        m_count = 0;
        for m in moods {
            if m_count >= self.mood_limit {
                break;
            }
            recent_moods.append({
                "created_at": m.created_at,
                "mood_score": m.mood_score,
                "emoji": m.emoji,
                "primary_emotion": m.primary_emotion,
                "context_text": m.context_text,
                "time_of_day": m.time_of_day
            });
            m_count += 1;
        }

        recent_journals = [];
        j_count = 0;
        for j in journals {
            if j_count >= self.journal_limit {
                break;
            }
            recent_journals.append({
                "created_at": j.created_at,
                "mood_score": j.mood_score,
                "content": j.content,
                "emotion_labels": j.emotion_labels,
                "trigger_labels": j.trigger_labels,
                "risk_level": j.risk_level
            });
            j_count += 1;
        }

        med_history = {};
        if histories {
            h = histories[0];
            med_history = {
                "conditions": h.conditions,
                "medications": h.medications,
                "therapy_status": h.therapy_status,
                "risk_notes": h.risk_notes,
                "allergies": h.allergies
            };
        }

        state = {
            "user_id": self.user_id,
            "recent_moods": recent_moods,
            "recent_journals": recent_journals,
            "preferences": user.preferences,
            "medical_history": med_history
        };

        response = generate_supportive_suggestions(state);
        suggestions_data = response.get("suggestions", []);

        created_titles = [];

        for s in suggestions_data {
            title = s.get("title", "Suggestion");
            content = s.get("content", "");
            category = s.get("category", "");
            duration = s.get("duration_minutes", 5);
            tags = s.get("tags", []);

            sug = Suggestion(
                user_id=self.user_id,
                created_at=self.created_at,
                title=title,
                content=content,
                category=category,
                duration_minutes=duration,
                source="llm",
                tags=tags
            );

            user +>:UserAll(
                relation_type="suggestion",
                created_at=self.created_at
            ):+> sug;

            created_titles.append(title);
        }

        report {
            "user_id": self.user_id,
            "created_at": self.created_at,
            "suggestion_count": len(created_titles),
            "titles": created_titles
        };
    }
}
