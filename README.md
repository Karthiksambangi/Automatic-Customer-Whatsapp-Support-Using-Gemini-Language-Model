# Automatic Customer WhatsApp Support Using Gemini Language Model

An AI-powered customer support automation system that integrates WhatsApp with Google Gemini LLM to automatically handle and respond to customer queries.

---

## 📌 Overview

This project enables automated customer support over WhatsApp by integrating:

- WhatsApp Web (via Node.js bridge)
- Python backend server
- Google Gemini Language Model
- REST-based communication between services

The system listens to incoming WhatsApp messages, processes them using Gemini LLM, and sends intelligent responses back to users automatically.

---

## 🚀 Features

- Automated WhatsApp message handling
- AI-generated responses using Gemini API
- Modular backend architecture
- Configurable using environment variables
- Scalable multi-service design

---

## 🧠 Tech Stack

- Python (Backend Logic)
- Node.js (WhatsApp Web Bridge)
- Google Gemini API (LLM Responses)
- REST APIs

---

## 📂 Project Structure

Automatic-Customer-Whatsapp-Support-Using-Gemini-Language-Model/

├── frontend/  
├── mcp_server/  
├── python-backend/  
├── whatsapp-bridge/  
├── gemini_client.py  
├── whatsapp_gemini_bot.py  
└── README.md  

---

## ⚙️ Setup Instructions

### 1. Clone Repository

```bash
git clone https://github.com/Karthiksambangi/Automatic-Customer-Whatsapp-Support-Using-Gemini-Language-Model.git
cd Automatic-Customer-Whatsapp-Support-Using-Gemini-Language-Model
2. Configure Environment Variables

Create a .env file in the root directory and add:

GEMINI_API_KEY=your_api_key_here
3. Install Dependencies
Python Backend
cd python-backend
pip install -r requirements.txt
WhatsApp Bridge
cd whatsapp-bridge
npm install
4. Run Services

Start Python backend:

python app.py

Start WhatsApp bridge:

npm start

Scan the WhatsApp QR code when prompted.

🏗️ Architecture Flow

User sends a message on WhatsApp

WhatsApp Bridge captures the message

Message is sent to the Python backend

Gemini API generates a response

Response is sent back to the user

🎯 Use Cases

Customer support automation

FAQ handling

AI chatbot integration

Business WhatsApp automation
