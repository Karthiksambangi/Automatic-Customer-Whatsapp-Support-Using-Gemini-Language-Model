import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load your Gemini API key
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)

# List and print available models
for m in genai.list_models():
    print(m.name)