import os
import subprocess
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY", "").strip()
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env")

env = os.environ.copy()
env["GEMINI_API_KEY"] = api_key

# Optional: set a port explicitly
# env["JAC_SERVER_PORT"] = "8000"

subprocess.run(["jac", "serve", "mindharmony.jac"], env=env, check=True)
