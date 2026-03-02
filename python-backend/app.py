from flask import Flask, request, jsonify, send_from_directory
import requests
import uuid
import sqlite3
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# In-memory session store (use a database for production)
sessions = {}

# Ensure db folder exists
os.makedirs('db', exist_ok=True)

# --- SECURITY WARNING ---
# Storing API keys directly in code is a major security risk.
# In a real application, load this from an environment variable.
GEMINI_API_KEY = "AIzaSyAf-dseh9hN8a46DUjLdBxnqkQpxk-DWwY" # Your API Key

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is not set. Please set it as an environment variable.")

# --- UPDATED: Using the gemini-2.5-pro model as requested ---
GEMINI_ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent?key={GEMINI_API_KEY}"

# WhatsApp bridge endpoint
WHATSAPP_BRIDGE_URL = "http://localhost:9600/api/send"


def create_users_table():
    conn = None
    try:
        conn = sqlite3.connect('db/mydb.db')
        cur = conn.cursor()
        cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            system_model TEXT NOT NULL
        )
        ''')
        conn.commit()
        print("Users table checked/created successfully.")
    except sqlite3.Error as e:
        print(f"Database error during table creation: {e}")
    finally:
        if conn:
            conn.close()

# Call this when your app starts
create_users_table()

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    if not data:
        return jsonify({"success": False, "message": "Invalid JSON data"}), 400

    name = data.get('name')
    phone = data.get('phone')
    system_model = data.get('system_model')

    if not all([name, phone, system_model]):
        return jsonify({"success": False, "message": "Missing required fields (name, phone, system_model)"}), 400

    conn = None
    try:
        conn = sqlite3.connect('db/mydb.db')
        cur = conn.cursor()
        cur.execute("INSERT INTO users (name, phone, system_model) VALUES (?, ?, ?)",
                      (name, phone, system_model))
        conn.commit()
        print(f"User registered and saved to DB: {name}, {phone}, {system_model}")
    except sqlite3.Error as e:
        print(f"Database error during user registration: {e}")
        return jsonify({"success": False, "message": "Database error during registration."}), 500
    finally:
        if conn:
            conn.close()

    session_id = str(uuid.uuid4())
    precontext = f"Customer Name: {name}, Phone: {phone}, System Model: {system_model}"
    sessions[session_id] = {
        "phone": phone,
        "precontext": precontext,
        "history": []
    }
    return jsonify({"success": True, "session_id": session_id, "message": "Registration successful!"})

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    if not data:
        return jsonify({"reply": "Invalid JSON data"}), 400

    session_id = data.get('session_id')
    user_message = data.get('message')

    session = sessions.get(session_id)
    if not session:
        return jsonify({"reply": "Session not found or expired."}), 400

    if not user_message:
        return jsonify({"reply": "No message provided."}), 400

    prompt_parts = [session['precontext']]
    for entry in session['history']:
        prompt_parts.append(f"User: {entry['user']}")
        prompt_parts.append(f"AI: {entry['ai']}")
    prompt_parts.append(f"User: {user_message}")
    prompt_parts.append("AI:")

    prompt = "\n".join(prompt_parts)

    gemini_reply = "Sorry, I couldn't get a response from the AI."
    try:
        gemini_payload = {
            "contents": [
                {"parts": [{"text": prompt}]}
            ],
            "generationConfig": {
                # --- FIX: Increased token limit to prevent 'MAX_TOKENS' with gemini-2.5-pro ---
                "maxOutputTokens": 2048
            }
        }
        resp = requests.post(GEMINI_ENDPOINT, json=gemini_payload)
        resp.raise_for_status()
        result = resp.json()

        if result and 'candidates' in result and result['candidates']:
            candidate = result['candidates'][0]
            if 'content' in candidate and 'parts' in candidate['content'] and candidate['content']['parts']:
                gemini_reply = candidate['content']['parts'][0]['text']
            elif 'finishReason' in candidate and candidate.get('finishReason') == 'SAFETY':
                print("❌ Gemini response blocked due to safety settings.")
                gemini_reply = "The response was blocked due to safety settings."
            else:
                print(f"Gemini API response structure unexpected (e.g. MAX_TOKENS): {result}")
                gemini_reply = "Sorry, the AI response was incomplete or malformed."
        else:
            print(f"Gemini API returned no candidates. This may be due to a prompt safety block. Full response: {result}")
            gemini_reply = "Sorry, the AI returned an empty response. The prompt may have been blocked."

    except requests.exceptions.RequestException as e:
        print(f"❌ Error calling Gemini API: {e}")
        if e.response is not None:
            print(f"❌ Response Status Code: {e.response.status_code}")
            print(f"❌ Response Body: {e.response.text}")
        gemini_reply = "Sorry, there was a network error communicating with the AI."
    except Exception as e:
        print(f"An unexpected error occurred processing the response: {e}")
        gemini_reply = "An internal error occurred."

    session['history'].append({"user": user_message, "ai": gemini_reply})

    print(f"\n=== DEBUG: Attempting to send WhatsApp messages ===")
    print(f"User phone: {session['phone']}")
    print(f"User message: {user_message}")
    print(f"Gemini reply: {gemini_reply}")
    
    try:
        phone_number = session['phone']
        if not phone_number.startswith('91'):
            phone_number = '91' + phone_number
        
        for msg_to_send in [user_message, gemini_reply]:
            whatsapp_payload = {
                "recipient": phone_number,
                "message": msg_to_send
            }
            print(f"Sending payload: {whatsapp_payload}")
            whatsapp_resp = requests.post(WHATSAPP_BRIDGE_URL, json=whatsapp_payload)
            print(f"Response status: {whatsapp_resp.status_code}")
            print(f"Response body: {whatsapp_resp.text}")
            whatsapp_resp.raise_for_status()
            print(f"✅ SUCCESS: Sent message to WhatsApp bridge for {phone_number}: {msg_to_send}")
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR sending message to WhatsApp bridge: {e}")
        print(f"Make sure WhatsApp bridge is running on {WHATSAPP_BRIDGE_URL}")

    return jsonify({"reply": gemini_reply})

if __name__ == '__main__':
    app.run(port=5001, debug=True)

