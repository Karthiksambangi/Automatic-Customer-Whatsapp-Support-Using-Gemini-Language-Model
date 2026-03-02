from flask import Flask, request, jsonify

app = Flask(__name__)

# In-memory message store for testing
messages = []

@app.route('/messages', methods=['GET'])
def get_messages():
    return jsonify(messages)

@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.json
    # Simulate sending a message by adding it to the store
    messages.append({
        "id": len(messages) + 1,
        "chat_id": data.get("chat_id"),
        "text": data.get("text"),
        "sender": "bot"
    })
    return jsonify({"status": "sent"})

if __name__ == "__main__":
    app.run(port=5000)