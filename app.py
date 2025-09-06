from flask import Flask, request, jsonify
import openai
import os

app = Flask(__name__)

# Configurar OpenAI para usar OpenRouter
openai.api_key = os.environ.get("OPENROUTER_API_KEY")
openai.api_base = "https://openrouter.ai/api/v1"

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        req = request.get_json(silent=True, force=True)
        user_text = req["queryResult"]["queryText"]

        # Usando la nueva API de OpenAI 1.0.0
        response = openai.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_text}]
        )

        llm_reply = response.choices[0].message.content.strip()

    except Exception as e:
        print("Error interno:", e)
        llm_reply = f"Error interno: {str(e)}"

    return jsonify({"fulfillmentText": llm_reply})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
