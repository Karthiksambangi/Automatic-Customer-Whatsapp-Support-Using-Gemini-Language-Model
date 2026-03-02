import requests

payload = {
    "chat_id": "test_chat",
    "text": "Hello from test!",
}
resp = requests.post("http://localhost:5000/send_message", json=payload)
print(resp.json())