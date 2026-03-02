import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file or environment variables.")

def ask_gemini(prompt):
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('models/gemini-1.5-flash-latest')  # Changed model name
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print("Error from Gemini API:", e)
        return None

# Example usage
if __name__ == "__main__":
    prompt = "What is the weather condition in Hyderabad today?"
    result = ask_gemini(prompt)
    if result:
        print(result)
    else:
        print("No response from Gemini.")