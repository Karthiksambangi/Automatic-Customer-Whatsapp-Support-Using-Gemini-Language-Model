import os
import time
import requests
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")
YOUR_BOT_NUMBER = os.getenv("YOUR_BOT_NUMBER")

# Gemini setup
def ask_gemini(prompt):
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print("Error from Gemini API:", e)
        return None

# Poll for new WhatsApp messages
def get_new_messages():
    # Replace with your MCP server's endpoint for fetching messages
    resp = requests.get(f"{MCP_SERVER_URL}/messages")
    resp.raise_for_status()
    return resp.json()  # Adjust based on actual response structure

# Send a message via MCP
def send_whatsapp_message(chat_id, text):
    payload = {"chat_id": chat_id, "text": text}
    resp = requests.post(f"{MCP_SERVER_URL}/send_message", json=payload)
    return resp.ok

if __name__ == "__main__":
    seen_message_ids = set()
    while True:
        try:
            messages = get_new_messages()
            for msg in messages:
                msg_id = msg.get("id")
                chat_id = msg.get("chat_id")
                text = msg.get("text")
                sender = msg.get("sender")

                # Avoid replying to your own bot's messages
                if msg_id in seen_message_ids or sender == YOUR_BOT_NUMBER:
                    continue

                # Mark as seen
                seen_message_ids.add(msg_id)

                # Get Gemini's reply
                reply = ask_gemini(text)
                if reply:
                    send_whatsapp_message(chat_id, reply)
                    print(f"Replied to {chat_id}: {reply}")

            time.sleep(5)  # Poll every 5 seconds
        except Exception as e:
            print("Error in main loop:", e)
            time.sleep(5)