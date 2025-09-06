from flask import Flask, request, jsonify
from openai import OpenAI
import os

app = Flask(__name__)

# Configurar cliente OpenRouter con GPT-3.5
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY")
)

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        req = request.get_json(silent=True, force=True)
        user_text = req["queryResult"]["queryText"]

        completion = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_text}],
            extra_headers={
                "HTTP-Referer": "https://mi-proyecto.up.railway.app",  # opcional
                "X-Title": "Mi Webhook GPT3.5"  # opcional
            }
        )

        llm_reply = completion.choices[0].message.content.strip()

    except Exception as e:
        print("Error interno:", e)
        llm_reply = f"Error interno: {str(e)}"

    return jsonify({"fulfillmentText": llm_reply})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
