import os
from dotenv import load_dotenv
import subprocess

# Load .env file
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file")

# Pass key to subprocess environment
env = os.environ.copy()
env["GEMINI_API_KEY"] = api_key


# Run Jac with updated environment
#subprocess.run(["run", "example.jac"], env=env)
subprocess.run(["jac", "serve", "mindharmony.jac"], env=env)  
