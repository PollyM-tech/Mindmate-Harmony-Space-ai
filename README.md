BetterAI

BetterAI is a Jac-based prototype for mental-health tooling. It models users, emotions, triggers, activities, journal and mood entries, and therapy-session workflows. The project uses an LLM wrapper (Model) to analyze journal entries, assess patient responses, and generate supportive suggestions.

Quick highlights
- Node and edge models for users, emotions, triggers, suggestions, journaling, and therapy sessions.
- Walkers to register patients, start assessments, submit answers/journals, and generate recommendations.
- Integrated LLM calls for analysis and recommendations.

Requirements
- Jac runtime for executing .jac files.
- Byllm/Model wrapper or equivalent LLM SDK installed and available to the Jac runtime.
- Python packages used in the repo (if running Python helpers): python-dotenv, requests, etc.

Environment
- Create a `.env` file or export environment variables. The code expects:
  - GEMINI_API_KEY — API key used by the Model wrapper.

Example `.env`
GEMINI_API_KEY=your_api_key_here

Security & privacy
- This project touches sensitive mental-health data. Never commit API keys or PHI to version control.
- Use secrets management (env vars, secret store) and restrict access.
- Consider legal and ethical review before using LLM outputs in clinical contexts.

Quick start
1. Install dependencies (adjust to your environment):
   - pip install python-dotenv requests byllm   # if applicable
   - Install Jac runtime per project instructions.
2. Set environment variables (or create `.env`).
3. Run the Jac module (example):
   - Jac Client expects a running Jac server. So you must start backend first:
   - python run.py
   - streamlit run app.py 

Notes & troubleshooting
- Ensure walker signatures have non-default arguments before default ones (Jac/Python restriction).
- Use mocked LLM responses for tests to avoid API calls and costs.
- Validate JSON responses from LLMs before writing to the graph to avoid runtime errors.

Contributing & license
- Open PRs with clear change descriptions.
- Do not add secrets to the repo.
- LICENSE file  MIT

 
