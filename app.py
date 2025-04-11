from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

API_URL = "https://xiaoai.plus/v1/chat/completions"
API_KEY = "sk-wbdkdE8VNbd8d0TqEItWrHxGlWRyPZbyzrc6v71OwYvEUM2x"

conversation_history = {}

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_id = data.get("user_id")
    user_message = data.get("message")

    if not user_id or not user_message:
        return jsonify({"error": "Missing user_id or message"}), 400

    if user_id not in conversation_history:
        conversation_history[user_id] = []

    # 加入当前用户消息
    conversation_history[user_id].append({"role": "user", "content": user_message})
    conversation_history[user_id] = conversation_history[user_id][-10:]  # 限制上下文

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    payload = {
        "model": "gpt-4o",  # 你可以改成你 xiaoai.plus 支持的模型，比如 gpt-3.5-turbo
        "messages": conversation_history[user_id]
    }

    try:
        response = requests.post(API_URL, json=payload, headers=headers, timeout=20)
        response.raise_for_status()
        result = response.json()
        reply = result["choices"][0]["message"]["content"]
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # 加入 AI 回复
    conversation_history[user_id].append({"role": "assistant", "content": reply})
    return jsonify({"reply": reply})
