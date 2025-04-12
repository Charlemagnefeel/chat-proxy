from flask import Flask, request, Response
import requests
import re

app = Flask(__name__)

API_URL = "https://xiaoai.plus/v1/chat/completions"
API_KEY = "sk-wbdkdE8VNbd8d0TqEItWrHxGlWRyPZbyzrc6v71OwYvEUM2x"

conversation_history = {}

def is_reset_command(text):
    text = text.lower().strip()
    return any(text.startswith(trigger) for trigger in ["/reset", "重置对话", "清空对话", "reset"])

def remove_think_content(text):
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)

def handle_chat(user_id, message, model, session_id, user_name=None):
    # ✅ deepseek-r1 和 deepseek-v3 都带修饰
    if model in ["deepseek-r1", "deepseek-v3"]:
        message = message.lstrip("sS")
        message += "。尽量缩短思考时间，正文限制在800字以内。"
    elif model == "gpt-4o":
        message = message.lstrip("wW")

    # 构建上下文 key
    if session_id.startswith("1-"):
        key = f"{session_id}_{user_id}_{model}"
    else:
        key = f"{session_id}_{model}"

    if is_reset_command(message):
        conversation_history.pop(key, None)
        return "✅ 对话已重置（触发关键词成功）"

    if key not in conversation_history:
        if session_id.startswith("2-"):
            conversation_history[key] = [{
                "role": "system",
                "content": "当前为群聊场景，消息内容开头[]内的内容是群聊成员昵称，仅供你识别不同消息的发送者身份用，回答中无需包含该昵称。"
            }]
        else:
            conversation_history[key] = []

    match = re.search(r"设定：(.*)", message)
    if match:
        setting_content = match.group(1).strip()
        if model in ["deepseek-r1", "deepseek-v3"]:  # ✅ 支持 deepseek-v3
            if session_id.startswith("2-") and user_name:
                setting_text = f"收到来自 [{user_name}] 的设定指令：{setting_content}。该设定将应用于之后的对话。"
            else:
                setting_text = f"设定指令：{setting_content}。该设定将应用于之后的对话。"
            conversation_history[key].append({
                "role": "assistant",
                "content": setting_text,
                "preserve": True
            })
        else:
            conversation_history[key].append({
                "role": "system",
                "content": setting_content,
                "preserve": True
            })
        return "✅ 设定已保存（不会触发当前回复）"

    if session_id.startswith("2-") and user_name:
        content = f"[{user_name}]：{message}"
    else:
        content = message
    conversation_history[key].append({"role": "user", "content": content})

    max_len = 20
    preserved = []
    normal = []

    for msg in conversation_history[key]:
        if msg.get("preserve"):
            preserved.append(msg)
        else:
            normal.append(msg)

    max_normal_len = max_len - len(preserved)
    normal = normal[-max_normal_len:] if max_normal_len > 0 else []
    conversation_history[key] = preserved + normal

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    payload = {
        "model": model,
        "messages": conversation_history[key]
    }

    try:
        response = requests.post(API_URL, json=payload, headers=headers, timeout=300)
        response.raise_for_status()
        result = response.json()
        reply = result["choices"][0]["message"]["content"]

        if "xiaoai" in reply.lower():
            return "服务器开小差了"

        # ✅ 仅对 deepseek-r1 去除 think 标签
        if model == "deepseek-r1":
            reply = remove_think_content(reply)

    except Exception as e:
        return f"❌ 发生错误：{str(e)}"

    conversation_history[key].append({"role": "assistant", "content": reply})
    return reply

# ✅ 支持 gpt-4o
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_id = data.get("message_from")
    message = data.get("message")
    message_type = data.get("message_type")
    message_to = data.get("message_to")
    session_id = f"{message_type}-{message_to}" if message_type and message_to else user_id
    user_name = data.get("message_from_name")

    if not user_id or not message:
        return Response("Missing user_id or message", status=400)

    reply = handle_chat(user_id, message, "gpt-4o", session_id, user_name)
    return Response(reply, content_type="text/plain; charset=utf-8")

# ✅ 支持 deepseek-r1
@app.route("/deepseek", methods=["POST"])
def deepseek():
    data = request.get_json()
    user_id = data.get("message_from")
    message = data.get("message")
    message_type = data.get("message_type")
    message_to = data.get("message_to")
    session_id = f"{message_type}-{message_to}" if message_type and message_to else user_id
    user_name = data.get("message_from_name")

    if not user_id or not message:
        return Response("Missing user_id or message", status=400)

    reply = handle_chat(user_id, message, "deepseek-r1", session_id, user_name)
    return Response(reply, content_type="text/plain; charset=utf-8")

# ✅ 新增 deepseek-v3 路由
@app.route("/deepseekv3", methods=["POST"])
def deepseekv3():
    data = request.get_json()
    user_id = data.get("message_from")
    message = data.get("message")
    message_type = data.get("message_type")
    message_to = data.get("message_to")
    session_id = f"{message_type}-{message_to}" if message_type and message_to else user_id
    user_name = data.get("message_from_name")

    if not user_id or not message:
        return Response("Missing user_id or message", status=400)

    reply = handle_chat(user_id, message, "deepseek-v3", session_id, user_name)
    return Response(reply, content_type="text/plain; charset=utf-8")

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
